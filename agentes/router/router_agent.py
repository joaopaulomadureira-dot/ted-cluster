import os
import json
import time
import httpx
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv(Path(__file__).parent / ".env")

app = FastAPI()

TED_GATE_URL = os.environ.get("TED_GATE_URL", "http://100.93.114.31:4003")
TED_GATE_KEY_ESCRITA = os.environ.get("TED_GATE_KEY_ESCRITA", "")
TED_GATE_KEY_COD = os.environ.get("TED_GATE_KEY_COD", "")
TED_GATE_KEY_LIVRE = os.environ.get("TED_GATE_KEY_LIVRE", "")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "")

# 2026-09-03: nomes de modelo saíram do código e foram pro modelos_atual.json --
# o atualizador_modelos.py (roda 1x/semana via launchd, domingo 06h) reescreve esse
# json sozinho quando um modelo some do catálogo gratuito, sem precisar editar/reiniciar
# a mão. Se o arquivo não existir ou vier corrompido, cai nos valores conhecidos abaixo
# (os mesmos que estavam hardcoded antes dessa mudança) -- nunca quebra por causa disso.
_MODELOS_PATH = Path(__file__).parent / "modelos_atual.json"
def _carregar_modelos():
    try:
        return json.loads(_MODELOS_PATH.read_text())
    except Exception:
        return {}
_MODELOS = _carregar_modelos()
MODELO_GROQ = _MODELOS.get("groq_model", "openai/gpt-oss-120b")
MODELO_GEMINI = _MODELOS.get("gemini_model", "gemma-4-31b-it")
MODELO_NVIDIA = _MODELOS.get("nvidia_model", "nvidia/nemotron-3.5-lightning-30b-a3b")

USO_PATH = "/tmp/ted-router-uso.json"

_cooldown_until = {}
COOLDOWN_SECONDS = 300  # provedor que responder 429 fica de fora da cascata por 5min, sem precisar de deploy

# cache de respostas em memoria -- economiza chamada repetida (health-checks periodicos,
# perguntas repetidas) sem precisar de infra nova. TTL curto pra nao servir resposta velha
# pra pergunta sensivel a tempo.
_CACHE = {}
CACHE_TTL_SECONDS = int(os.environ.get("ROUTER_CACHE_TTL_SECONDS", "900"))
CACHE_MAX_ENTRADAS = 500

# compressor de contexto -- corta prompt gigante (log colado, etc) antes de gastar
# token com ele. ~24000 caracteres = ~6000 tokens, folga confortavel pra qualquer
# provedor da cascata sem cortar conversa normal (que nunca chega perto disso).
PROMPT_MAX_CHARS = int(os.environ.get("ROUTER_PROMPT_MAX_CHARS", "24000"))


def _cache_get(chave: str):
    item = _CACHE.get(chave)
    if not item:
        return None
    expira_em, resposta, provedor = item
    if time.time() > expira_em:
        _CACHE.pop(chave, None)
        return None
    return resposta, provedor


def _cache_set(chave: str, resposta: str, provedor: str):
    if len(_CACHE) >= CACHE_MAX_ENTRADAS:
        # remove a entrada mais antiga (aproximado, sem heap -- volume baixo o suficiente)
        mais_antiga = min(_CACHE, key=lambda k: _CACHE[k][0])
        _CACHE.pop(mais_antiga, None)
    _CACHE[chave] = (time.time() + CACHE_TTL_SECONDS, resposta, provedor)


def _registrar_uso(provedor: str):
    from datetime import date
    hoje = date.today().isoformat()
    try:
        with open(USO_PATH) as f:
            dados = json.load(f)
    except Exception:
        dados = {}
    dia = dados.setdefault(hoje, {})
    dia[provedor] = dia.get(provedor, 0) + 1
    try:
        with open(USO_PATH, "w") as f:
            json.dump(dados, f)
    except Exception:
        pass

# cascata automatica (fallback em sequencia). openrouter fica de fora --
# so acessivel explicito via task_type="openrouter" (secao 6.1 do v1.1: OpenRouter/Anthropic sao manuais)
# Ordem por capacidade real (conferida em 2026-08-21 direto no painel do Google AI Studio
# do JPM + docs oficiais -- nao chute, ver feedback_openrouter_so_modelos_gratis na memoria):
# NVIDIA ~40rpm sem teto diario fixo (melhor rpm) -> Groq 30rpm/14400 por dia -> Gemma 4 31B
# 30rpm/14400 por dia (EMPATADO com Groq -- painel real do JPM mostrou que Gemma nao e o mais
# fraco, uma busca generica anterior deu numero errado) -> OpenRouter gratis 20rpm/~1000-1800
# por dia (mais fraco dos 4) -> local por ultimo (JPM: "depois as locais" -- reserva, nao
# primeira escolha).
_ORDEM_NUVEM = ["groq", "nvidia", "gemini_gemma", "openrouter"]
# 2026-09-03: NVIDIA promovida de volta pra 2a posicao (JPM: usar TODAS as APIs, NVIDIA
# e essencial porque o free tier dela NAO TEM TETO DIARIO -- so limite de 40 req/min,
# contra Groq (1000/dia) e Gemini (~1000-1500/dia). Pra uso de alto volume de tokens,
# é a mais folgada das 4.
# CORRECAO do achado de 2026-08-21 ("vaza pensamento na resposta"): NAO era bug do
# modelo -- era max_tokens baixo demais (testado hoje com 150, reproduziu igualzinho;
# com 2000+ a resposta sai limpa, thinking fica so no reasoning_content). Mesma
# pegadinha ja documentada pro Gemma no ecossistema anterior (ver API_TED.md, iCloud:
# "raciocinio interno consome o MESMO orcamento de max_tokens"). max_tokens da funcao
# _nvidia() subiu de 1024 pra 2500 por causa disso -- ver comentario la embaixo.

CASCATA = {
    "local": ["ollama_local", "groq", "gemini_gemma"],
    "fast": _ORDEM_NUVEM + ["ollama_local"],
    "code": ["ollama_cod", "groq"],
    "escrita": ["ollama_escrita", "groq"],
    "livre": ["ollama_livre"],
    "openrouter": ["openrouter"],
    "nvidia": ["nvidia"],
    "test_groq": ["groq"],
    "test_gemini": ["gemini_gemma"],
    "test_ollama": ["ollama_local"],
    "default": _ORDEM_NUVEM + ["ollama_local"],
}


class RouterRequest(BaseModel):
    prompt: str
    task_type: str = "default"
    usar_cache: bool = True


# 2026-08-21: achado real -- nenhum provedor da cascata sabia quem e o "Ted". Testado em
# NVIDIA, Groq e local, os 3 responderam sobre "TED Talks" (a conferencia) quando perguntados
# sobre o proprio ecossistema, porque a chamada ia crua, sem system prompt nenhum. Esse texto
# vai como mensagem de sistema em TODO provedor a partir de agora -- resolve a confusao de
# identidade sem custar quase nada de token (curto de proposito). Perguntas sobre detalhe real
# do ecossistema (agentes, decisoes, arquitetura) continuam indo pro Doc Reader via dominio
# DOCUMENTOS do TED Master -- aqui e so o minimo pra nao alucinar quem o Ted e.
SYSTEM_PROMPT = (
    "Voce e o Ted, assistente de IA do ecossistema pessoal de infraestrutura do JPM -- "
    "SEM relacao nenhuma com TED Talks/conferencias. E um cluster privado de 4 computadores "
    "(GERENTE e o notebook do JPM, liga/desliga conforme ele usa, NAO e monitorado 24h; COORD "
    "coordena; OP1 roda os agentes de IA; OP2 hospeda a infraestrutura 24h), acessado via "
    "Telegram. Responda em portugues simples e direto, sem jargao tecnico desnecessario. "
    "Use o CONTEXTO fornecido na mensagem (memoria da conversa, documentos, dados reais) pra "
    "responder de forma especifica e util -- pense sobre o que a pessoa realmente quer saber "
    "antes de desistir. So diga que nao sabe se de fato nao houver informacao nenhuma no "
    "contexto pra responder, e nesse caso seja direto e honesto (ex: 'nao tenho esse dado no "
    "momento'). NUNCA invente que vai 'perguntar pro operador', 'verificar e te aviso', ou "
    "qualquer outra acao de segundo plano que voce nao pode realmente fazer -- isso e uma "
    "desculpa fabricada, pior que admitir a limitacao."
)


async def _ollama_local(prompt: str, usar_identidade: bool = True) -> str:
    return await _via_gate(prompt, "ted-escrita-local-gemma2", TED_GATE_KEY_ESCRITA, usar_identidade)


async def _ollama_escrita(prompt: str, usar_identidade: bool = True) -> str:
    return await _via_gate(prompt, "ted-escrita-local-gemma2", TED_GATE_KEY_ESCRITA, usar_identidade)


async def _ollama_cod(prompt: str, usar_identidade: bool = True) -> str:
    return await _via_gate(prompt, "ted-cod-local-qwen25coder", TED_GATE_KEY_COD, usar_identidade)


async def _ollama_livre(prompt: str, usar_identidade: bool = True) -> str:
    return await _via_gate(prompt, "ted-livre-local-dolphinphi", TED_GATE_KEY_LIVRE, usar_identidade)


def _mensagens(prompt: str, usar_identidade: bool) -> list[dict]:
    """2026-08-21: SYSTEM_PROMPT so entra quando usar_identidade=True. Descoberto na marra --
    classificacao de dominio (task_type='fast') exige resposta de UMA PALAVRA, e o system
    prompt (que fala de portugues simples, 'diga que nao sabe', etc) confundia o modelo,
    fazendo ele devolver um paragrafo de raciocinio em vez da palavra pedida. Identidade do Ted
    so faz sentido pra conversa de verdade, nunca pra tarefa de classificacao/extracao."""
    msgs = []
    if usar_identidade:
        msgs.append({"role": "system", "content": SYSTEM_PROMPT})
    msgs.append({"role": "user", "content": prompt})
    return msgs


async def _via_gate(prompt: str, modelo: str, chave: str, usar_identidade: bool = True) -> str:
    if not chave:
        raise RuntimeError(f"Chave do TED GATE não configurada para {modelo}")
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{TED_GATE_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {chave}"},
            json={"model": modelo, "messages": _mensagens(prompt, usar_identidade)},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]


async def _groq(prompt: str, usar_identidade: bool = True) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY não configurada")
    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": MODELO_GROQ,
                "messages": _mensagens(prompt, usar_identidade),
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _gemini_gemma(prompt: str, usar_identidade: bool = True) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada")
    corpo = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 2000},
    }
    if usar_identidade:
        corpo["systemInstruction"] = {"parts": [{"text": SYSTEM_PROMPT}]}
    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_GEMINI}:generateContent?key={GEMINI_API_KEY}",
            json=corpo,
        )
        resp.raise_for_status()
        data = resp.json()
        parts = data["candidates"][0]["content"]["parts"]
        texto = "".join(p["text"] for p in parts if not p.get("thought"))
        return texto


async def _nvidia(prompt: str, usar_identidade: bool = True) -> str:
    if not NVIDIA_API_KEY:
        raise RuntimeError("NVIDIA_API_KEY não configurada")
    # esse modelo só responde direito em modo stream (fica pendurado em non-stream)
    # e manda reasoning_content (pensamento interno) separado do content final -- MAS só
    # se tiver orçamento suficiente pra terminar de pensar E responder. 2026-09-03:
    # max_tokens subiu de 1024 pra 2500 e timeout de 30s pra 60s -- com 1024 (e pior
    # ainda, 150, testado direto) o "pensamento" as vezes consome o max_tokens inteiro
    # e a resposta final nunca chega, ficando só reasoning cru no content. Confirmado
    # limpo com 2000+. Nunca baixar de 2000 aqui.
    partes = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
            json={
                "model": MODELO_NVIDIA,
                "messages": _mensagens(prompt, usar_identidade),
                "stream": True,
                "max_tokens": 2500,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[len("data: "):]
                if payload.strip() == "[DONE]":
                    break
                chunk = json.loads(payload)
                delta = chunk["choices"][0]["delta"]
                if delta.get("content"):
                    partes.append(delta["content"])
    return "".join(partes)


# modelos GRATUITOS do OpenRouter (catalogo reconferido em 2026-09-03 via /api/v1/models --
# os 2 antigos (glm-5.2, north-mini-code) continuam validos e responderam limpo no teste.
# NUNCA trocar por modelo pago aqui -- JPM pagou pra desbloquear limite diario maior nos
# modelos :free (50 -> 1800/dia), nao pra a gente gastar credito automatico. Ver
# task_type="openrouter" manual pra qualquer uso pago explicito, fora dessa lista.
# Diversidade proposital de laboratorio: Google/Gemma ja tem via gemini_gemma, NVIDIA ja
# tem via nvidia direto -- aqui so laboratorios que nao aparecem em outro lugar da cascata.
# 2026-09-03: adicionado minimax-m3 como 3o fallback (testado, responde limpo, 1M ctx,
# lab MiniMax nao tinha representante na cascata ainda) -- so aumenta resiliencia, mesmo
# pool de conta/RPM dos outros dois, nao gasta cota extra.
MODELOS_OPENROUTER_GRATIS = _MODELOS.get(
    "openrouter_modelos",
    ["z-ai/glm-5.2:free", "cohere/north-mini-code:free", "minimax/minimax-m3:free"],
)


async def _openrouter(prompt: str, usar_identidade: bool = True) -> str:
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_KEY não configurada")
    erros = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for modelo in MODELOS_OPENROUTER_GRATIS:
            try:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
                    json={
                        "model": modelo,
                        "messages": _mensagens(prompt, usar_identidade),
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                erros.append(f"{modelo}: {e}")
    raise RuntimeError(f"todos os modelos gratis do openrouter falharam: {erros}")


PROVEDORES = {
    "ollama_local": _ollama_local,
    "ollama_escrita": _ollama_escrita,
    "ollama_cod": _ollama_cod,
    "ollama_livre": _ollama_livre,
    "groq": _groq,
    "gemini_gemma": _gemini_gemma,
    "nvidia": _nvidia,
    "openrouter": _openrouter,
}


def _comprime_prompt_longo(texto: str) -> str:
    """Corta o meio de prompts muito longos (ex: log/arquivo colado inteiro) mantendo
    inicio e fim -- normalmente onde esta o contexto e o resultado/erro final -- em vez
    de gastar tokens (e as vezes estourar o limite do provedor) com o miolo repetitivo.
    Nao chama IA nenhuma pra comprimir -- corte simples e determinístico, sem custo."""
    if len(texto) <= PROMPT_MAX_CHARS:
        return texto
    metade = PROMPT_MAX_CHARS // 2
    cortados = len(texto) - PROMPT_MAX_CHARS
    return (
        texto[:metade]
        + f"\n\n[...{cortados} caracteres cortados no meio pra economizar tokens...]\n\n"
        + texto[-metade:]
    )


@app.post("/ted/router")
async def router(req: RouterRequest):
    req.prompt = _comprime_prompt_longo(req.prompt)
    chave_cache = req.task_type + "::" + req.prompt.strip().lower()
    if req.usar_cache:
        achado = _cache_get(chave_cache)
        if achado:
            resposta, provedor = achado
            return {"resposta": resposta, "provedor_usado": provedor + " (cache)"}

    cascata = CASCATA.get(req.task_type, CASCATA["default"])
    erros = []
    agora = time.time()
    for nome_provedor in cascata:
        se_restante = _cooldown_until.get(nome_provedor, 0) - agora
        if se_restante > 0:
            erros.append(f"{nome_provedor}: em cooldown por 429, volta em {int(se_restante)}s")
            continue
        func = PROVEDORES[nome_provedor]
        # "fast" e usado pelo classificador de dominio do TED Master, que exige resposta de
        # UMA PALAVRA -- system prompt de identidade atrapalha isso, so entra pros outros.
        usar_identidade = req.task_type != "fast"
        try:
            resposta = await func(req.prompt, usar_identidade)
            _registrar_uso(nome_provedor)
            if req.usar_cache:
                _cache_set(chave_cache, resposta, nome_provedor)
            return {"resposta": resposta, "provedor_usado": nome_provedor}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                _cooldown_until[nome_provedor] = agora + COOLDOWN_SECONDS
            erros.append(f"{nome_provedor}: {e}")
        except Exception as e:
            erros.append(f"{nome_provedor}: {e}")
    raise HTTPException(status_code=502, detail={"erro": "Todos os provedores falharam", "detalhes": erros})


@app.get("/ted/router/health")
async def health():
    return {"status": "ok"}


@app.get("/ted/router/cooldowns")
async def cooldowns():
    agora = time.time()
    return {p: max(0, int(t - agora)) for p, t in _cooldown_until.items() if t > agora}


@app.get("/ted/router/cache_stats")
async def cache_stats():
    agora = time.time()
    validas = sum(1 for (expira, _, _) in _CACHE.values() if expira > agora)
    return {"entradas_validas": validas, "entradas_totais": len(_CACHE), "ttl_segundos": CACHE_TTL_SECONDS}
