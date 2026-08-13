import os
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

OP2_HOST = os.environ.get("OP2_HOST", "op2-ted.tail2a272d.ts.net")
OLLAMA_URL = f"http://{OP2_HOST}:11434"
ROUTER_URL = os.environ.get("ROUTER_URL", "http://localhost:8010/ted/router")

# limite de modelos ja carregados no Ollama pra considerar "ocupado" -- ver com OLLAMA_MAX_LOADED_MODELS=1
LIMITE_OCUPADO = 1


async def _carga_op2() -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{OLLAMA_URL}/api/ps")
        resp.raise_for_status()
        modelos = resp.json().get("models", [])
    return {
        "modelos_carregados": len(modelos),
        "nomes": [m.get("name") for m in modelos],
        "ocupado": len(modelos) >= LIMITE_OCUPADO,
    }


@app.get("/ted/orchestrator/status")
async def status():
    try:
        carga = await _carga_op2()
        carga["op2_alcancavel"] = True
    except Exception as e:
        carga = {"op2_alcancavel": False, "erro": str(e)}
    return carga


class DispatchRequest(BaseModel):
    prompt: str
    preferencia: str = "auto"  # auto | local | cloud


@app.post("/ted/orchestrator/dispatch")
async def dispatch(req: DispatchRequest):
    rota = "local"
    motivo = "preferencia explicita"

    if req.preferencia == "cloud":
        rota = "cloud"
    elif req.preferencia == "local":
        rota = "local"
    else:
        try:
            carga = await _carga_op2()
            if not carga.get("op2_alcancavel", True) or carga.get("ocupado"):
                rota = "cloud"
                motivo = "OP2 ocupado ou inalcançável — foi pra nuvem"
            else:
                rota = "local"
                motivo = "OP2 livre — processou local"
        except Exception:
            rota = "cloud"
            motivo = "não deu pra checar carga do OP2 — foi pra nuvem por segurança"

    task_type = "local" if rota == "local" else "default"

    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(ROUTER_URL, json={"prompt": req.prompt, "task_type": task_type})
        resp.raise_for_status()
        resultado = resp.json()

    return {"rota_escolhida": rota, "motivo": motivo, **resultado}


@app.get("/ted/orchestrator/health")
async def health():
    return {"status": "ok"}
