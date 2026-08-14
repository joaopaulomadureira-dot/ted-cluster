# Hardware real — OP1

✅ **DADOS CAPTURADOS** (2026-08-12 via SSH - tedop1@100.112.109.38)

- Modelo: Mac mini
- Identificador: Macmini7,1
- Ano/geração: **Late 2014** (corrigido 14/08/2026 — doc original dizia "2011-2012" errado)
- CPU: Intel Core i5-4278U (Haswell) dual-core @ 2.60GHz
- AVX2: ✅ **SIM** (corrigido 14/08/2026 — confirmado via `sysctl hw.optional.avx2_0` = 1; a suposição original de "sem AVX2" estava errada e bloqueou desnecessariamente o OpenCode nativo por dias)
- RAM: 8 GB
- Disco interno: 234 GB total, 12 GB utilizado, 176 GB livre
- Disco externo: Nenhum

## Benchmark de disco ✅

### Disco Interno (SSD nativo)
- **Escrita**: 813 MB/s ✅ RÁPIDO
- **Leitura**: 6.2 GB/s (cache)

### Disco Externo (1TB SSD em /Volumes/1)
- **Escrita**: 455 MB/s ✅ Bom (USB3/Thunderbolt)
- **Leitura**: 6.2 GB/s (cache)
- Espaço: 931GB total, praticamente vazio

### 🎯 Decisão Fase 1:
**USAR INTERNO** (813 MB/s)
- Interno é 1.8x mais rápido
- Espaço suficiente (176GB livre)
- Externo 1TB: reservado para backup/armazenamento extra

## Notas críticas

- ⚠️ **Macmini7,1 é de 2011** — CPU Intel i5 dual-core muito antiga
- **Talvez NÃO tenha AVX2** — pode bloquear OpenCode e Tailscale CLI
- Latência Tailscale: ~5-45ms (variável, pode estar em outra subnet)
- **Recomendação Fase 1**: Verificar AVX2, considerar limitações de CPU

## Fase 0 status

- **COMPLETO** (mas com ressalvas sobre suporte AVX2)
