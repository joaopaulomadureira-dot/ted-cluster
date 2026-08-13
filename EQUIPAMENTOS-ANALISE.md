# Análise de Equipamentos — TED vs. Nina

**Data**: 2026-08-12  
**Status**: Fase 0 — Benchmark de disco PENDENTE

---

## 📊 Comparativo: Hardware Real TED vs. Nina (Planejado)

### **GERENTE (sua interface)**

| Aspecto | TED | Nina |
|---------|-----|------|
| Máquina | MacBook Air M4 | MacBook Pro M1 |
| CPU | Apple Silicon M4 | Apple Silicon M1 |
| RAM | 16GB unificada | 16GB unificada |
| SSD | 256GB nativo | 512GB nativo |
| Aceleração MLX | ✅ Sim | ✅ Sim |
| Papel | Decisão + criação projetos | Idem |
| **Status** | ✅ Mais potente que Nina | Baseline |

---

### **COORD (Coordenador técnico)**

| Aspecto | TED | Nina |
|---------|-----|------|
| Máquina | Mac Mini M2 | Mac Mini M1 |
| CPU | Apple Silicon M2 | Apple Silicon M1 |
| RAM | 8GB unificada | 8GB unificada |
| SSD | 256GB nativo | 512GB nativo |
| Papel | Claude Code + OpenCode + deploy | Idem |
| **Status** | ✅ Equivalente (M2 > M1) | Baseline |

---

### **OP1 (Operador 1 — Agentes)**

| Aspecto | TED | Nina (Real) |
|---------|-----|------------|
| Máquina | Mac Mini Intel 2011 | Mac Mini Intel 2011 |
| CPU | Intel Core i5 dual-core | Intel Core i7 quad-core |
| Ano | 2011-2012 | 2011-2012 |
| RAM | 8GB | 16GB |
| SSD Interno | 234GB (176GB livre) | ~480GB |
| SSD Externo | ❓ PRECISA TESTAR | SSD USB2 (lento) |
| Aceleração | ❌ Nenhuma | ❌ Nenhuma |
| **Avaliação** | ⚠️ **Mais fraco** (menos CPU cores, menos RAM) | Operador i7 |
| **Impacto** | Modelos ≤7B apenas | Modelos até 7B |
| **Rate Limite Esperado** | ~1-2 tok/s (local) | ~2-3 tok/s (local) |

**Diferenças críticas OP1**:
- CPU: i5 dual-core vs i7 quad-core (-2 cores)
- RAM: 8GB vs 16GB (-50%)
- Espaço: 176GB livre vs 480GB (-63%)

---

### **OP2 (Operador 2 — Infraestrutura 24h)**

| Aspecto | TED | Nina (Real) |
|---------|-----|------------|
| Máquina | Mac Mini Intel 2011 | Mac Mini Intel 2011 |
| CPU | Intel Core i5 (quad-core spec) | Intel Core i7 quad-core |
| Ano | 2011-2012 | 2011-2012 |
| RAM | 8GB | 16GB |
| SSD Interno | 931GB total (903GB livre) | ~480GB |
| SSD Externo | ❓ PRECISA TESTAR | SSD USB3 Thunderbolt 1TB |
| Hospedagem | Docker 15 serviços | Idem |
| Disponibilidade | 24h/7d (casa da mãe) | 24h/7d (idem) |
| **Avaliação** | ✅ **Espaço excelente** (903GB livre) | Baseline |
| **Impacto** | Modelos grandes podem caber | Modelos 7-13B testado |
| **Rate Limite Esperado** | ~1-2 tok/s (local) | ~2-3 tok/s (local) |

**Vantagens OP2 TED**:
- Espaço: 903GB livre vs 480GB (+88%)
- Permite armazenar múltiplos modelos grandes

---

## 🎯 Análise: Por Que TED é Mais Desafiador que Nina

### **1. RAM Reduzida (8GB vs 16GB)**
```
OP1 Nina:  16GB → rodar llama3.2:7b (7GB) + system (1GB) = OK
OP1 TED:   8GB  → rodar llama3.2:3b (3GB) + system (1GB) = OK
           → llama3.2:7b vai sobrecarregar e usar swap

OP2 Nina:  16GB → hospeda 15 serviços Docker + modelo local
OP2 TED:   8GB  → mesmas 15 serviços, mas muito mais apertado
           → memory pressure maior, mais swap
```

**Ponderação**: Limitar modelos locais a 3-4B max. Router Agent fallback pra Groq/Gemini.

### **2. CPU Mais Fraco (i5 dual vs i7 quad)**
```
OP1 Nina:  i7 quad-core → 4 threads paralelos
OP1 TED:   i5 dual-core → 2 threads paralelos (-50% throughput)
           → Inferência ~2x mais lenta

Implicação: Router Agent vai usar Groq (nuvem) mais frequentemente
```

### **3. Espaço OP1 Limitado (176GB livre)**
```
OP1 Nina:  ~480GB → pode manter 3 modelos + dados + logs
OP1 TED:   176GB  → apertado, limpeza frequent necessária
           → Não colocar Restic backup aqui (vai ficar sem espaço)
```

⚠️ **Isso muda a decisão v1.1!**  
v1.1 diz: "Repositório Restic no OP1"  
Mas OP1 TED tem só 176GB livre. Se Restic começar a acumular backups diários:
- Dia 1: 50GB backup
- Dia 10: 500GB (sem espaço!)

**Solução**: Restic em MinIO do OP2 (903GB), mas com cleanup automático.

### **4. Espaço OP2 Abundante (903GB livre) — Vantagem**
```
OP2 Nina:  480GB  → storage central, mas limitado
OP2 TED:   903GB  → muita sobra
           → Pode rodar Restic aqui com segurança
           → Pode manter múltiplos modelos grandes (13B+)
           → Backup local robusto
```

---

## 🔌 SSDs Externos — BENCHMARK COMPLETO (Fase 0) ✅

### OP1 — Comparativo

| Tipo | Velocidade | Espaço | Conexão | Decisão |
|------|-----------|--------|---------|---------|
| **Interno** | **813 MB/s** | 176GB livre | SATA nativo | ✅ **USAR** |
| **Externo** | **455 MB/s** | 931GB livre | USB3/TB | Backup |

**Análise**: Interno é 1.8x mais rápido. Mantém tudo no interno, externo é para backup.

---

### OP2 — Comparativo

| Tipo | Velocidade | Espaço | Conexão | Decisão |
|------|-----------|--------|---------|---------|
| **Interno** | **87 MB/s** ⚠️ | 903GB livre | SATA nativo | ❌ Muito lento |
| **Externo** | **457 MB/s** ✅ | 915GB livre | USB3/TB | **USAR** 🔥 |

**Análise**: **CRÍTICO** — Externo é 5.3x mais rápido! DEVE usar externo para Docker + Ollama.

**Implicação**: OP2 docker-compose.yml vai apontar volumes para `/Volumes/Install\ macOS\ Sonoma/`

---

## 📋 Decisões Baseadas em Hardware TED

### **Modelos Ollama Disponíveis (8GB RAM)**

| Modelo | Tamanho | OP1 TED | OP2 TED |
|--------|---------|---------|---------|
| llama3.2:3b | ~2GB | ✅ Sim | ✅ Sim |
| phi4-mini | ~2.5GB | ✅ Sim | ✅ Sim |
| dolphin3 | ~4.7GB | ❌ Não (RAM) | ✅ Sim |
| mistral:7b | ~4.1GB | ❌ Não (RAM) | ✅ Sim |
| llama3.2:7b | ~4.7GB | ❌ Não (RAM) | ✅ Sim |

**Recomendação**:
- **OP1**: llama3.2:3b + phi4-mini (combinado ~4.5GB, deixa 3.5GB pro sistema)
- **OP2**: Todos os modelos acima (pode rodar 2+ em paralelo com cuidado)

### **Router Agent Cascata (Ajustado para TED)**

```
task_type: local
1. Ollama OP1 (3b) ← rápido mas limitado
2. Ollama OP2 (maior modelo) ← mais lento, mais capaz
3. Groq ← nuvem, rápido, com quota
4. Gemini ← nuvem, quota menor

[Não usar Exo — latência WAN]
```

### **Docker/Modelos — Caminho Quente (DECISÃO FINAL Fase 0)** ✅

#### OP1 → Usar INTERNO
```bash
# docker-compose mounts
volumes:
  postgres: /var/lib/postgresql
  redis: /var/lib/redis
  ollama: /var/ollama
# Tudo no / (interno 813 MB/s)
```

#### OP2 → Usar EXTERNO
```bash
# docker-compose mounts
volumes:
  postgres: /Volumes/Install macOS Sonoma/docker/postgres
  redis: /Volumes/Install macOS Sonoma/docker/redis
  ollama: /Volumes/Install macOS Sonoma/ollama
# Tudo no externo 1TB (457 MB/s — 5x melhor que interno)
```

**Impacto**:
- OP1: 176GB interno suficiente pra Docker + Ollama (3-4B modelos)
- OP2: 915GB externo abundante pra tudo (15 serviços + modelos grandes)

---

## 🚨 Riscos Específicos do TED (vs. Nina)

| Risco | Impacto | Mitigação |
|-------|--------|-----------|
| **RAM baixa (8GB)** | Swap constante, lentidão | Limitar modelos a ≤4B |
| **CPU fraca (i5 dual)** | Throughput reduzido | Usar Groq/Gemini como primary |
| **OP1 espaço baixo** | Sem lugar pra Restic | Restic em OP2, não em OP1 |
| **SSD externo desconhecido** | Pode ser USB2 lento | Testar benchmark Fase 0 |
| **OP2 WAN latência** | Exo inviável | Ollama isolado, não cluster |

---

## ✅ Checklist — Levantamento Completo Fase 0

- [x] GERENTE hardware capturado
- [x] COORD hardware capturado
- [x] OP1 hardware capturado (parcial)
- [x] OP2 hardware capturado (parcial)
- [ ] **OP1 SSD externo: modelo + velocidade benchmark**
- [ ] **OP2 SSD externo: modelo + velocidade benchmark**
- [ ] AVX2 confirmado em Intel nós
- [ ] Latência OP1↔OP2 confirmada (116ms WAN) ✓
- [ ] Decisão: Restic em OP2, não OP1 (espaço)
- [ ] Decisão: Modelos ≤4B para OP1 (RAM)
- [ ] Decisão: Modelos até 7B para OP2 (RAM + espaço)

---

## 📝 Próximo Passo

**Fazer benchmark SSD de OP1 e OP2** (interno vs externo) para:
1. Decidir caminho quente (Docker/Ollama)
2. Decidir se Restic cabe em OP1 ou deve ir em OP2
3. Determinar se há SSD externo USB2 lento que desaconselhamos usar

**Status**: Benchmark em progresso via SSH.
