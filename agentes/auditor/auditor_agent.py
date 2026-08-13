import os
import asyncio
import subprocess
import httpx
from datetime import datetime
from fastapi import FastAPI

app = FastAPI()

OP2_HOST = os.environ.get("OP2_HOST", "op2-ted.tail2a272d.ts.net")
OP1_HOST = os.environ.get("OP1_HOST", "op1-ted.tail2a272d.ts.net")
ROUTER_URL = os.environ.get("ROUTER_URL", "http://localhost:8010/ted/router")

# allowlist fechada -- so essas acoes podem ser sugeridas/autoaplicadas, nada mais
AGENTES_OP1 = {
    "router": "com.ted.router",
    "doctor": "com.ted.doctor",
    "docreader": "com.ted.docreader",
    "orchestrator": "com.ted.orchestrator",
    "mcp": "com.ted.mcp",
}

_historico = []


async def _checar_agentes_op1() -> list[dict]:
    achados = []
    portas = {"router": 8010, "doctor": 8011, "docreader": 8012, "orchestrator": 8013, "mcp": 8015}
    async with httpx.AsyncClient(timeout=8.0) as client:
        for nome, porta in portas.items():
            try:
                path = "/mcp" if nome == "mcp" else f"/ted/{nome if nome != 'docreader' else 'docs'}/health"
                resp = await client.get(f"http://localhost:{porta}{path}")
                ok = resp.status_code < 500
            except Exception as e:
                ok = False
            if not ok:
                achados.append({"tipo": "agente_down", "agente": nome, "acao_sugerida": f"restart_agente:{nome}"})
    return achados


async def _checar_containers_op2() -> list[dict]:
    achados = []
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(f"http://{OP2_HOST}:4003/health")
            if resp.status_code >= 500:
                achados.append({"tipo": "ted_gate_down", "acao_sugerida": "nenhuma (fora do allowlist)"})
    except Exception:
        achados.append({"tipo": "op2_inalcancavel", "acao_sugerida": "nenhuma (fora do allowlist)"})
    return achados


def _restart_agente(nome: str) -> str:
    label = AGENTES_OP1.get(nome)
    if not label:
        return "recusado: nao esta na allowlist"
    plist = f"/Users/tedop1/Library/LaunchAgents/{label}.plist"
    subprocess.run(["launchctl", "unload", plist], capture_output=True)
    subprocess.run(["launchctl", "load", plist], capture_output=True)
    return f"reiniciado: {nome}"


async def _consultar_ia(pergunta: str, task_type: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(ROUTER_URL, json={"prompt": pergunta, "task_type": task_type})
            resp.raise_for_status()
            return resp.json().get("resposta", "")
    except Exception as e:
        return f"erro: {e}"


async def _consenso_autofix(achado: dict) -> dict:
    """Pergunta pra 3 IAs (providers diferentes) se e seguro autoaplicar a acao sugerida.
    So autoaplica se pelo menos 2 das 3 concordarem (maioria, ~70%)."""
    acao = achado.get("acao_sugerida", "")
    if not acao.startswith("restart_agente:"):
        return {"consenso": False, "motivo": "acao fora da allowlist, nao pergunta pra IA"}

    pergunta = (
        f"Achado de auditoria no cluster TED: {achado}. "
        f"A acao sugerida e '{acao}' (reiniciar um agente FastAPI local via launchctl, sem perda de dados). "
        f"Responda SO 'SIM' ou 'NAO': e seguro autoaplicar essa acao agora?"
    )
    # 3 opinioes de providers diferentes, em paralelo
    respostas = await asyncio.gather(
        _consultar_ia(pergunta, "fast"),       # groq
        _consultar_ia(pergunta, "default"),    # gemini_gemma
        _consultar_ia(pergunta, "nvidia"),     # nvidia
    )
    votos_sim = sum(1 for r in respostas if "SIM" in r.upper()[:10])
    aprovado = votos_sim >= 2
    return {"consenso": aprovado, "votos_sim": votos_sim, "respostas": respostas}


@app.post("/ted/auditor/run")
async def rodar_auditoria():
    achados = []
    achados += await _checar_agentes_op1()
    achados += await _checar_containers_op2()

    resultado = {"timestamp": datetime.utcnow().isoformat(), "achados": achados, "acoes": []}

    for achado in achados:
        consenso = await _consenso_autofix(achado)
        entrada = {"achado": achado, "consenso": consenso}
        if consenso.get("consenso"):
            acao = achado["acao_sugerida"].split(":", 1)[1]
            entrada["resultado_acao"] = _restart_agente(acao)
        resultado["acoes"].append(entrada)

    _historico.append(resultado)
    if len(_historico) > 30:
        _historico.pop(0)
    return resultado


@app.get("/ted/auditor/history")
async def historico():
    return {"execucoes": _historico[-10:]}


@app.get("/ted/auditor/health")
async def health():
    return {"status": "ok"}
