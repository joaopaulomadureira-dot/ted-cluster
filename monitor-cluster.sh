#!/bin/bash
# Real-time cluster monitoring

clear
echo "📡 TED CLUSTER REAL-TIME MONITOR"
echo "Pressione Ctrl+C para sair"
echo ""

while true; do
  clear
  echo "📡 TED CLUSTER REAL-TIME MONITOR"
  echo "Atualizado: $(date '+%H:%M:%S')"
  echo ""
  
  echo "🔌 Conectividade:"
  ping -c 1 -W 1 100.77.72.87 > /dev/null 2>&1 && echo "  GERENTE (100.77.72.87):  ✅" || echo "  GERENTE (100.77.72.87):  ❌"
  ping -c 1 -W 1 100.98.186.17 > /dev/null 2>&1 && echo "  COORD (100.98.186.17):   ✅" || echo "  COORD (100.98.186.17):   ❌"
  ping -c 1 -W 1 100.112.109.38 > /dev/null 2>&1 && echo "  OP1 (100.112.109.38):    ✅" || echo "  OP1 (100.112.109.38):    ❌"
  ping -c 1 -W 1 100.122.103.89 > /dev/null 2>&1 && echo "  OP2 (100.122.103.89):    ✅" || echo "  OP2 (100.122.103.89):    ❌"
  
  echo ""
  echo "🖥️  Local Tailscale:"
  pgrep -f "Tailscale" > /dev/null 2>&1 && echo "  App:        ✅" || echo "  App:        ❌"
  launchctl list | grep -q "io.tailscale.ted" && echo "  Auto-start: ✅" || echo "  Auto-start: ❌"
  launchctl list | grep -q "io.tailscale.monitor" && echo "  Monitor:    ✅" || echo "  Monitor:    ❌"
  
  echo ""
  echo "📝 Logs recentes:"
  echo "  Last health check:"
  tail -1 /tmp/tailscale-monitor.log 2>/dev/null | sed 's/^/    /'
  
  echo ""
  echo "🔄 Próxima verificação em 5s... (Ctrl+C para sair)"
  sleep 5
done
