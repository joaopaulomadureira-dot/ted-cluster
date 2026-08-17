#!/bin/bash
# Cria a VM do Google Cloud que vira o 5º nó do cluster Ted (OP3).
# Rodar na sua máquina local (GERENTE/COORD) com `gcloud` autenticado — NÃO dentro de nenhum nó do cluster.
# Ver GCP-VM-SETUP.md para o passo a passo completo.

set -e

# --- Parâmetros (ajuste conforme necessário) ---
PROJECT_ID="${TED_GCP_PROJECT:-ted-cluster-op3}"
ZONE="${TED_GCP_ZONE:-southamerica-east1-a}"
MACHINE_TYPE="${TED_GCP_MACHINE_TYPE:-e2-medium}"
DISK_SIZE="${TED_GCP_DISK_SIZE:-30GB}"
INSTANCE_NAME="${TED_GCP_INSTANCE_NAME:-op3-ted}"
IMAGE_FAMILY="ubuntu-2204-lts"
IMAGE_PROJECT="ubuntu-os-cloud"

echo "=== Setup GCP VM — Ted OP3 ==="
echo "Projeto: $PROJECT_ID"
echo "Zona: $ZONE"
echo "Máquina: $MACHINE_TYPE"
echo "Instância: $INSTANCE_NAME"
echo ""

gcloud config set project "$PROJECT_ID"

# 1. Firewall: nada de portas de serviço públicas. Só SSH via IAP e Tailscale direto (UDP 41641).
echo "--- Configurando firewall ---"
gcloud compute firewall-rules create ted-allow-iap-ssh \
  --network=default \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=35.235.240.0/20 \
  --description="SSH via IAP tunnel apenas (sem IP publico de gerenciamento)" \
  2>/dev/null || echo "(regra ted-allow-iap-ssh já existe, pulando)"

gcloud compute firewall-rules create ted-allow-tailscale \
  --network=default \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=udp:41641 \
  --source-ranges=0.0.0.0/0 \
  --description="Tailscale WireGuard direto (NAT traversal)" \
  2>/dev/null || echo "(regra ted-allow-tailscale já existe, pulando)"

# 2. Criar a instância
echo ""
echo "--- Criando instância $INSTANCE_NAME ---"
gcloud compute instances create "$INSTANCE_NAME" \
  --zone="$ZONE" \
  --machine-type="$MACHINE_TYPE" \
  --image-family="$IMAGE_FAMILY" \
  --image-project="$IMAGE_PROJECT" \
  --boot-disk-size="$DISK_SIZE" \
  --boot-disk-type=pd-balanced \
  --no-address \
  --tags=ted-op3

echo ""
echo "✅ VM criada sem IP público (--no-address). Acesso só via IAP tunnel ou Tailscale."
echo ""
echo "=== Próximos passos ==="
echo "1. Conectar via IAP:"
echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --tunnel-through-iap"
echo "2. Instalar Tailscale (ver GCP-VM-SETUP.md, Passo 3)"
echo "3. Rodar setup-tailscale-op3-linux.sh dentro da VM"
