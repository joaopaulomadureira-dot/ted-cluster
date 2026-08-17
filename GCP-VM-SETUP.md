# Google Cloud VM — Setup do 5º nó (OP3)

**Papel no ecossistema Ted**: nó estável 24h na tailnet + fallback de nuvem no Router Agent.
**Motivação**: OP1 e OP2 são Mac mini Intel 2011-2014 domésticos, com instabilidade documentada sob carga
(SESSAO-2026-08-14-RESUMO.md — DNS intermitente, Colima travando). Uma VM no Google Cloud dá um nó com
uptime de datacenter, IP estável, sem depender de energia/rede residencial.

Diferente dos outros 4 nós (hardware físico já existente), **este nó não existe ainda** — este documento
é o guia de criação do zero.

---

## 🎯 Decisões de dimensionamento

| Item | Escolha | Motivo |
|---|---|---|
| Região | `southamerica-east1` (São Paulo) | Menor latência a partir do Brasil — os outros nós giram em 5-45ms entre si; uma região dos EUA adicionaria 150-250ms |
| Zona | `southamerica-east1-a` | Zona padrão da região |
| Máquina | `e2-medium` (2 vCPU, 4GB RAM) | Mínimo viável pra rodar Ollama com um modelo pequeno (2-3B) + Tailscale + SO, sem trocar constantemente para swap. `e2-small` (2GB) é o piso absoluto se o papel for só relay/bastion, sem Ollama. |
| Disco | 30GB `pd-balanced` | SO + binário Ollama + 1-2 modelos pequenos (~2-4GB cada) |
| SO | Ubuntu 22.04 LTS | Suporte oficial Tailscale + Ollama, mesma família usada em scripts de automação Linux comuns |
| Hostname Tailscale | `op3-ted` | Segue o padrão dos outros nós (`gerente-ted`, `coord-ted`, `op1-ted`, `op2-ted`) |

**Custo estimado** (preços GCP ago/2026, sujeitos a mudança): `e2-medium` em `southamerica-east1` fica em
torno de **US$ 27-30/mês** rodando 24h. `e2-small` cai pra ~US$ 14-16/mês. Não há free tier elegível fora
das regiões dos EUA (`us-west1`, `us-central1`, `us-east1`) — se o custo for bloqueador, a alternativa é
um `e2-micro` free tier em região dos EUA, aceitando ~150-200ms de latência extra (inviável para hospedar
Ollama útil no Router Agent, mas ok como bastion/backup puro).

---

## 📋 Pré-requisitos

1. Conta Google Cloud com billing ativo (cartão cadastrado — GCP não libera Compute Engine sem billing, mesmo no free tier)
2. `gcloud` CLI instalado na sua máquina (GERENTE ou COORD): https://cloud.google.com/sdk/docs/install
3. Chave de auth Tailscale reutilizável (gerar em https://login.tailscale.com/admin/settings/keys — marcar "Reusable" e "Ephemeral: off" pra sobreviver a reboots)

---

## 🚀 Passo 1 — Autenticar e criar o projeto

```bash
gcloud auth login

# Criar projeto dedicado (nomes de projeto GCP são globalmente únicos — ajuste se necessário)
gcloud projects create ted-cluster-op3 --name="Ted Cluster OP3"
gcloud config set project ted-cluster-op3

# Vincular billing (troque BILLING_ACCOUNT_ID pelo seu — liste com: gcloud billing accounts list)
gcloud billing projects link ted-cluster-op3 --billing-account=BILLING_ACCOUNT_ID

# Habilitar a API do Compute Engine
gcloud services enable compute.googleapis.com
```

## 🚀 Passo 2 — Criar a VM

Use o script `setup-gcp-vm.sh` deste repositório (rode na sua máquina, não em nenhum nó do cluster):

```bash
chmod +x setup-gcp-vm.sh
./setup-gcp-vm.sh
```

O script cria a instância com:
- Firewall restrito: só permite SSH (porta 22, via IAP — sem IP exposto na internet) e UDP 41641 (Tailscale direto)
- Nenhuma porta de serviço (Ollama, Docker etc.) exposta publicamente — tudo passa pela tailnet

## 🚀 Passo 3 — Instalar Tailscale na VM

```bash
# Conectar via SSH (IAP tunnel, não precisa de IP público)
gcloud compute ssh op3-ted --zone=southamerica-east1-a --tunnel-through-iap

# Dentro da VM:
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --authkey=SUA_CHAVE_AQUI --hostname=op3-ted
```

Depois de autenticar, copie `setup-tailscale-op3-linux.sh` pra dentro da VM (`scp` ou colar via `nano`) e rode:

```bash
chmod +x setup-tailscale-op3-linux.sh
sudo ./setup-tailscale-op3-linux.sh
```

Isso configura o Tailscale como serviço `systemd` com restart automático — equivalente ao LaunchAgent
`io.tailscale.ted` usado nos 4 nós macOS, mas usando o mecanismo nativo do Linux.

## 🚀 Passo 4 — Confirmar entrada na tailnet

No GERENTE:
```bash
tailscale status | grep op3-ted
```

Anotar o IP Tailscale atribuído (`100.x.x.x`) e preencher `hardware/op3-gcp.md`.

## 🚀 Passo 5 — (Opcional) Instalar Ollama pra servir como fallback do Router Agent

```bash
# Dentro da VM op3-ted:
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma2:2b   # modelo pequeno, cabe em 4GB RAM com folga pro SO
```

No Router Agent (`agentes/router/router_agent.py`, roda hoje no OP2), configurar:
```bash
export OP3_OLLAMA_URL="http://op3-ted.<sua-tailnet>.ts.net:11434"
export OP3_OLLAMA_MODEL="gemma2:2b"
```

O provider `ollama_op3` já foi adicionado ao código do Router Agent (cascatas `local` e `default`) — fica
inativo (falha rápido e cai pro próximo da cascata) até essas duas variáveis serem configuradas.

---

## ✅ Checklist

- [ ] Projeto GCP criado, billing vinculado
- [ ] VM `op3-ted` criada (`e2-medium`, `southamerica-east1-a`)
- [ ] Firewall confirmado: sem portas de serviço públicas
- [ ] Tailscale instalado e persistente (`systemctl status tailscaled`)
- [ ] `op3-ted` aparece em `tailscale status` nos outros nós
- [ ] IP Tailscale anotado em `hardware/op3-gcp.md`
- [ ] `check-tailscale-health.sh` atualizado com o IP real do OP3
- [ ] (Opcional) Ollama instalado + `OP3_OLLAMA_URL`/`OP3_OLLAMA_MODEL` configurados no Router Agent
- [ ] Restart automático do Tailscale testado (reboot real da VM: `gcloud compute instances reset op3-ted --zone=southamerica-east1-a`)

---

## 🚨 Nota de segurança

Esta VM entra na mesma tailnet privada dos outros 4 nós — ou seja, uma vez conectada, ela enxerga (e é
enxergada por) OP1, OP2, COORD e GERENTE como se estivesse na rede local. Diferente dos Macs domésticos,
uma VM cloud é alvo mais provável de scans automatizados se algo for exposto por engano. Por isso:

- **Nunca** abrir portas de serviço (5432, 6379, 11434, 5678 etc.) no firewall GCP — tudo deve passar pelo Tailscale
- SSH só via IAP tunnel (`--tunnel-through-iap`), sem IP público de gerenciamento
- Revisar `gcloud compute firewall-rules list` periodicamente
