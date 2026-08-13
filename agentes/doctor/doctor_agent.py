import os
import httpx
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

_ultimo_alerta = {}


async def _telegram(mensagem: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem},
        )


@app.post("/ted/doctor/webhook")
async def webhook(request: Request):
    payload = await request.json()
    servico = payload.get("monitor", {}).get("name", "desconhecido")
    status = payload.get("heartbeat", {}).get("status")

    chave = f"{servico}:{status}"
    if _ultimo_alerta.get(servico) == status:
        return {"ignorado": "sem mudança de estado"}
    _ultimo_alerta[servico] = status

    estado = "DOWN" if status == 0 else "UP"
    msg = f"🩺 TED Doctor: {servico} está {estado}"
    await _telegram(msg)
    return {"alertado": True, "servico": servico, "estado": estado}


@app.post("/ted/doctor/diagnose")
async def diagnose():
    return {"status": "diagnóstico manual não implementado ainda — usar /ted/doctor/health"}


@app.get("/ted/doctor/health")
async def health():
    return {"status": "ok"}
