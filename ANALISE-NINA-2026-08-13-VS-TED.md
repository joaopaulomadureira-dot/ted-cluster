# Análise: Evolução do Nina (13/08/2026) vs. Estado Atual do TED

**Fontes**: `Historia-Completa-Ecossistema-Nina-v2.1-a-hoje.pdf` + `Relatorio-Build-Ecossistema-Nina-2026-08-13.pdf`
**Regra de leitura**: Nina é referência, não decisão pronta. Cada item abaixo é "vale considerar", não "já apliquei".

---

## 1. O que já bate — Nina confirma escolhas que o TED já tomou

| Item | Nina descobriu | TED já fez igual |
|---|---|---|
| Exo | Investigação nova (11/08): Exo hoje **exige MLX** (Apple Silicon), sem fallback CPU nenhum — a versão que o v2.1/v1.0 descreviam não existe mais | ✅ Já descartamos Exo (latência WAN OP1↔OP2) — a razão do Nina é ainda mais forte (nem rodaria de jeito nenhum nos Intel) |
| Docker runtime | OrbStack não sobe sem sessão gráfica principal — bateram nisso na prática, trocaram pra Colima | ✅ Já fomos direto de Colima, sem passar pelo problema |
| Backup Restic | Corrigido de "MinIO no próprio OP2" pra "SSD externo do OP1" — ponto único de falha com o Vaultwarden | ✅ Já fizemos isso hoje (repositório no OP1, separado) |
| Doctor Agent x Uptime Kuma | Nina teve que **corrigir depois** (schedule fixo de 5min duplicava alerta) | ✅ TED já nasceu certo nisso — webhook-only desde o início |
| SSH | Endurecido: só chave, porta 22 bloqueada na LAN | ✅ Já fizemos igual hoje |
| Anthropic no Router | Removida de vez — nunca teve chave, decisão formal de nunca ter | ➡️ TED nunca teve Anthropic na cascata pra começo de conversa — mesmo resultado, caminho mais curto |

**Leitura**: os 7 princípios (P1-P7) sobreviveram intactos nos dois ecossistemas. O documento do Nina confirma a tese do v1.1: gastar tempo confirmando premissas de hardware/software antes de construir em cima delas evita retrabalho.

---

## 2. Diferença real que vale revisar — cascata do Router

**Nina (final, com dados reais de performance)**: `Gemini Gemma 31B → Gemini Gemma 26B → Groq 70B → Local`, com **OpenRouter e NVIDIA também fora da cascata automática** (só manual, junto com Anthropic).

**TED (hoje)**: `gemini_gemma → groq → nvidia → ollama_local` — NVIDIA está **dentro** da cascata automática, 3ª posição.

Isso diverge do que o próprio documento v1.1 do TED pede (seção 6.1: "OpenRouter e Anthropic tratados como providers manuais... fora da cascata automática" — não fala de NVIDIA explicitamente, mas o Nina decidiu tirar ela também). Não mudei isso sozinho — é uma decisão sua: manter NVIDIA na cascata automática ou tirar ela também (só ficaria acessível via `task_type: "nvidia"`, que já existe).

---

## 3. Gap real — OpenCode nunca foi instalado em nenhum nó do TED

Isso é o achado mais acionável do relatório. O v1.1 do TED (seção 9, passo 3) **já pede** OpenCode nos 4 nós — mas nenhuma sessão até agora instalou de verdade. Todo trabalho de hoje foi feito por mim direto (Claude Code via SSH), não pelo OpenCode — exatamente o mesmo desvio que o Nina teve até ontem (12/08) e só corrigiu formalmente hoje (13/08).

**Achado técnico direto do Nina, aplicável ao TED sem adaptação** (OP1/OP2 do TED são a mesma classe de hardware — Intel sem AVX2):

> O binário nativo do OpenCode trava com `SIGILL` em CPU Intel sem AVX2 — mesmo problema documentado antes com o Tailscale CLI. Solução: rodar via pacote npm (`opencode-ai`) dentro de um container Docker Linux, que não tem essa exigência. Imagem fixa (`node:20-bookworm` + `npm i -g opencode-ai`) + wrapper de shell que monta `$PWD` como `/workspace` e persiste `$HOME/.opencode-docker-state` como `/root` do container, detectando TTY interativo.

No GERENTE/COORD (Apple Silicon) seria instalação nativa direta, sem esse problema.

**Isso não instala sozinho** — decisão sua se quer que eu resolva isso agora ou não.

---

## 4. Gaps opcionais — agentes que o Nina tem e o TED não

Nenhum destes estava no v1.1 original do TED — são adições que o Nina fez por iniciativa do JPM lá, não correções de bug. Trago só como inventário, sem recomendar nenhum:

| Agente do Nina | O que faz | Faz sentido pro TED? |
|---|---|---|
| **MCP Agent** | Expõe Router/DocReader/Orchestrator como ferramentas que o OpenCode chama sozinho | Só relevante depois do item 3 (OpenCode) estar de pé — aí sim, útil |
| **Cluster Orchestrator** | Decide em qual nó rodar cada tarefa conforme carga real | TED tem só 2 nós de operação (OP1/OP2) com papéis bem separados (agentes vs infra) — o cenário de "múltiplos nós disputando carga" é menos aplicável aqui |
| **Auditor Agent** | Auditoria diária 3h15, consenso 70/30 entre 3 IAs, corrige sozinho o que é seguro | Interessante pro TED conforme cresce, mas exige ter pelo menos 3 IAs cascata madura primeiro |
| **OpenWA + Agente WhatsApp** | Lê conversas de WhatsApp, constrói memória pessoal sobre o dono do número | É uma direção de produto (assistente pessoal), não de infra — só faz sentido se você quiser isso pro TED especificamente, não é "correção" nem "melhoria de infra" |

---

## 5. Lições técnicas soltas, guardar pra quando forem relevantes

- **SDK do MCP mudou de nome de classe** (`FastMCP` → `mcp.server.mcpserver.MCPServer`) — se um dia construirmos MCP Agent, checar a API real instalada antes de escrever código, não confiar em treinamento antigo.
- **Não colar chave de LLM crua no config do OpenCode** — se OpenCode + MCP Agent virarem realidade no TED, expor o Router como ferramenta MCP em vez de duplicar chaves, senão viram dois consumidores de cota sem coordenação.
- **`docker-compose.override.yml` pode não fazer merge de verdade** — sempre confirmar com `docker compose config` antes de assumir que um override pegou; se não pegar, editar o arquivo base direto é mais confiável.
- Padrão de verificação do Nina em todo item: nunca só "o serviço está no ar", sempre um teste funcional real (ex: ler um projeto real com o OpenCode, não só rodar `--version`). Já é o padrão que venho seguindo aqui hoje.

---

## Resumo pra decisão sua

1. **Cascata NVIDIA** — automática (como está) ou manual (como o Nina decidiu)?
2. **OpenCode no TED** — instalar agora (tenho a receita pronta do Docker/AVX2) ou deixar pra depois?
3. **MCP/Orchestrator/Auditor/WhatsApp** — nenhum é urgente; me diga se algum interessa como próximo passo real.
