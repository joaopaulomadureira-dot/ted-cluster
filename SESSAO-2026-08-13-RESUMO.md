# Sessão 13/08/2026 — Resumo (Fase 2 completa + paridade Nina)

**Status geral**: Fase 2 (instalação) fechada. Cluster com 12 serviços no OP2, 6 agentes no OP1, OpenCode nos 4 nós, GitHub configurado com auto-commit. Sessão gigante — retomar daqui.

---

## ✅ Acesso e segurança

- SSH restaurado do GERENTE pra COORD/OP1/OP2 (chave `~/.ssh/ted_rsa`, usuários reais: `tedcoord02`, `tedop1`, `tedop2` — não são os nomes óbvios)
- `PasswordAuthentication no` nos 3 nós (só chave)
- Regra pf bloqueando porta 22 na LAN + LaunchDaemon persistente em COORD e OP1 (pulado no OP2 por risco de lockout sem acesso físico)
- Hostnames Tailscale renomeados: `gerente-ted`, `coord-ted`, `op1-ted`, `op2-ted` (domínio real: `tail2a272d.ts.net`) — antes tinham nomes genéricos

## ✅ OP2 — Infraestrutura (12 serviços via Colima + docker-compose)

Postgres, MinIO, Vaultwarden (HTTPS via Caddy com cert self-signed estático — `tls internal` do Caddy não funcionava nesse ambiente), Redis, Caddy, n8n, Uptime Kuma, Outline, ChromaDB, Open WebUI, Beszel, Dozzle.

- **Restic**: migrado do OP2 pro OP1 (SFTP, chave dedicada `~/.ssh/ted_restic_key`), backup diário 3h, testado
- **TED GATE**: reescrito (timeout 120s→300s, tratamento de erro decente)
- **Modelos Ollama**: `ted-escrita-local-gemma2`, `ted-cod-local-qwen25coder`, `ted-livre-local-dolphinphi` (trocado do dolphin3 8B que travava), `ted-cod-local-phi4mini`, `ted-embed-local-nomic`
- **Uptime Kuma**: conta admin criada via Playwright (login/senha no `TED_INFRA_CHAVES.md`), 18 monitores, todos verdes
- **Vaultwarden**: conta pessoal do JPM criada (signup reaberto temporariamente, fechado de novo depois)
- **n8n**: conta criada, 2 workflows (Uptime Kuma→Doctor Agent testado ponta a ponta; teste manual do Router)

## ✅ OP1 — Agentes (6 no total agora)

| Agente | Porta | Status |
|---|---|---|
| Router | 8010 | Cascata corrigida (`gemini_gemma→groq→nvidia→ollama_local`), chaves Groq/Gemini/NVIDIA/OpenRouter configuradas e testadas |
| Doctor | 8011 | Webhook-only (já estava certo desde o início) |
| Doc Reader | 8012 | **Upgradado pra RAG real** (ChromaDB + embeddings, antes só guardava em memória) |
| Orchestrator | 8013 | **Novo hoje** — decide local (Ollama OP2) vs. nuvem conforme carga real |
| Auditor | 8014 | **Novo hoje** — testado de verdade (derrubei o Doctor de propósito, 3 IAs votaram 3/3, reiniciou sozinho). Agendado diário 3h15 |
| MCP | 8015 | **Novo hoje** — expõe Router/DocReader/Orchestrator como ferramentas pro OpenCode |

Paridade com o relatório de build do Nina (13/08), **exceto WhatsApp/OpenWA** (combinado não fazer).

## ✅ OpenCode nos 4 nós

Nativo em GERENTE/COORD. Via Docker (`opencode-local` image + wrapper) em OP1/OP2 — binário nativo trava com SIGILL nesses Intel sem AVX2. Registrado com o MCP Agent nos 4 (`opencode mcp add ted --url http://op1-ted.tail2a272d.ts.net:8015/mcp`), testado de ponta a ponta.

## ✅ Ollama CLI nos 4 nós

Instalado em COORD e OP1 (GERENTE e OP2 já tinham). `OLLAMA_HOST=http://op2-ted.tail2a272d.ts.net:11434` configurado em todos, testado (`ollama list` funciona nos 4, mostra os modelos reais do OP2).

## ✅ GitHub

- Repo: **https://github.com/joaopaulomadureira-dot/ted-cluster** (documentação + código dos 6 agentes)
- Token classic PAT ativo, `gh auth setup-git` configurado
- **Hook automático**: qualquer Edit/Write dentro de `~/Ted` faz commit+push sozinho (`~/.claude/settings.json`, PostToolUse), testado e confirmado funcionando
- Repo antigo `ted10-policy` — JPM ia deletar manualmente. Token fine-grained antigo também precisa ser revogado manualmente (github.com/settings/tokens) — sem API pra isso

## ⚠️ Pendências reais pra próxima sessão

1. **NVIDIA_API_KEY** — trocada por uma nova, já testada e funcionando (modelo certo: `nvidia/nemotron-3.5-lightning-30b-a3b`, precisa `stream:true`)
2. Revogar manualmente o token GitHub antigo (fine-grained) e deletar o repo `ted10-policy`
3. Cascata NVIDIA ficou automática (dentro do `default`), por pedido explícito do JPM — diferente do Nina que tirou ela pra manual
4. n8n só tem 2 workflows básicos — expandir conforme necessidade real
5. Modelos Ollama do OP2 ainda usam nomes/IP em alguns lugares (Uptime Kuma, `.zshrc` do GERENTE) — funciona igual, só não é hostname, baixa prioridade

## 🧠 Memórias e documentação

- `TED_INFRA_CHAVES.md` (iCloud, pasta "Api Ted") — fonte única de todas as chaves/senhas/tokens, atualizada em tempo real a sessão toda
- `ANALISE-NINA-2026-08-13-VS-TED.md` (este repo) — comparativo completo Nina x TED que motivou o trabalho de hoje
- Este arquivo + tudo em `~/Ted` sobe pro GitHub automaticamente a partir de agora
