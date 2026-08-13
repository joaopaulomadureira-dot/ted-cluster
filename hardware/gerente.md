# Hardware real — GERENTE

- Modelo: MacBook Air M4
- Identificador: Mac16,12
- Ano/geração: 2024 (M4 generation)
- CPU: Apple M4 (4 Performance cores + 6 Efficiency cores = 10 total)
- AVX2: N/A (Apple Silicon, não aplicável)
- RAM: 16 GB
- Disco interno: Apple Disk Image Media, 228 GB total, 12 GB utilizado, 184 GB livre
- Disco externo: Nenhum conectado
- Hostname Tailscale: macbook-air-de-ted (100.77.72.87)

## Notas de Fase 0 ✅

- GERENTE é Apple Silicon (M4), não precisa de OpenCore Legacy Patcher
- Não há disco externo — todo caminho quente (modelos, Docker volumes) ficará no interno
- Tailscale CLI e OpenCode terão suporte nativo (M4 é nativo, não precisa de AVX2)
- Latência Tailscale: 5-7ms (bom)
- **Fase 0 status: COMPLETO**
