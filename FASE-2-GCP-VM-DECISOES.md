# Fase 2 — Google Cloud VM (OP3) — Decisões

**Data**: 2026-08-17
**Status**: 📝 Planejado — VM ainda não criada (aguardando JPM rodar `GCP-VM-SETUP.md`)

---

## 🎯 Contexto

Pedido: vincular o Google Cloud, principalmente uma máquina virtual, ao ecossistema Ted.

O cluster hoje tem 4 nós físicos domésticos (GERENTE, COORD, OP1, OP2) com instabilidade documentada em
OP1/OP2 sob carga (DNS intermitente, Colima travando — `SESSAO-2026-08-14-RESUMO.md`) e dependência de
energia/rede residencial (`DISASTER-RECOVERY.md`).

## 🎯 DECISÃO 1: Papel da VM no ecossistema

**Escolhido por JPM**: nó estável 24h (5º nó Tailscale) + fallback de nuvem no Router Agent.

Descartados nesta rodada (podem ser revisitados depois):
- **Backup offsite (Restic)** — resolveria o risco já documentado em `FASE-1-DECISOES.md` (Decisão 6: hoje
  o backup Restic vive no próprio OP2, mesmo nó dos dados). Não escolhido agora, mas continua sendo o
  próximo candidato natural se surgir apetite por DR mais robusto.
- **Bastion/ponto de entrada público** — resolveria a exposição de webhooks (n8n, Telegram Gateway) sem
  depender de Tailscale Funnel. Não escolhido; sem IP público na VM por ora (ver Decisão 3).

## 🎯 DECISÃO 2: Nome e posição no cluster

**OP3** — segue o padrão de nomenclatura dos operadores existentes (OP1, OP2), diferenciando-se por ser
infraestrutura cloud, não hardware doméstico. Hostname Tailscale: `op3-ted`.

## 🎯 DECISÃO 3: Dimensionamento e região

| Item | Escolha |
|---|---|
| Região | `southamerica-east1` (São Paulo) — menor latência a partir do Brasil |
| Máquina | `e2-medium` (2 vCPU, 4GB RAM) — mínimo pra rodar Ollama + modelo pequeno sem swap constante |
| IP público | Nenhum (`--no-address`) — acesso só via IAP tunnel (SSH) e Tailscale (tudo mais) |
| Custo estimado | ~US$ 27-30/mês, sem free tier elegível (free tier GCP é restrito a `us-*`) |

Alternativa mais barata considerada e descartada por ora: `e2-micro` free tier em região dos EUA
(~150-200ms de latência extra) — inviável pro papel de fallback de inferência (Router Agent precisa de
resposta rápida), ficaria só como bastion puro, papel que não foi escolhido nesta rodada.

## 🎯 DECISÃO 4: Integração no Router Agent

Novo provider `ollama_op3` em `agentes/router/router_agent.py`, chamando Ollama diretamente via Tailscale
(não passa pelo TED GATE do OP2, que é específico dos modelos hospedados fisicamente em OP1/OP2).

Adicionado às cascatas:
- `local`: `["ollama_local", "ollama_op3", "groq", "gemini_gemma"]` — OP3 como segunda tentativa local,
  antes de cair pra nuvem paga/com quota
- `default`: `["gemini_gemma", "groq", "nvidia", "ollama_local", "ollama_op3"]` — último degrau antes de
  falhar tudo

**Mudança é aditiva e inofensiva até a VM existir**: sem `OP3_OLLAMA_URL` configurada, `_ollama_op3` levanta
`RuntimeError` imediatamente e a cascata cai pro próximo provedor, exatamente como qualquer outro provider
sem chave configurada (mesmo padrão já usado pra Groq/Gemini/NVIDIA/OpenRouter).

## 🎯 DECISÃO 5: Segurança de rede

VM sem IP público de gerenciamento — SSH só via IAP tunnel (`gcloud compute ssh --tunnel-through-iap`).
Firewall libera apenas porta 22 (via ranges do IAP, `35.235.240.0/20`) e UDP 41641 (Tailscale WireGuard
direto). Nenhuma porta de serviço (Ollama 11434, etc.) exposta na internet — tudo passa pela tailnet
privada, mesmo modelo de confiança já usado pelos outros 4 nós.

---

## ✅ Checklist Fase 2 — GCP VM

- [ ] JPM roda `GCP-VM-SETUP.md` (projeto GCP, billing, `setup-gcp-vm.sh`)
- [ ] VM `op3-ted` criada e na tailnet (`setup-tailscale-op3-linux.sh`)
- [ ] `hardware/op3-gcp.md` preenchido com specs reais + IP Tailscale
- [ ] `check-tailscale-health.sh` testado com `TED_OP3_IP` exportado
- [ ] (Opcional) Ollama instalado na VM, `OP3_OLLAMA_URL`/`OP3_OLLAMA_MODEL` configurados no ambiente do
      Router Agent (OP2), reiniciar o Router Agent pra pegar a mudança
- [ ] Reboot real da VM testado (`gcloud compute instances reset op3-ted --zone=southamerica-east1-a`),
      confirmar que Tailscale volta sozinho

---

## 📝 Próximo passo

Nenhuma ação futura decidida automaticamente — quando JPM criar a VM e confirmar o checklist acima, revisar
com ele se o papel de backup offsite (Restic) ou bastion público fazem sentido como Fase 3, ou se o escopo
atual (nó estável + fallback de router) é suficiente.
