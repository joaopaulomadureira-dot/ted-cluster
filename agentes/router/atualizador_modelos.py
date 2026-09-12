"""
Atualizador semanal de modelos do Router (TED).

Roda 1x por semana (launchd, domingo 06h, com.ted.atualizador-modelos) e verifica se os
modelos GRATUITOS configurados no router_agent.py (Groq, Gemini, OpenRouter) ainda existem
no catalogo ao vivo de cada provedor. Se um modelo sumiu, troca por um da lista de
candidatos aprovados (mesma familia/qualidade) SEM precisar de deploy manual -- so
reescreve modelos_atual.json e reinicia o router.

NVIDIA e proposital NAO tem lista de candidatos pra troca automatica ainda: a auditoria
de 2026-09-03 achou uma resposta suja num teste, mas era falso alarme -- max_tokens baixo
demais no teste (150), nao bug do modelo (com 2000+ a resposta sai limpa, corrigido em
_nvidia() no router_agent.py). Mesmo sem bug real, trocar de MODELO NVIDIA ainda exige
confirmar que o max_tokens/timeout usado aqui continuam suficientes pro modelo novo antes
de confiar de olhos fechados -- esse script so ALERTA se o modelo atual sumir do catalogo,
nao troca sozinho ate essa checagem de orcamento de tokens ser automatizada tambem.

Escreve tudo em relatorio_atualizacao_modelos.log (mesma pasta) -- conferir ali antes de
mexer manualmente em modelos_atual.json.
"""
import os
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

PASTA = Path(__file__).parent
load_dotenv(PASTA / ".env")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "")

MODELOS_PATH = PASTA / "modelos_atual.json"
LOG_PATH = PASTA / "relatorio_atualizacao_modelos.log"

# candidatos aprovados, em ordem de preferencia -- so entram aqui modelos ja testados
# manualmente (resposta limpa, sem vazamento de raciocinio/pensamento na resposta final)
CANDIDATOS_GROQ = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "groq/compound", "qwen/qwen3.8-27b"]
CANDIDATOS_GEMINI = ["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]


def log(msg):
    linha = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}"
    print(linha)
    with open(LOG_PATH, "a") as f:
        f.write(linha + "\n")


def carregar_modelos():
    return json.loads(MODELOS_PATH.read_text())


def salvar_modelos(dados, resumo):
    dados["ultima_atualizacao"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dados["ultimo_resultado"] = resumo
    MODELOS_PATH.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n")


def checar_groq(atual_id):
    r = httpx.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        timeout=15.0,
    )
    r.raise_for_status()
    ids_ativos = {m["id"] for m in r.json().get("data", [])}
    if atual_id in ids_ativos:
        return atual_id, False, "modelo atual ainda existe no catalogo Groq"
    for candidato in CANDIDATOS_GROQ:
        if candidato in ids_ativos:
            return candidato, True, f"modelo '{atual_id}' sumiu do catalogo Groq -> trocado para '{candidato}'"
    return atual_id, False, f"ALERTA: modelo '{atual_id}' sumiu do catalogo Groq e NENHUM candidato aprovado esta disponivel -- revisar CANDIDATOS_GROQ manualmente"


def checar_gemini(atual_id):
    r = httpx.get(
        f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}",
        timeout=15.0,
    )
    r.raise_for_status()
    ids_ativos = {
        m["name"].replace("models/", "")
        for m in r.json().get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    }
    if atual_id in ids_ativos:
        return atual_id, False, "modelo atual ainda existe no catalogo Gemini"
    for candidato in CANDIDATOS_GEMINI:
        if candidato in ids_ativos:
            return candidato, True, f"modelo '{atual_id}' sumiu do catalogo Gemini -> trocado para '{candidato}'"
    return atual_id, False, f"ALERTA: modelo '{atual_id}' sumiu do catalogo Gemini e NENHUM candidato aprovado esta disponivel -- revisar CANDIDATOS_GEMINI manualmente"


def checar_nvidia(atual_id, nvidia_key):
    r = httpx.get(
        "https://integrate.api.nvidia.com/v1/models",
        headers={"Authorization": f"Bearer {nvidia_key}"},
        timeout=15.0,
    )
    r.raise_for_status()
    ids_ativos = {m["id"] for m in r.json().get("data", [])}
    if atual_id in ids_ativos:
        return atual_id, False, "modelo atual ainda existe no catalogo NVIDIA"
    return atual_id, False, (
        f"ALERTA: modelo '{atual_id}' sumiu do catalogo NVIDIA. NAO troquei sozinho de "
        f"proposito -- precisa confirmar manualmente que max_tokens>=2000/timeout>=60s "
        f"bastam pro modelo novo antes de trocar (licao de 2026-09-03: resposta sai suja "
        f"se o orcamento de tokens for baixo demais pro 'pensamento' do modelo)."
    )


def checar_openrouter(lista_atual):
    r = httpx.get("https://openrouter.ai/api/v1/models", timeout=15.0)
    r.raise_for_status()
    livres = [m for m in r.json()["data"] if m["id"].endswith(":free")]
    ids_livres = {m["id"] for m in livres}
    por_contexto = sorted(livres, key=lambda m: -m.get("context_length", 0))

    ainda_existe = [m for m in lista_atual if m in ids_livres]
    removidos = [m for m in lista_atual if m not in ids_livres]

    labs_representados = {m.split("/")[0] for m in ainda_existe}
    nova_lista = list(ainda_existe)
    for m in por_contexto:
        if len(nova_lista) >= 3:
            break
        lab = m["id"].split("/")[0]
        if m["id"] in nova_lista or lab in labs_representados:
            continue
        nova_lista.append(m["id"])
        labs_representados.add(lab)

    mudou = set(nova_lista) != set(lista_atual)
    if not mudou:
        return lista_atual, False, "os 3 modelos gratuitos do OpenRouter continuam validos"
    resumo = f"OpenRouter: removidos {removidos or '[]'}, lista nova = {nova_lista}"
    return nova_lista, True, resumo


def reiniciar_router():
    uid = subprocess.check_output(["id", "-u"]).decode().strip()
    subprocess.run(["launchctl", "kickstart", "-k", f"gui/{uid}/com.ted.router"], check=False)


def dias_desde_ultima_atualizacao(dados):
    ultima = dados.get("ultima_atualizacao")
    if not ultima:
        return None
    data_ultima = datetime.strptime(ultima, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - data_ultima).days


def main():
    dados = carregar_modelos()

    # Rede de seguranca: alem do gatilho semanal (StartCalendarInterval, domingo 06h), o
    # LaunchAgent tambem roda no login (RunAtLoad) -- necessario porque o OP1 as vezes
    # nao termina de ligar/logar a tempo do horario agendado (achado em 2026-09-12: o
    # atualizador nunca disparou sozinho no domingo 06/09 porque o boot daquele dia so
    # terminou as 08:57). Sem essa checagem de idade, um RunAtLoad puro rodaria toda vez
    # que o OP1 reinicia (varias vezes ao dia, ver historico de boot irregular) -- por
    # isso so roda de verdade se a ultima atualizacao bem-sucedida tiver mais de 6 dias.
    dias = dias_desde_ultima_atualizacao(dados)
    if dias is not None and dias < 6:
        log(f"=== atualizador semanal de modelos: pulado (ultima atualizacao ha {dias} dia(s), ainda nao completou 6) ===")
        return

    log("=== atualizador semanal de modelos: iniciando ===")
    mudancas = []
    alertas = []
    houve_mudanca = False

    try:
        novo, mudou, msg = checar_groq(dados["groq_model"])
        log(f"Groq: {msg}")
        if mudou:
            mudancas.append(msg)
            houve_mudanca = True
        if msg.startswith("ALERTA"):
            alertas.append(msg)
        dados["groq_model"] = novo
    except Exception as e:
        log(f"ERRO checando Groq (mantido valor atual): {e}")

    try:
        novo, mudou, msg = checar_gemini(dados["gemini_model"])
        log(f"Gemini: {msg}")
        if mudou:
            mudancas.append(msg)
            houve_mudanca = True
        if msg.startswith("ALERTA"):
            alertas.append(msg)
        dados["gemini_model"] = novo
    except Exception as e:
        log(f"ERRO checando Gemini (mantido valor atual): {e}")

    try:
        nvidia_key = os.environ.get("NVIDIA_API_KEY", "")
        _, _, msg = checar_nvidia(dados["nvidia_model"], nvidia_key)
        log(f"NVIDIA: {msg}")
        if msg.startswith("ALERTA"):
            alertas.append(msg)
    except Exception as e:
        log(f"ERRO checando NVIDIA (mantido valor atual): {e}")

    try:
        nova_lista, mudou, msg = checar_openrouter(dados["openrouter_modelos"])
        log(f"OpenRouter: {msg}")
        if mudou:
            mudancas.append(msg)
            houve_mudanca = True
        dados["openrouter_modelos"] = nova_lista
    except Exception as e:
        log(f"ERRO checando OpenRouter (mantida lista atual): {e}")

    resumo = "; ".join(mudancas) if mudancas else "nenhuma mudanca necessaria esta semana"
    if alertas:
        resumo += " | ALERTAS PENDENTES: " + "; ".join(alertas)
    salvar_modelos(dados, resumo)

    if houve_mudanca:
        log("mudanca detectada -> reiniciando com.ted.router")
        reiniciar_router()
    else:
        log("nenhuma mudanca -> router nao precisou reiniciar")

    if alertas:
        log(f"*** {len(alertas)} ALERTA(S) precisam de revisao humana -- ver acima ***")

    log("=== atualizador semanal de modelos: concluido ===")


if __name__ == "__main__":
    main()
