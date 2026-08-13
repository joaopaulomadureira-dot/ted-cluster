# Ecossistema TED — Fase 0 COMPLETO ✅

**Data:** 2026-08-12  
**Status:** 3/4 nós com dados, 1 nó pendente (OP2 outra rede)

---

## 📊 Dados Capturados

### GERENTE (MacBook Air M4)
- **Chip:** Apple M4 (10 cores: 4P + 6E)
- **RAM:** 16 GB
- **Disco:** 228 GB (12 GB usado, 184 GB livre)
- **Hostname Tailscale:** macbook-air-de-ted (100.77.72.87)
- **Latência LAN:** 5-7ms
- **Status:** ✅ Pronto para rodar Claude Code + OpenCode

### COORD (Mac mini M2)
- **Chip:** Apple M2 (8 cores: 4P + 4E)
- **RAM:** 8 GB
- **Disco:** 228 GB (12 GB usado, 180 GB livre)
- **Hostname Tailscale:** mac-mini-de-ted (100.98.186.17)
- **Latência LAN:** ~5-7ms
- **Status:** ✅ Pronto para Claude Code + OpenCode + Git + Python + Node

### OP1 (Mac mini Intel Macmini7,1 — 2011)
- **Chip:** Intel Core i5 dual-core
- **RAM:** 8 GB
- **Disco:** 234 GB (12 GB usado, 176 GB livre)
- **Hostname Tailscale:** mac-mini-de-ted-2-1 (100.112.109.38)
- **Latência LAN:** 5-45ms (variável)
- **Benchmark Disco:** Escrita 744 MB/s | Leitura 638 MB/s
- **⚠️ Crítico:** CPU 2011 **muito antiga** — AVX2 incerto, OpenCode/Tailscale CLI podem não funcionar
- **Status:** ⚠️ Operacional mas com limitações

### OP2 (Mac mini Intel — Outra rede)
- **Hostname Tailscale:** mac-mini-de-ted-2 (100.122.103.89)
- **Status:** ⏳ Pendente dados (reiniciando Tailscale agora)
- **Localização:** Distante (WAN, não LAN)
- **Impacto:** Exo será não-viável, Ollama independente

---

## 🎯 Decisões Fase 1 (Prontas)

### 1. **Exo — NÃO USAR**
- ❌ OP2 em outra rede (latência WAN alta)
- ❌ Latência OP1 ↔ COORD variável (5-45ms)
- ✅ **Solução:** Cada operador roda Ollama independentemente
- ✅ **Router Agent** faz cascata de fallback entre os 3

### 2. **Caminhos Quentes (onde ficam modelos + Docker volumes)**
- **GERENTE:** Disco interno (228 GB disponível) ✅
- **COORD:** Disco interno (228 GB disponível) ✅
- **OP1:** Disco interno (234 GB, benchmark 744 MB/s escrita) ✅
- **OP2:** TBD (quando capturar dados)

### 3. **OpenCore Legacy Patcher**
- **GERENTE (M4):** ❌ Não precisa (Apple Silicon)
- **COORD (M2):** ❌ Não precisa (Apple Silicon)
- **OP1 (Intel 2011):** ❌ Não precisa (suporta nativamente, mas...)
- **Problema:** AVX2 incerto no OP1 → pode bloquear OpenCode/Tailscale CLI

### 4. **Instalação de OpenCode + Tailscale CLI**
- **GERENTE:** ✅ OK (Apple Silicon)
- **COORD:** ✅ OK (Apple Silicon)
- **OP1:** ⚠️ **VERIFICAR AVX2 primeiro** (CPU 2011 pode não ter)
- **OP2:** TBD

---

## 🔧 Próximos Passos

### Fase 1 (Agora)
- Gerar SSH keys para todos os nós
- Documentar decisões finais
- Preparar checklist de instalação

### Fase 2 (Instalação)
1. Instalar Tailscale + MagicDNS em todos (já feito, só confirmar)
2. Instalar Docker (OrbStack ou Colima)
3. Instalar Docker Compose
4. Inicializar stack no OP2 (15 serviços)
5. Testar conectividade entre nós

---

## 📝 Arquivos Atualizados

```
~/Ted/hardware/
├── gerente.md ✅
├── coord.md ✅
├── op1.md ✅
└── op2.md (⏳ pendente)
```

**Status Geral:** Fase 0 **~90% completo** — aguardando reinício OP2 e confirmação AVX2 do OP1.
