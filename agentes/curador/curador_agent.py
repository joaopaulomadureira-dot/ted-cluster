import os
import json
import hashlib
import subprocess
from pathlib import Path
import httpx
from datetime import datetime, timezone
from fastapi import FastAPI

app = FastAPI()

INBOX = Path(os.path.expanduser("~/Ted/inbox-manutencao"))
PROCESSADOS_DIR = INBOX / "processados"
REGISTRO = INBOX / ".processed.json"

DOCREADER_URL = os.environ.get("DOCREADER_URL", "http://op1-ted.tail2a272d.ts.net:8012/ted/docs/ingest")
OUTLINE_MCP_URL = os.environ.get("OUTLINE_MCP_URL", "http://op2-ted.tail2a272d.ts.net:3002/mcp")
OUTLINE_API_KEY = os.environ.get("OUTLINE_API_KEY", "")
OUTLINE_COLLECTION_ID = os.environ.get("OUTLINE_COLLECTION_ID", "")

INBOX.mkdir(parents=True, exist_ok=True)
PROCESSADOS_DIR.mkdir(parents=True, exist_ok=True)


def _carregar_registro() -> dict:
    if REGISTRO.exists():
        try:
            return json.loads(REGISTRO.read_text())
        except Exception:
            return {}
    return {}


def _salvar_registro(reg: dict):
    REGISTRO.write_text(json.dumps(reg, indent=2, ensure_ascii=False))


def _hash_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    h.update(caminho.read_bytes())
    return h.hexdigest()[:16]


def _extrair_texto(pdf_path: Path) -> str:
    r = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"pdftotext falhou: {r.stderr}")
    return r.stdout


async def _indexar_docreader(nome: str, texto: str) -> dict:
    txt_name = nome.rsplit(".", 1)[0] + ".txt"
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            DOCREADER_URL,
            files={"file": (txt_name, texto.encode("utf-8"), "text/plain")},
        )
        resp.raise_for_status()
        return resp.json()


async def _criar_no_outline(nome: str, texto: str) -> dict:
    if not OUTLINE_API_KEY:
        return {"criado": False, "motivo": "OUTLINE_API_KEY nao configurada"}
    trecho = texto[:8000]
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            OUTLINE_MCP_URL,
            headers={
                "Authorization": f"Bearer {OUTLINE_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            content=json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {
                    "name": "create_document",
                    "arguments": {
                        "title": f"Manutenção — {nome}",
                        "text": f"Documento extraído automaticamente pelo Agente Curador de Manutenção.\n\n---\n\n{trecho}",
                        "publish": True,
                    },
                },
            }),
        )
        resp.raise_for_status()
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                dados = json.loads(line[5:])
                if "error" in dados:
                    return {"criado": False, "motivo": dados["error"]}
                return {"criado": True, "resultado": dados.get("result")}
    return {"criado": False, "motivo": "resposta inesperada do Outline MCP"}


async def _processar_um(pdf_path: Path, registro: dict) -> dict:
    texto = _extrair_texto(pdf_path)
    docreader_resultado = await _indexar_docreader(pdf_path.name, texto)
    outline_resultado = await _criar_no_outline(pdf_path.name, texto)

    destino = PROCESSADOS_DIR / pdf_path.name
    pdf_path.rename(destino)

    return {
        "arquivo": pdf_path.name,
        "chars_extraidos": len(texto),
        "docreader": docreader_resultado,
        "outline": outline_resultado,
    }


@app.post("/ted/curador/scan")
async def escanear():
    registro = _carregar_registro()
    resultados = []
    for pdf in sorted(INBOX.glob("*.pdf")):
        h = _hash_arquivo(pdf)
        chave = f"{pdf.name}:{h}"
        if chave in registro:
            continue
        try:
            resultado = await _processar_um(pdf, registro)
            registro[chave] = {"processado_em": datetime.now(timezone.utc).isoformat(), **resultado}
            resultados.append(resultado)
        except Exception as e:
            resultados.append({"arquivo": pdf.name, "erro": str(e)})

    _salvar_registro(registro)
    return {"processados": resultados, "total_no_registro": len(registro)}


@app.get("/ted/curador/health")
async def health():
    return {"status": "ok"}
