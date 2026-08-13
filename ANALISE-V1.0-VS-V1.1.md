# Análise: TED v1.0 vs v1.1 — Lições Aprendidas na Nina

**Data**: 2026-08-12  
**Contexto**: Comparação com levantamento real de hardware do TED + experiência da construção da Nina

---

## 📋 Resumo Executivo

O v1.0 era um plano **teórico** baseado em suposições. O v1.1 é uma **execução prática** com lições concretas da Nina. As principais mudanças:

1. **Metodologia**: v1.0 → instale tudo; v1.1 → descubra primeiro (Fase 0), decida depois (Fase 1), instale (Fase 2)
2. **Hardware**: v1.0 assume specs; v1.1 valida in loco antes de confiar
3. **Arquitetura**: v1.0 planeja Exo; v1.1 desrecomenda por latência WAN
4. **Resiliência**: v1.0 backup no mesmo nó; v1.1 backup separado
5. **Tooling**: v1.0 assume OrbStack; v1.1 sugere testar Colima

---

## 🔍 Diferenças Detalhadas

### 1. Hardware — Specs Reais vs. Suposições

| Item | v1.0 | v1.1 | **Hardware Real TED** |
|------|------|------|----------------------|
| **COORD** | Mac Mini M4 | Mac Mini **M2** ⚠️ | **Confirmado: M2** |
| **OP1** | Mac Mini Intel i5 16GB | Intel i5 dual-core 16GB | **Real: Intel dual-core 2011, 8GB RAM** ⚠️ |
| **OP2** | Mac Mini Intel i5 16GB | Intel i5 quad-core 16GB | **Real: Intel i5 2011, 8GB RAM, 903GB livre** ⚠️ |
| **Disco OP2** | 1TB NVMe externo | 1TB mas testar | **Confirmado: 931GB SSD, ~903GB livre** |
| **SSD Caminho quente** | Externo presumido | Testar benchmark | **Precisa testar OP1 vs OP2** |

**Ponderação TED**: 
- OP1 e OP2 têm **MENOS RAM** que o planejado (8GB vs 16GB esperado)
- OP2 tem **MÁS ESPAÇO** (903GB livre é muito mais que OP1's 176GB)
- Isso muda decisões de: alocação de modelos, Exo viabilidade, backup

---

### 2. Exo Cluster — Recomendação: **NÃO USAR**

#### v1.0 (Teórico)
```
Plano: OP1 + OP2 = 32GB pool → modelos 13B-30B
Benefício: Modelos maiores que 16GB
```

#### v1.1 (Baseado em Nina)
```
Problema achado: latência WAN entre nós em redes diferentes
Solução: cada nó Ollama independente + Router Agent cascata
```

#### **Decisão TED** (Baseada em Fase 0):
- **OP2 está em "outra rede"** (casa da mãe, WAN)
- Latência OP1↔OP2 será alta (>100ms, vimos 116ms médio em testes)
- **Exo inviável** — cada nó roda Ollama isolado
- Router Agent escolhe qual LLM por fallback, não por cluster

**Implicação**: Economia de tempo instalação, menos complexidade.

---

### 3. Backup Restic — Proteção Contra Ponto Único de Falha

#### v1.0 (Vulnerável)
```
Restic → MinIO no OP2
Risco: se OP2 falha/é comprometido → perde dados E backup
```

#### v1.1 (Corrigido na Nina)
```
Restic → SFTP no OP1 (separado fisicamente)
```

#### **Decisão TED**:
- **Implementar v1.1**: repositório Restic no OP1, não no MinIO do OP2
- Comando: `sftp://tedop1@op1.ted:~/restic-backups`
- Dessa forma: se OP2 falha, dados de Vaultwarden estão seguros em OP1

---

### 4. Router Agent — Rate Limits Reais (não teóricos)

#### v1.0 (Specs de datasheet)
```
6 providers: Ollama → Groq → Gemini → OpenRouter → Nvidia → Anthropic
Sem controle de quota real
```

#### v1.1 (Baseado em uso real da Nina, ago/2026)
```
Provider     | Limite Real
Groq         | 30 RPM (org-wide)
Gemini       | 50-80% cortado em dez/25
Gemini Gemma | Limites originais, mais altos
NVIDIA NIM   | ~40 RPM
OpenRouter   | 20 RPM / 1.000 RPD
```

#### **Cascata Real Recomendada (TED)**:
```
task_type: default
1. Gemini (Gemma) ← modelo mais econômico, mantém limites
2. Groq ← 30 RPM, confiável
3. Ollama local (op2.ted:11434) ← sem limite, mas lento
[OpenRouter + Anthropic] = manual, use quando explicito
```

**Ponderação TED**:
- Com OP2 em 903GB livre, pode rodar modelos locais maiores
- Gemini Gemma é boa primeira escolha (economia de quota)
- Groq como fallback rápido
- Implementar Redis rate limiter em OP2 (foi achado em v1.1)

---

### 5. Doctor Agent — Evitar Alertas Duplicados

#### v1.0 (Schedule + Telegram direto)
```
Schedule 5min → detecta problema → alerta Telegram × N vezes
Risco: spam de alertas, falsos positivos
```

#### v1.1 (Webhook Uptime Kuma)
```
Uptime Kuma detecta up/down uma vez
Doctor Agent webhook: diagnóstico + Telegram (uma vez por incidente)
Manual endpoint: /doctor/diagnose pra checagem sob demanda
```

#### **Decisão TED**:
- **Implementar v1.1**: Doctor Agent gatilhado só por Uptime Kuma
- Isso vai evitar spam de Telegram quando há problemas transitórios

---

### 6. Docker Runtime — OrbStack vs. Colima

#### v1.0
```
Assume OrbStack sem alternativa
```

#### v1.1
```
Aviso: OrbStack teve bug em Nina (falha ao iniciar em sessão não-GUI-primária)
Colima como alternativa — mas: --mount substitui em vez de somar
```

#### **Decisão TED**:
- **Começar com OrbStack** (mais simples)
- Se encontrar problema na Fase 2: trocar para Colima
- Documentar no `DOCKER_RUNTIME.md` quando trocar

---

### 7. Tailscale no Login — Novo em v1.1

#### v1.0
```
Não especificado
Problema achado: Tailscale não inicia automaticamente no login
```

#### v1.1
```
LaunchAgent RunAtLoad em todos os 4 nós desde dia 1
```

#### **Status TED**:
- ✅ **JÁ FEITO** — LaunchAgent `io.tailscale.ted` em GERENTE, COORD, OP1, OP2
- ✅ Retry logic + monitoramento contínuo
- ✅ Health check automático a cada 5 minutos

---

### 8. Outline — Bancas Separadas (v1.1)

#### v1.0
```
PostgreSQL compartilhado entre serviços
```

#### v1.1
```
Cada serviço banco próprio: ted_outline, ted_core, etc.
Nota: Outline precisa UTILS_SECRET além de SECRET_KEY
Outline não tem TOTP nativo (precisa SMTP)
```

#### **Decisão TED**:
- Criar bancos separados no Postgres desde instalação
- Verificar versão Open WebUI antes de contar com 2FA

---

### 9. Redis para Rate Limiter (Novo em v1.1)

#### v1.0
```
Não menciona Redis
```

#### v1.1
```
Redis recomendado pra contador de quota por provider (RPM/RPD)
Roda no OP2, acessível via Tailscale
```

#### **Decisão TED**:
- **Adicionar Redis ao catálogo de 15 serviços**
- Configuração: requirepass no OP2, acessível de OP1 (Router Agent)
- Benefício: não gastar quota sem perceber

---

### 10. OpenCore Legacy Patcher — Validar Necessidade

#### v1.0
```
Assume necessário em OP1/OP2 (2011-era Intel Macs)
```

#### v1.1
```
Confirmar se realmente necessário baseado no modelo real
```

#### **Situação TED**:
- OP1: Macmini7,1 (2011-2012, Intel i5 dual-core)
- OP2: Macmini7,1 (2011-2012, Intel i5)
- **Ambos provavelmente precisam** de OpenCore Legacy Patcher
- ⚠️ **Validar em Fase 0** antes de formatar

---

## 🎯 Ponderações Finais — TED vs. Nina

### O que é igual:
- ✅ 4 nós (OP1 operações, OP2 infraestrutura, COORD coordenador, GERENTE interface)
- ✅ Tailscale como VPN backbone
- ✅ 15 serviços Docker no OP2
- ✅ 3 agentes Python (Router, Doctor, DocReader)
- ✅ Vaultwarden + Uptime Kuma + n8n

### O que é diferente:
| Aspecto | Nina | TED |
|---------|------|-----|
| **Latência OP1↔OP2** | Mesma LAN | WAN (~116ms) |
| **RAM por nó** | 16GB (spec assume) | **8GB (real)** |
| **Espaço OP2** | ~1TB | **903GB livre** |
| **COORD** | M4 (planejado) | **M2 (real)** |
| **Exo** | Testado, descartado | **Não fazer** |
| **Backup** | Restic em OP1 | **Igual** |

### Decisões Críticas (Fase 1):
1. ✅ **Exo**: Não usar (latência WAN)
2. ✅ **SSD caminho quente**: Testar benchmark real em Fase 0
3. ✅ **Modelos locais**: Limitar a 7B (cabem em 8GB RAM)
4. ✅ **Router cascata**: Gemini Gemma → Groq → Ollama local
5. ✅ **Backup**: Restic em OP1, não em OP2
6. ✅ **Redis**: Adicionar ao catálogo para rate limiter

---

## 📝 Checklist — Aplicar v1.1 no TED

- [x] Tailscale confiabilizado (auto-start + monitoring)
- [x] Hardware documentado (Fase 0)
- [ ] Decisões Fase 1 confirmadas (Exo, SSD, modelos)
- [ ] OpenCore validado (formatar com confiança)
- [ ] Restic configurado em OP1 (não em OP2)
- [ ] Redis adicionado ao docker-compose
- [ ] Doctor Agent com webhook (não schedule)
- [ ] Rate limits do Router documentados

---

**Próximo Passo**: Fase 1 — Com dados reais, confirmar decisões acima. Depois Fase 2 com todas as correções da Nina já aplicadas desde dia 1.
