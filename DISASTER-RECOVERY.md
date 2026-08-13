# Disaster Recovery — Resiliência a Apagão

## ❓ Pergunta: "Se cair a energia, eles voltam funcionando?"

### ✅ Resposta: **SIM, mas precisa de auto-boot habilitado**

---

## 🔌 Sequência Após Apagão

```
┌─────────────────────────────────────┐
│ 1. Apagão / Queda de energia        │
└─────────────────────────────────────┘
                    ⬇
┌─────────────────────────────────────┐
│ 2. Energia volta                    │
└─────────────────────────────────────┘
                    ⬇
┌─────────────────────────────────────┐
│ 3. Macs ligam automaticamente       │
│    (Se auto-boot estiver ON)        │
└─────────────────────────────────────┘
                    ⬇
┌─────────────────────────────────────┐
│ 4. macOS carrega (30-60s)           │
└─────────────────────────────────────┘
                    ⬇
┌─────────────────────────────────────┐
│ 5. LaunchAgent inicia Tailscale     │
│    (RunAtLoad=true ✅)              │
└─────────────────────────────────────┘
                    ⬇
┌─────────────────────────────────────┐
│ 6. Tailscale conecta à rede (10-20s)│
└─────────────────────────────────────┘
                    ⬇
┌─────────────────────────────────────┐
│ ✅ Cluster online novamente         │
│    (Total: 2-3 minutos)             │
└─────────────────────────────────────┘
```

---

## ⚙️ O que já está configurado

✅ **LaunchAgent RunAtLoad=true**
- Tailscale vai iniciar automaticamente no boot
- Sem necessidade de login manual

✅ **Tailscale auto-reconnect**
- Reconecta automaticamente após boot
- Sem intervenção manual

✅ **LaunchAgent KeepAlive=true**
- Se Tailscale travar, reinicia automaticamente
- Funciona mesmo após apagão

---

## 🚨 O que PRECISA fazer manualmente

### CADA NÓ precisa ter auto-boot habilitado:

#### **GERENTE (MacBook M4):**
1. Apple menu → Preferências do Sistema
2. Energia → Energies savers
3. ☑️ "Reiniciar automaticamente após queda de energia"

#### **COORD (Mac mini M2):**
1. Apple menu → Preferências do Sistema
2. Energia → Energy Saver
3. ☑️ "Restart automatically after power failure"

#### **OP1 (Mac mini Intel 2011):**
1. Apple menu → Preferências do Sistema → Economia de Energia
2. ☑️ "Reiniciar automaticamente após queda de energia"

#### **OP2 (Mac mini Intel 2011 — outra localização):**
1. Pedindo pra sua mãe fazer o mesmo em OP2

**Instruções em PT-BR / EN-US:**
- Sistema menu → Energy Preferences
- Look for: "Automatically restart after power failure"
- ✅ Enable it

---

## 💡 Alternativa: UPS (Uninterruptible Power Supply)

Se houver apagões frequentes, considerar:

```
┌─────────────────────────────────────┐
│ UPS com Battery Backup              │
├─────────────────────────────────────┤
│ + Protege contra apagões curtos    │
│ + Smooth graceful shutdown         │
│ + Protege dados do banco de dados  │
│ + Mantém rede ligada              │
└─────────────────────────────────────┘
```

**Setup com UPS:**
- UPS com 15-30 min de bateria
- Conectar: GERENTE, COORD, OP1, OP2, roteador Tailscale
- Configurar shutdown automático após X minutos

---

## ✅ Checklist Final

- [ ] GERENTE: Auto-boot habilitado
- [ ] COORD: Auto-boot habilitado
- [ ] OP1: Auto-boot habilitado
- [ ] OP2: Auto-boot habilitado (sua mãe)
- [ ] LaunchAgent configurado (✅ já feito)
- [ ] Tested: Rebootar um nó e confirmar reconexão

---

## 🧪 Teste de Resiliência (Opcional)

Para confirmar que volta funcionando:

```bash
# No nó a testar (ex: OP1):
ssh tedop1@100.112.109.38

# Simular queda (não desliga, só testa Tailscale):
sudo killall Tailscale

# Aguardar 30s e verificar se reinicia
pgrep -a Tailscale

# Resultado esperado:
# ✅ Tailscale foi reiniciado automaticamente pelo LaunchAgent
```

---

## 📊 Resultado Final

Se auto-boot estiver ativado em todos os 4 nós:

```
✅ Cluster é resiliente a apagões
✅ Volta sozinho após queda de energia
✅ Zero intervenção manual necessária
✅ Tailscale auto-reconnect funciona
✅ Dados persistem (Vaultwarden, n8n, etc)
```

**Tempo total de recuperação: 2-3 minutos**

---

## 🆘 Se não voltar após apagão

1. Verificar se auto-boot está habilitado
2. Ligar nó manualmente se precisar
3. LaunchAgent vai iniciar Tailscale automaticamente
4. Cluster volta online

---

**Data:** 2026-08-12  
**Status:** ✅ Pronto para produção (com auto-boot ativado)
