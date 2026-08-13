import os
import httpx
import chromadb
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI()

CHROMADB_HOST = os.environ.get("CHROMADB_HOST", "100.122.103.89")
CHROMADB_PORT = int(os.environ.get("CHROMADB_PORT", "8000"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://100.122.103.89:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "ted-embed-local-nomic")

_chroma = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
_colecao = _chroma.get_or_create_collection("ted_docs")


def _chunk(texto: str, tamanho: int = 512, overlap: int = 64):
    palavras = texto.split()
    chunks = []
    i = 0
    while i < len(palavras):
        chunks.append(" ".join(palavras[i:i + tamanho]))
        i += tamanho - overlap
    return chunks


async def _embed(texto: str) -> list[float]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": texto},
        )
        resp.raise_for_status()
        return resp.json()["embedding"]


class QueryRequest(BaseModel):
    pergunta: str
    top_k: int = 4


@app.post("/ted/docs/ingest")
async def ingest(file: UploadFile = File(...)):
    if not file.filename.endswith((".md", ".txt")):
        return {"erro": "Só Markdown/texto suportado por enquanto — PDF pendente (ver nota do documento v1.1)"}

    conteudo = (await file.read()).decode("utf-8", errors="ignore")
    chunks = _chunk(conteudo)

    ids, embeddings, documentos, metadados = [], [], [], []
    for idx, chunk in enumerate(chunks):
        ids.append(f"{file.filename}::{idx}")
        embeddings.append(await _embed(chunk))
        documentos.append(chunk)
        metadados.append({"fonte": file.filename, "chunk": idx})

    _colecao.upsert(ids=ids, embeddings=embeddings, documents=documentos, metadatas=metadados)
    return {"documento": file.filename, "chunks": len(chunks)}


@app.post("/ted/docs/query")
async def query(req: QueryRequest):
    embedding = await _embed(req.pergunta)
    resultado = _colecao.query(query_embeddings=[embedding], n_results=req.top_k)
    respostas = []
    docs = resultado.get("documents", [[]])[0]
    metas = resultado.get("metadatas", [[]])[0]
    dists = resultado.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        respostas.append({"trecho": doc, "fonte": meta.get("fonte"), "chunk": meta.get("chunk"), "distancia": dist})
    return {"pergunta": req.pergunta, "resultados": respostas}


@app.get("/ted/docs/list")
async def listar():
    dados = _colecao.get()
    fontes = sorted({m["fonte"] for m in dados.get("metadatas", [])})
    return {"documentos": fontes}


@app.get("/ted/docs/health")
async def health():
    return {"status": "ok"}
