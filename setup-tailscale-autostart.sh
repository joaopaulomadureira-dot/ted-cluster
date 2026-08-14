#!/bin/bash
# Setup Tailscale auto-start persistente para todos os nós TED
# Rodar este script em cada nó (COORD, OP1, OP2)

set -e

echo "=== Setup Tailscale Auto-Start ==="
echo "Nó: $(hostname)"

# 1. Criar diretório correto (~/Library/LaunchAgents — launchd NÃO le ~/.launchagents no boot)
mkdir -p ~/Library/LaunchAgents

# 2. Criar LaunchAgent plist para Tailscale
cat > ~/Library/LaunchAgents/io.tailscale.ted.plist << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>io.tailscale.ted</string>

	<key>ProgramArguments</key>
	<array>
		<string>/bin/bash</string>
		<string>-c</string>
		<string>
# Auto-start Tailscale app
if ! pgrep -f "Tailscale" > /dev/null; then
  echo "[$(date)] Starting Tailscale..." >> /tmp/tailscale-ted.log
  open -a Tailscale
  sleep 5
fi

# Monitor e restart se travar
while true; do
  if ! pgrep -f "Tailscale" > /dev/null; then
    echo "[$(date)] Tailscale crashed, restarting..." >> /tmp/tailscale-ted.log
    open -a Tailscale
    sleep 5
  fi
  sleep 30
done
		</string>
	</array>

	<key>RunAtLoad</key>
	<true/>

	<key>KeepAlive</key>
	<true/>

	<key>StandardOutPath</key>
	<string>/tmp/tailscale-ted.log</string>

	<key>StandardErrorPath</key>
	<string>/tmp/tailscale-ted.err</string>

	<key>SessionCreate</key>
	<true/>
</dict>
</plist>
PLIST_EOF

echo "✅ LaunchAgent criado: ~/.launchagents/io.tailscale.ted.plist"

# 3. Descarregar versão antiga se existir
launchctl unload ~/.launchagents/io.tailscale.ted.plist 2>/dev/null || true
sleep 1

# 4. Carregar novo
launchctl load ~/.launchagents/io.tailscale.ted.plist

echo "✅ LaunchAgent carregado"

# 5. Verificar status
sleep 2
echo ""
echo "=== Status ==="
launchctl list | grep tailscale
echo ""
pgrep -a Tailscale || echo "⏳ Tailscale iniciando..."

echo ""
echo "=== Logs ==="
tail -5 /tmp/tailscale-ted.log 2>/dev/null || echo "Logs ainda não existem"

echo ""
echo "✅ Setup completo! Tailscale agora inicia automaticamente."
echo "📝 Logs em: /tmp/tailscale-ted.log"
