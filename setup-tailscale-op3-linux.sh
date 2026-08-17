#!/bin/bash
# Setup Tailscale auto-start persistente para o OP3 (VM Google Cloud, Ubuntu/Debian).
# Equivalente Linux do setup-tailscale-autostart.sh (que é específico de macOS/launchd).
# Rodar DENTRO da VM op3-ted, como root ou via sudo.

set -e

echo "=== Setup Tailscale Auto-Start — OP3 (Linux) ==="
echo "Nó: $(hostname)"

if ! command -v tailscale >/dev/null 2>&1; then
  echo "❌ Tailscale não está instalado. Rode primeiro:"
  echo "   curl -fsSL https://tailscale.com/install.sh | sh"
  exit 1
fi

# 1. O pacote oficial do Tailscale já instala e habilita o serviço systemd (tailscaled)
#    com restart automático. Aqui só confirmamos e reforçamos os flags corretos.
echo "--- Habilitando e iniciando tailscaled via systemd ---"
systemctl enable --now tailscaled

# 2. Garantir restart automático em caso de crash (equivalente ao KeepAlive do LaunchAgent macOS)
mkdir -p /etc/systemd/system/tailscaled.service.d
cat > /etc/systemd/system/tailscaled.service.d/override.conf << 'EOF'
[Service]
Restart=always
RestartSec=5
EOF

systemctl daemon-reload
systemctl restart tailscaled

echo "✅ tailscaled ativo com restart automático (systemd)"

# 3. Habilitar IP forwarding não é necessário aqui (OP3 não é subnet router/exit node),
#    mas deixamos comentado como referência caso o papel mude no futuro:
# echo 'net.ipv4.ip_forward = 1' | tee -a /etc/sysctl.d/99-tailscale.conf
# sysctl -p /etc/sysctl.d/99-tailscale.conf

echo ""
echo "=== Status ==="
systemctl status tailscaled --no-pager -l | head -10
echo ""
tailscale status || echo "⏳ Ainda não autenticado — rode: sudo tailscale up --authkey=... --hostname=op3-ted"

echo ""
echo "✅ Setup completo! tailscaled agora sobrevive a reboot e crash."
echo "📝 Testar reboot real: sudo reboot"
