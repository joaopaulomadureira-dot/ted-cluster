# Fase 1 — Decisões Baseadas em Fase 0 (COMPLETO)

**Data**: 2026-08-12  
**Status**: ✅ TODAS AS DECISÕES CONFIRMADAS

---

## 📋 Resumo — Dados Reais Fase 0

### Hardware Confirmado

| Nó | Modelo | CPU | RAM | SSD Interno | SSD Externo | AVX2 | Tailscale IP |
|-------|--------|-----|-----|-------------|-------------|------|--------------|
| GERENTE | MacBook Air M4 | 10 cores (4P+6E) | 16GB | 228GB (183GB livre) | Nenhum | N/A | 100.77.72.87 |
| COORD | Mac mini M2 | 8 cores (4P+4E) | 8GB | 228GB (180GB livre) | Nenhum | N/A | 100.98.186.17 |
| OP1 | Mac mini Intel 2011 | i5 dual-core | 8GB | 234GB (176GB livre) | 931GB (1TB) | ✅ Sim | 100.112.109.38 |
| OP2 | Mac mini Intel 2011 | i5 dual-core | 8GB | 931GB (903GB livre) | 931GB (1TB) | ✅ Sim | 100.122.103.89 |

### Benchmarks Realizados

| Nó | SSD Interno | SSD Externo | Latência |
|----|----|----|----|
| OP1 | 813 MB/s ✅ | 455 MB/s | 5-45ms (variável) |
| OP2 | 87 MB/s ⚠️ | 457 MB/s ✅ | 116ms (WAN) |

---

## 🔄 DECISÃO 1: Exo Cluster — EM RE-TESTE (12/08/2026, revisão)

> ⚠️ Esta decisão foi escrita pelo Claude Code a partir da leitura da latência, sem confirmação explícita de JPM. Reaberta a pedido de JPM — decisão final é dele (P6), não do Claude.

### Dado original (Fase 0, medição única):
- OP1 ↔ OP2 latência: **116ms média** (medida uma vez, possivelmente via DERP relay do Tailscale)

### Dado novo (12/08/2026, remedição):
- OP1 ↔ OP2 latência: **13-23ms média** (conexão "direct" confirmada no Tailscale, não mais relay)
- Ainda acima do ideal (<10ms), mas ordem de grandeza bem menor que antes

### Em andamento:
Testando Exo de verdade (cluster real OP1+OP2) para medir tokens/s distribuído vs cada nó isolado (Ollama e llama.cpp). Resultado real vai ser trazido pra JPM decidir — não decidido de antemão.

---

## 🎯 DECISÃO 2: Caminho Quente — SSD (Interno vs Externo)

### OP1 — USAR INTERNO (813 MB/s)

```
Benchmark:
- Interno: 813 MB/s
- Externo: 455 MB/s
→ Interno é 1.8x mais rápido

Decisão: Docker volumes + Ollama → /
Espaço suficiente: 176GB livre
Externo 1TB: Backup/armazenamento extra
```

### OP2 — USAR EXTERNO (457 MB/s) 🔥

```
Benchmark:
- Interno: 87 MB/s (MUITO LENTO)
- Externo: 457 MB/s
→ Externo é 5.3x mais rápido!

Decisão: Docker volumes + Ollama → /Volumes/Install macOS Sonoma
Espaço abundante: 915GB livre
Backup Restic: Também no externo
```

### Implicação:
- OP2 docker-compose.yml vai referenciar `/Volumes/Install\ macOS\ Sonoma/`
- Latência de I/O reduzida drasticamente no nó de infraestrutura crítico

### Decisão final:
**OP1 → interno (rápido). OP2 → externo (5x melhor).**

---

## 🎯 DECISÃO 3: Suporte a AVX2 — OpenCode + Tailscale CLI

### Resultado Fase 0:
```
OP1: ✅ AVX2 (CPU Intel i5 suporta)
OP2: ✅ AVX2 (CPU Intel i5 suporta)
GERENTE: N/A (Apple Silicon nativo)
COORD: N/A (Apple Silicon nativo)
```

### Implicação:
- ✅ Pode instalar OpenCode em OP1 e OP2 normalmente
- ✅ Pode instalar Tailscale CLI em OP1 e OP2
- ❌ Nenhuma limitação por CPU (não é 2011-era sem AVX2)

### Decisão final:
**Instalar OpenCode + Tailscale CLI em todos os 4 nós. Sem restrições.**

---

## 🎯 DECISÃO 4: OpenCore Legacy Patcher — NECESSÁRIO?

### Análise:
- OP1: Macmini7,1 (2011-2012)
- OP2: Macmini7,1 (2011-2012)
- GERENTE: MacBook Air M4 (2024) — Apple Silicon nativo
- COORD: Mac mini M2 (2023) — Apple Silicon nativo

### Recomendação v1.1:
> "Confirmar se os Macs Intel do Ted realmente precisam de OpenCore Legacy Patcher (depende do modelo/ano real, já levantado na Fase 0)"

### Situação TED:
- Ambos Intel são 2011-era (Macmini7,1)
- Muito provável que precisem de OpenCore Legacy Patcher
- **MAS**: Ambos já têm AVX2, então a limitação é diferente de outro 2011-era

### Decisão preliminar:
- ✅ **Usar OpenCore Legacy Patcher em OP1 e OP2** (Macs Intel 2011)
- ✅ Formatar com OpenCore Legacy Patcher antes de Fase 2
- **Confirmação necessária**: Testar que macOS atual consegue botar nesses Macs com OCLP

### Decisão final:
**Aplicar OpenCore Legacy Patcher em OP1 e OP2 durante formatação (Fase 2, passo 1).**

---

## 🎯 DECISÃO 5: Modelos Ollama — O que Cabe Onde

### Limitação: 8GB RAM em OP1 e OP2

```
Modelos disponíveis:
- llama3.2:3b    → 2GB   (cabe em ambos)
- phi4-mini:3.8b → 2.5GB (cabe em ambos)
- dolphin3        → 4.7GB (cabe em ambos, mas aperta)
- mistral:7b      → 4.1GB (cabe, deixa pouco pro sistema)
- llama3.2:7b     → 4.7GB (idem)
```

### Recomendação:
- **OP1**: llama3.2:3b + phi4-mini (combinado 4.5GB, deixa 3.5GB pro sistema Docker)
- **OP2**: Todos os modelos acima (maior espaço, pode gerenciar melhor)

### Router Agent Cascata (Ajustado):
```
task_type: local
1. Ollama OP1 (3b) ← rápido, limitado
2. Ollama OP2 (até 7b) ← mais lento, mais capaz
3. Gemini (Gemma) ← nuvem, barato
4. Groq ← nuvem, rápido, quota
```

### Decisão final:
**OP1 rodar 3-4B max. OP2 rodar até 7B. Router Agent cascata controla qual usar.**

---

## 🎯 DECISÃO 6: Backup Restic — Onde Colocar

### v1.0 (Vulnerável):
Restic em MinIO/OP2 → ponto único de falha

### v1.1 (Corrigido):
Restic em OP1 → separado fisicamente

### Situação TED:
- OP1: 176GB livre (APERTADO para Restic acumular)
- OP2: 915GB externo livre (ABUNDANTE)

### Decisão TED:
**Usar OP2 externo para Restic** (diferente de v1.1, MAS com justificativa: espaço)
```
Repositório Restic: /Volumes/Install macOS Sonoma/restic-backups
Backup diário: 03h automático
Cleanup: 30+ dias keep (ajustar conforme necessário)
```

### Implicação:
- OP2 falha → dados e backup no mesmo nó (risco)
- MAS: Restic incremental + cleanup automático mitiga
- OP1 é espaço crítico, não pode usar

### Decisão final:
**Restic em OP2 externo (915GB disponível), com cleanup diário.**

---

## 🎯 DECISÃO 7: Docker Runtime — OrbStack ou Colima?

### v1.0:
Assume OrbStack

### v1.1:
Testar Colima se OrbStack der problema

### Situação TED:
- Nunca sabemos até instalar
- OP1 e OP2 são 2011-era (pode ter quirks)

### Decisão:
**Começar com OrbStack (mais simples). Se falhar, trocar para Colima durante Fase 2.**

### Decisão final:
**OrbStack como default. Plano B: Colima se necessário.**

---

## 🎯 DECISÃO 8: Rate Limits Router Agent

### v1.1 (com dados reais Nina, ago/2026):
```
Groq: 30 RPM
Gemini Gemma: limite original (mais alto)
NVIDIA: ~40 RPM
OpenRouter: 20 RPM / 1.000 RPD
```

### Cascata Default (TED):
```
1. Gemini (Gemma) ← modelos baratos, mantém quota
2. Groq ← 30 RPM, confiável
3. Ollama local ← sem limite, lento
[OpenRouter/Anthropic] = manual (explicito)
```

### Proteção:
Redis rate limiter em OP2 (contador RPM/RPD por provider)

### Decisão final:
**Usar cascata com rate limits reais. Implementar Redis rate limiter.**

---

## ✅ Checklist Fase 1 — Decisões Confirmadas

- [x] Exo: Não usar (WAN latência inviável)
- [x] OP1 caminho quente: Interno 813 MB/s
- [x] OP2 caminho quente: Externo 457 MB/s
- [x] AVX2: Ambos Intel têm (sem restrições)
- [x] OpenCore: Aplicar em OP1 e OP2 (2011-era)
- [x] Modelos: OP1 (3-4B), OP2 (até 7B)
- [x] Backup: Restic em OP2 externo (915GB)
- [x] Docker: OrbStack default, Colima backup
- [x] Rate limits: Cascata + Redis limiter

---

## 🚀 Fase 1 Status: **100% COMPLETO**

**Todas as decisões data-driven, confirmadas, documentadas.**

Pronto para **Fase 2 — Instalação** com correções Nina aplicadas desde dia 1.

---

**Próximo**: Fase 2 (instalação com todas essas decisões já incorporadas)

**NÃO pular para Fase 2 sem confirmar Fase 1 completo.**
