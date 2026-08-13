#!/bin/bash
# Fix Tailscale crashes — Versão robusta com retry e logging melhorado
# Roda em TODOS os nós

set -e

echo "🔧 Fixing Tailscale stability issues..."
echo ""

# 1. Criar plist melhorado com retry logic
cat > ~/.launchagents/io.tailscale.ted.plist << 'PLIST'
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
# Robust Tailscale monitoring with retry logic
log_file="/tmp/tailscale-ted.log"
pidfile="/tmp/tailscale-ted.pid"
max_retries=3
retry_delay=10

log_msg() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$log_file"
}

start_tailscale() {
  if ! pgrep -f "Tailscale" > /dev/null; then
    log_msg "Starting Tailscale..."
    open -a Tailscale 2>&1 || log_msg "ERROR: Failed to start Tailscale"
    sleep 3
  fi
}

# Initial start
start_tailscale

# Monitoring loop with retry
retry_count=0
while true; do
  if pgrep -f "Tailscale" > /dev/null 2>&1; then
    # Process is running - reset retry counter
    retry_count=0
    sleep 30
  else
    # Process crashed
    retry_count=$((retry_count + 1))
    log_msg "Tailscale crashed (attempt $retry_count/$max_retries)"

    if [ $retry_count -le $max_retries ]; then
      sleep $retry_delay
      start_tailscale
    else
      log_msg "Max retries reached, waiting 60s before reset"
      sleep 60
      retry_count=0
      start_tailscale
    fi
  fi
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

	<key>LaunchOnlyOnce</key>
	<false/>

	<key>StartInterval</key>
	<integer>60</integer>

	<key>TimeOut</key>
	<integer>300</integer>
</dict>
</plist>

echo "✅ Plist melhorado criado"

# 2. Descarregar versão antiga
launchctl unload ~/.launchagents/io.tailscale.ted.plist 2>/dev/null || true
sleep 1

# 3. Carregar nova versão
launchctl load ~/.launchagents/io.tailscale.ted.plist

# 4. Verificar status
sleep 2
echo "✅ LaunchAgent carregado:"
launchctl list | grep tailscale

echo ""
echo "✅ Tailscale agora tem:"
echo "   • Retry logic (até 3 tentativas)"
echo "   • Logging melhorado"
echo "   • Delay entre retries (10s)"
echo "   • Monitoramento contínuo"
echo ""
echo "📝 Logs em: /tmp/tailscale-ted.log"
