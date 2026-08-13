import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

TED_GATE_URL = os.environ.get("TED_GATE_URL", "http://100.122.103.89:4003")
TED_GATE_KEY_ESCRITA = os.environ.get("TED_GATE_KEY_ESCRITA", "")
TED_GATE_KEY_COD = os.environ.get("TED_GATE_KEY_COD", "")
TED_GATE_KEY_LIVRE = os.environ.get("TED_GATE_KEY_LIVRE", "")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "")

# cascata automatica (fallback em sequencia). openrouter fica de fora --
# so acessivel explicito via task_type="openrouter" (secao 6.1 do v1.1: OpenRouter/Anthropic sao manuais)
CASCATA = {
    "local": ["ollama_local", "groq", "gemini_gemma"],
    "fast": ["groq", "ollama_local", "gemini_gemma"],
    "code": ["ollama_cod", "groq"],
    "escrita": ["ollama_escrita", "groq"],
    "livre": ["ollama_livre"],
    "openrouter": ["openrouter"],
    "nvidia": ["nvidia"],
    "default": ["gemini_gemma", "groq", "nvidia", "ollama_local"],
}


class RouterRequest(BaseModel):
    prompt: str
    task_type: str = "default"


async def _ollama_local(prompt: str) -> str:
    return await _via_gate(prompt, "ted-escrita-local-gemma2", TED_GATE_KEY_ESCRITA)


async def _ollama_escrita(prompt: str) -> str:
    return await _via_gate(prompt, "ted-escrita-local-gemma2", TED_GATE_KEY_ESCRITA)


async def _ollama_cod(prompt: str) -> str:
    return await _via_gate(prompt, "ted-cod-local-qwen25coder", TED_GATE_KEY_COD)


async def _ollama_livre(prompt: str) -> str:
    return await _via_gate(prompt, "ted-livre-local-dolphinphi", TED_GATE_KEY_LIVRE)


async def _via_gate(prompt: str, modelo: str, chave: str) -> str:
    if not chave:
        raise RuntimeError(f"Chave do TED GATE não configurada para {modelo}")
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{TED_GATE_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {chave}"},
            json={"model": modelo, "messages": [{"role": "user", "content": prompt}]},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]


async def _groq(prompt: str) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY não configurada")
    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _gemini_gemma(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada")
    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 2000},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        parts = data["candidates"][0]["content"]["parts"]
        texto = "".join(p["text"] for p in parts if not p.get("thought"))
        return texto


async def _nvidia(prompt: str) -> str:
    if not NVIDIA_API_KEY:
        raise RuntimeError("NVIDIA_API_KEY não configurada")
    # esse modelo só responde direito em modo stream (fica pendurado em non-stream)
    # e manda reasoning_content (pensamento interno) separado do content final
    partes = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream(
            "POST",
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
            json={
                "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "max_tokens": 1024,
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


async def _openrouter(prompt: str) -> str:
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_KEY não configurada")
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={
                "model": "openai/gpt-oss-20b:free",
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


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


@app.post("/ted/router")
async def router(req: RouterRequest):
    cascata = CASCATA.get(req.task_type, CASCATA["default"])
    erros = []
    for nome_provedor in cascata:
        func = PROVEDORES[nome_provedor]
        try:
            resposta = await func(req.prompt)
            return {"resposta": resposta, "provedor_usado": nome_provedor}
        except Exception as e:
            erros.append(f"{nome_provedor}: {e}")
    raise HTTPException(status_code=502, detail={"erro": "Todos os provedores falharam", "detalhes": erros})


@app.get("/ted/router/health")
async def health():
    return {"status": "ok"}
