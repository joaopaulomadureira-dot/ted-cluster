# Sessão 12/08/2026 — Resumo (Fase 2 em andamento)

**Status geral**: Fase 0 ✅ e Fase 1 ✅ completas (docs antigos). Fase 2 (instalação) em andamento forte hoje. Parada no fim do dia por causa de superaquecimento suspeito do OP2 — retomar amanhã.

---

## ✅ O que ficou pronto e funcionando

### COORD (Mac mini M2)
- Xcode CLT, Homebrew, git, python3, node instalados
- Claude Code + OpenCode instalados
- Chave SSH ed25519 gerada e propagada pra OP1 e OP2 (login sem senha confirmado)

### GERENTE (este Mac)
- Homebrew instalado (obs: sudo precisa de `SUDO_ASKPASS` nesse ambiente sandboxado — script em `/private/tmp/.../scratchpad/askpass.sh`, senha 470054)
- OpenCode + Ollama CLI instalados
- `OLLAMA_HOST=http://100.122.103.89:11434` configurado no `~/.zshrc` — chama IAs do OP2 direto daqui
- `~/.claude/settings.json`: `defaultMode: bypassPermissions` aplicado (usuário pediu pra parar prompts de permissão)

### OP1 (limpo, só agentes — conforme decisão do usuário)
- Ollama/llama.cpp/exo REMOVIDOS (OP1 não hospeda IA local, só roda os agentes)
- 3 Agentes rodando via LaunchAgent, portas 8010 (Router), 8011 (Doctor), 8012 (DocReader)
  - Router: cascata local(TED GATE)→Groq→Gemini Gemma — **chaves cloud (GROQ/GEMINI) ainda são placeholder vazio, precisam ser geradas NOVAS pro TED** (nunca reusar as do Nina)
  - Doctor: só webhook (`/ted/doctor/webhook`), sem schedule — evita spam de alerta
  - DocReader: só Markdown/txt por enquanto (PDF pendente, mesma limitação do Nina com Macs antigos)
  - Código fonte: `~/ted/router/`, `~/ted/doctor/`, `~/ted/docreader/` no OP1

### OP2 (SSD externa `/Volumes/Install macOS Sonoma/`)
- Ollama rodando (LaunchAgent `com.ted.ollama`), modelos na SSD externa, acessível remotamente (`0.0.0.0:11434`)
- **3 IAs com apelido, nome já embute o modelo** (padrão pedido pelo usuário):
  - `ted-escrita-local-gemma2` → gemma2:2b — ✅ testada, funciona
  - `ted-cod-local-qwen25coder` → qwen2.5-coder:7b — ⚠️ CAUSOU O TRAVAMENTO (ver abaixo)
  - `ted-livre-local-dolphin3` → dolphin3 (sem guardrail) — não testada ainda (parou antes)
- **TED GATE**: serviço próprio (chave por IA), porta 4003, LaunchAgent `com.ted.gate`, código em `/Volumes/Install macOS Sonoma/ted-gate/ted_gate.py`
  - Resposta inclui campo `modelo_real` (pedido do usuário — sempre saber qual modelo respondeu)
  - Chaves geradas e documentadas em `TED_INFRA_CHAVES.md` (pasta iCloud "Api Ted")
- **docker-compose.yml preparado** (não aplicado ainda) em `/private/tmp/.../scratchpad/docker-compose.yml` — 15 serviços do catálogo (falta Caddy e Restic, ver depois)

---

## ⚠️ Testado e descartado

- **Exo nativo** (biblioteca oficial exo-explore): bloqueado — depende de `exo-rs` (Rust) via `uv` + toolchain Rust, não instala com pip simples. Não insistir sem reavaliar.
- **RPC distribuído (llama.cpp --rpc, OP1+OP2)**: crashava — "Compute error" / "Remote RPC server crashed", causa provável era o backend gráfico (Intel Iris) instável no OP2. Testado com `-d CPU` e `-d BLAS`, ainda crashava.
- **Decisão do usuário**: abandonar Exo/RPC distribuído. Usar **Ollama isolado no OP2** (funciona bem pra modelos até ~3-4B; 7B foi o que travou a máquina).

---

## 🔴 INCIDENTE — OP2 caiu (fim do dia)

- Ao carregar `qwen2.5-coder:7b` (4.7GB) no Ollama, o OP2 ficou 100% sem resposta (SSH e ping falhando, Tailscale mostrando offline)
- **Causa suspeita confirmada pelo usuário**: o Mac está dentro de **uma caixa fechada** (sem ventilação) — provável superaquecimento, não só RAM
- **Sem acesso físico agora** (máquina na casa da mãe do usuário) — não dava pra reiniciar remotamente (sem tomada inteligente)
- **Ação do usuário**: vai tirar o Mac da caixa fechada da próxima vez que for lá, pra melhorar ventilação
- **Ação pendente minha**: quando o OP2 voltar, aplicar `OLLAMA_FLASH_ATTENTION=1` e `OLLAMA_KV_CACHE_TYPE=q8_0` no LaunchAgent do Ollama (reduz uso de RAM do KV cache — recomendação do próprio Homebrew) ANTES de testar o modelo 7B de novo, com mais cautela

---

## 📋 Pendências pra amanhã (retomar aqui)

1. **Confirmar se OP2 voltou** (ping / Tailscale status / SSH)
2. Se voltou: aplicar flags de economia de RAM no Ollama, retestar `ted-cod-local-qwen25coder` com cautela
3. Testar `ted-livre-local-dolphin3` (não chegou a testar)
4. Testar isolamento de chaves (chave errada pro modelo errado → esperar 403)
5. Atualizar `TED_INFRA_CHAVES.md` com status final confirmado das 3 chaves
6. Gerar chaves NOVAS de Groq/Gemini pro TED (nunca reusar do Nina) e preencher no Router Agent (OP1)
7. Aplicar o `docker-compose.yml` preparado no OP2 (15 serviços — Passo 5 da Fase 2 do documento v1.1)
8. Adicionar Redis ao catálogo (rate limiter do Router, decisão já tomada na Fase 1)
9. Configurar Caddy (HTTPS) e Restic (backup) — únicos dois do catálogo ainda não tratados
10. n8n: importar workflows quando o serviço estiver de pé
11. Doc Reader: ingerir o documento v1.1 (P7 — "cluster conhece a si mesmo")

---

## 🧠 Memórias salvas nessa sessão (ver `~/.claude/projects/-Users-tedger01/memory/`)
- `project-ted-v1.1-base-document` — v1.1 é a base fixa de tudo
- `feedback-nina-is-reference-not-decision` — Nina é conhecimento, não decisão pronta
- `feedback-jpm-decides-not-claude` — eu apresento dados, JPM decide arquitetura (P6)
- `feedback-no-execution-authorization-questions` — não pedir autorização pra executar, só decisões de arquitetura
- `project-op2-no-physical-access` — OP2 sem acesso físico fácil, cuidado com cargas pesadas, causa provável = caixa fechada sem ventilação
