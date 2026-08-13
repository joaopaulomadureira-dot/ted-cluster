#!/bin/bash
# Check Tailscale health across TED cluster

echo "=== TED Cluster Tailscale Health Check ==="
echo "Timestamp: $(date)"
echo ""

echo "🔌 Testando conectividade entre nós:"
echo ""

# Testar cada nó individualmente
echo -n "GERENTE (100.77.72.87): "
ping -c 1 -W 2 100.77.72.87 > /dev/null 2>&1 && echo "✅ ONLINE" || echo "❌ OFFLINE"

echo -n "COORD (100.98.186.17): "
ping -c 1 -W 2 100.98.186.17 > /dev/null 2>&1 && echo "✅ ONLINE" || echo "❌ OFFLINE"

echo -n "OP1 (100.112.109.38): "
ping -c 1 -W 2 100.112.109.38 > /dev/null 2>&1 && echo "✅ ONLINE" || echo "❌ OFFLINE"

echo -n "OP2 (100.122.103.89): "
ping -c 1 -W 2 100.122.103.89 > /dev/null 2>&1 && echo "✅ ONLINE" || echo "❌ OFFLINE"

echo ""
echo "📊 Status local Tailscale:"

# Verificar se app está rodando
if pgrep -f "Tailscale" > /dev/null; then
  echo "✅ Tailscale app rodando"
else
  echo "❌ Tailscale app NÃO está rodando!"
fi

# Verificar LaunchAgent
if launchctl list | grep -q "tailscale"; then
  echo "✅ LaunchAgent carregado"
else
  echo "⚠️  LaunchAgent não está carregado"
fi

echo ""
echo "📝 Logs recentes:"
tail -3 /tmp/tailscale-ted.log 2>/dev/null || echo "(sem logs ainda)"

echo ""
echo "=== Próximos Passos ==="
echo "1. Quando OP2 reiniciar: será detectado aqui"
echo "2. Rodar setup-tailscale-autostart.sh em COORD, OP1, OP2"
echo "3. Executar este script novamente para confirmar 4/4 nós online"
