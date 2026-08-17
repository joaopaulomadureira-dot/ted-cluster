# Hardware real — OP3 (Google Cloud VM)

❓ **PENDENTE DE CRIAÇÃO** — este nó ainda não existe. Ver `GCP-VM-SETUP.md` para o passo a passo.
Preencher esta seção assim que a VM subir (mesmo padrão dos outros nós em `hardware/*.md`).

## Especificação planejada

- Provedor: Google Cloud (Compute Engine)
- Máquina: `e2-medium` (2 vCPU, 4GB RAM)
- Região/zona: `southamerica-east1-a` (São Paulo)
- Disco: 30GB `pd-balanced`
- SO: Ubuntu 22.04 LTS
- IP público: nenhum (`--no-address` — acesso só via IAP tunnel ou Tailscale)
- Hostname Tailscale: `op3-ted`
- IP Tailscale: ❓ A PREENCHER (`tailscale status | grep op3-ted`)

## Papel no cluster

- **5º nó, sempre online** — datacenter uptime, sem depender de energia/rede residencial (diferente de
  OP1/OP2, hardware doméstico com instabilidade documentada sob carga — ver `SESSAO-2026-08-14-RESUMO.md`)
- **Fallback de nuvem no Router Agent** — roda Ollama com um modelo pequeno (`gemma2:2b` sugerido),
  exposto via `OP3_OLLAMA_URL` em `agentes/router/router_agent.py`, novo provider `ollama_op3`
- Não hospeda dados críticos (Postgres, Vaultwarden) nem é destino de backup nesta fase — papel puramente
  de disponibilidade + capacidade de inferência

## Notas

- Diferente dos outros nós, é infraestrutura efêmera/recriável por definição (IaC via `setup-gcp-vm.sh`) —
  perda desta VM não é perda de dados, só de disponibilidade temporária
- Custo recorrente (~US$ 27-30/mês em `e2-medium`, `southamerica-east1`) — não é free tier

## Fase 0 status

- ⏳ **Pendente** — aguardando criação da VM (ver checklist em `GCP-VM-SETUP.md`)
