# Ecossistema TED — Fase 0 (Descoberta de Hardware)

## Status: EM PROGRESSO ✓

### ✅ Completado
- [x] Claude Code regularizado no GERENTE (M4 MacBook)
- [x] Estrutura de diretórios criada: `~/Ted/hardware/`
- [x] Hardware do GERENTE descoberto e documentado
- [x] Templates criados para COORD, OP1, OP2

### 📋 Próximos passos (você executa)

#### 1. COORD (Mac Mini M2)
SSH/acesso local:
```bash
ssh coord-ted  # ou acesso local
cd ~/Ted/hardware/
# Rodar os comandos do template coord.md e preencher
```

#### 2. OP1 (Mac Mini Intel i5)
```bash
ssh op1-ted  # ou acesso local
# Rodar os comandos do template op1.md + benchmark de disco
# Preencher resultado
```

#### 3. OP2 (Mac Mini Intel i7)
```bash
ssh op2-ted  # ou acesso local
# Rodar os comandos do template op2.md + benchmark de disco
# Preencher resultado
# Pós-Tailscale: teste de latência OP1 ↔ OP2
```

### 🎯 Após preencher todos os 4 nós:
- Revisar `/hardware/*.md` (todos os 4 arquivo preenchidos)
- Decidir:
  - **Exo?** (basear em latência OP1↔OP2)
  - **Caminhos quentes** (interno vs. externo em cada operador)
  - **OpenCore Legacy Patcher?** (confirmar com hardwares Intel reais)
  - **Onde rodam OpenCode + Tailscale CLI** (verificar AVX2)

### 💾 Dados do GERENTE (já capturados)
- MacBook Air M4 (Apple Silicon)
- 16 GB RAM
- 228 GB SSD (12 GB usado, 184 GB livre)
- Sem disco externo
- Tailscale hostname: PENDENTE

---

**Próximo comando:** Preencher os dados dos 3 nós restantes, depois chamar Claude Code novamente para Fase 1.
