# Tailscale Setup — TED Cluster

## Status Atual (2026-08-12)

✅ **GERENTE (MacBook M4)**
- Tailscale rodando
- Auto-start ativado (LaunchAgent)
- Monitor ativo (verifica a cada 5 min)

✅ **COORD (Mac mini M2)**
- Tailscale rodando
- **Falta:** Auto-start + Monitor

✅ **OP1 (Mac mini Intel 2011)**
- Tailscale rodando
- **Falta:** Auto-start + Monitor

❌ **OP2 (Mac mini Intel — outra rede)**
- Offline (aguardando reinício)
- **Falta:** Auto-start + Monitor

---

## 🚀 Setup em cada nó (COORD, OP1, OP2)

### Passo 1: Copiar scripts
Você precisa executar isto em cada nó (COORD, OP1, OP2):

```bash
# Copiar script de setup
scp ~/Ted/setup-tailscale-autostart.sh tedopX@<IP>:~/
```

Ou manualmente:
```bash
# EM CADA NÓ:
mkdir -p ~/Ted
cd ~/Ted

# Copiar o conteúdo de setup-tailscale-autostart.sh e salvar
nano setup-tailscale-autostart.sh
# (Colar o conteúdo, Ctrl+X, Y, Enter)

chmod +x setup-tailscale-autostart.sh
```

### Passo 2: Executar setup em cada nó

```bash
# No COORD:
ssh tedcoord02@100.98.186.17
~/setup-tailscale-autostart.sh

# No OP1:
ssh tedop1@100.112.109.38
~/setup-tailscale-autostart.sh

# No OP2 (quando estiver online):
ssh tedop2@100.122.103.89
~/setup-tailscale-autostart.sh
```

---

## 📊 Verificar Saúde do Cluster

Rodar no GERENTE (aqui):

```bash
/Users/tedger01/Ted/check-tailscale-health.sh
```

**Esperado quando todos estiverem online:**
```
GERENTE (100.77.72.87): ✅ ONLINE
COORD (100.98.186.17): ✅ ONLINE
OP1 (100.112.109.38): ✅ ONLINE
OP2 (100.122.103.89): ✅ ONLINE
```

---

## 🔧 O que cada LaunchAgent faz

### `io.tailscale.ted`
- **Função:** Inicia Tailscale app automaticamente no boot
- **Comportamento:** Se travar, reinicia a cada 30 segundos
- **Logs:** `/tmp/tailscale-ted.log`
- **Rodando em:** GERENTE (já feito)

### `io.tailscale.monitor` 
- **Função:** Monitora saúde do cluster a cada 5 minutos
- **Comportamento:** Registra status de conectividade
- **Logs:** `/tmp/tailscale-monitor.log`
- **Rodando em:** GERENTE (já feito)

---

## 🚨 Troubleshooting

### "Tailscale está offline?"
```bash
# Verificar se app está rodando
pgrep -a Tailscale

# Ver logs
tail -20 /tmp/tailscale-ted.log
tail -20 /tmp/tailscale-monitor.log

# Reiniciar manualmente
pkill -f Tailscale
open -a Tailscale
```

### "LaunchAgent não está carregado?"
```bash
# Descarregar e recarregar
launchctl unload ~/.launchagents/io.tailscale.ted.plist
launchctl load ~/.launchagents/io.tailscale.ted.plist

# Verificar
launchctl list | grep tailscale
```

### "Ping para um nó falha?"
```bash
# Testar conectividade individual
ping -c 3 100.98.186.17  # COORD
ping -c 3 100.112.109.38 # OP1
ping -c 3 100.122.103.89 # OP2

# Se falhar, verificar:
# 1. Node está ligado?
# 2. Tailscale app está rodando no nó?
# 3. Node está na mesma tailnet?
```

---

## 📝 Checklist Final

- [ ] GERENTE: Tailscale auto-start ✅
- [ ] GERENTE: Monitor ativo ✅
- [ ] COORD: Rodar `setup-tailscale-autostart.sh`
- [ ] OP1: Rodar `setup-tailscale-autostart.sh`
- [ ] OP2: Reiniciar → Rodar `setup-tailscale-autostart.sh`
- [ ] Todos os 4 nós respondendo ping
- [ ] Health check mostrando 4/4 online

---

## 🎯 Próxima Etapa

Quando **Tailscale 100% operacional em todos os 4 nós**, avise para rodar **Fase 1** (decisões finais).

**Comandos para acompanhar:**
```bash
# Ver status em tempo real
tail -f /tmp/tailscale-monitor.log

# Verificar saúde
/Users/tedger01/Ted/check-tailscale-health.sh
```
