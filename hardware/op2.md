# Hardware real — OP2

✅ **DADOS CAPTURADOS** (2026-08-12 via SSH - tedop2@100.122.103.89)

- Modelo: Mac mini
- Identificador: Macmini7,1
- Ano/geração: **Late 2014** (corrigido 14/08/2026 — doc original dizia "2011-2012" errado, igual OP1)
- CPU: Intel Core i5-4278U (Haswell) dual-core @ 2.60GHz (confirmado idêntico ao OP1)
- AVX2: ✅ **SIM** (corrigido 14/08/2026 — confirmado via `sysctl hw.optional.avx2_0` = 1)
- RAM: 8 GB
- Disco interno: 931 GB total, 12 GB utilizado, 903 GB livre (2% capacity)
  - **⚠️ MUITO MAIS ESPAÇO que OP1** (903 GB vs 176 GB)
- Disco externo: ✅ **EXISTE (não montado atualmente)**

## Benchmark de disco ✅

### Disco Interno (SSD nativo)
- **Escrita**: 87 MB/s ⚠️ LENTO
- **Leitura**: 6.8 GB/s (cache)

### Disco Externo (1TB SSD em /Volumes/Install\ macOS\ Sonoma)
- **Escrita**: 457 MB/s ✅ RÁPIDO (USB3/Thunderbolt)
- **Leitura**: 6.6 GB/s (cache)
- Espaço: 931GB total, 915GB livre (só 16GB usado)

### 🎯 Decisão Fase 1:
**USAR EXTERNO** (457 MB/s) 🔥
- Externo é **5x mais rápido** que interno (457 vs 87 MB/s)
- Espaço abundante (915GB livre)
- **CRÍTICO**: Docker volumes + Ollama modelos → `/Volumes/Install macOS Sonoma`
- Interno → apenas SO, não usado para carga

## Notas críticas

- ⚠️ **Macmini7,1 é de 2011** — CPU Intel i5 dual-core muito antiga
- **Talvez NÃO tenha AVX2** — pode bloquear OpenCode e Tailscale CLI
- **Latência Tailscale:** ~116ms média (45-257ms) — em outra rede/localização (WAN)
- **Espaço em disco:** Excelente para armazenar modelos Ollama (903 GB)
- **Recomendação Fase 1:** Verificar AVX2, usar como "armazenamento central" se possível

## Fase 0 status

- **✅ COMPLETO** — Todos os 4 nós com dados de hardware

## Exo viabilidade final

- ❌ OP2 em WAN (latência 116ms)
- ❌ OP1 latência variável (5-45ms)
- ✅ **Decisão:** NÃO USAR EXO — cada operador com Ollama independente
