import httpx
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("ted-cluster")

ROUTER_URL = "http://localhost:8010/ted/router"
DOCS_URL = "http://localhost:8012/ted/docs/query"
ORCH_URL = "http://localhost:8013/ted/orchestrator"


@mcp.tool()
def busca_documentacao_ted(pergunta: str, top_k: int = 4) -> dict:
    """Busca semântica na documentação indexada do cluster TED (o documento v1.1, decisões de arquitetura, etc.). Use quando precisar saber como o TED foi projetado ou decisões já tomadas."""
    r = httpx.post(DOCS_URL, json={"pergunta": pergunta, "top_k": top_k}, timeout=90)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def perguntar_ia_ted(prompt: str, task_type: str = "default") -> dict:
    """Manda um prompt pra cascata de LLMs do TED (Gemini/Groq/NVIDIA/Ollama local, com fallback automático e controle de cota). Use em vez de chamar uma API de LLM direto -- isso mantém o controle de cota centralizado."""
    r = httpx.post(ROUTER_URL, json={"prompt": prompt, "task_type": task_type}, timeout=180)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def status_carga_cluster() -> dict:
    """Consulta a carga atual do cluster TED (se o OP2 está ocupado processando modelo local ou livre). Use antes de disparar tarefas pesadas, ou pra decidir se vale mandar algo local ou pra nuvem."""
    r = httpx.get(f"{ORCH_URL}/status", timeout=10)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8015)
