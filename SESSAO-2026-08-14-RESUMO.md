# Sessão 14/08/2026 — Resumo (Bug crítico Tailscale autostart corrigido)

**Status geral**: Bug encontrado e corrigido nos 4 nós, validado com reboot real em todos. Cluster confirmado 4/4 online na tailnet ao final da sessão.

---

## 🐛 Problema reportado

JPM reportou que OP1, COORD e GERENTE não sobem o Tailscale sozinhos quando ligados — precisava abrir o app manualmente toda vez.

## 🔍 Causa raiz

O `setup-tailscale-autostart.sh` (criado na sessão de 12/08) gravava o LaunchAgent em `~/.launchagents/` (minúsculo, pasta oculta arbitrária). **O macOS só lê LaunchAgents de usuário em `~/Library/LaunchAgents/`.** O agente funcionou na sessão original só porque foi carregado manualmente com `launchctl load` — nunca sobreviveu a um reboot real, apesar de `TAILSCALE-FINAL.md` ter documentado erroneamente "100% operacional, auto-iniciando" naquele dia.

Confirmado idêntico nos 4 nós: GERENTE, COORD, OP1, OP2.

## ✅ Correção aplicada

Em cada nó:
1. `mkdir -p ~/Library/LaunchAgents`
2. Copiado o plist existente pra lá
3. `launchctl bootout gui/$UID <plist>` (limpa estado antigo, se houver)
4. `launchctl bootstrap gui/$UID <plist>` (forma correta no macOS moderno, substitui `launchctl load`)
5. `launchctl enable gui/$UID/io.tailscale.ted`

`~/Ted/setup-tailscale-autostart.sh` também corrigido pra não reintroduzir o bug em setups futuros.

## ✅ Validação — reboot real nos 4 nós

| Nó | Método de teste | Resultado |
|---|---|---|
| COORD | `osascript ... restart` via SSH | Voltou sozinho, Tailscale + `io.tailscale.ted` ativos |
| OP1 | `osascript ... restart` via SSH | Voltou sozinho, Tailscale + `io.tailscale.ted` ativos |
| OP2 | Já tinha caído/religado no ciclo normal; LaunchAgent corrigido enquanto acessível | Tailscale + `io.tailscale.ted` ativos |
| GERENTE | JPM reiniciou fisicamente | Boot 08:27:52 → 14 min depois, Tailscale.app + `io.tailscale.ted` + `io.tailscale.monitor` já rodando sozinhos |

Confirmação final: `tailscale status` no GERENTE mostra os 4 nós (`gerente-ted`, `coord-ted`, `op1-ted`, `op2-ted`) todos ativos na tailnet.

## 📌 Descoberta lateral: OP1 e OP2 têm ciclo de energia noturno

OP1 e OP2 desligam às 00:00 e ligam às 05:00 todo dia (schedule já existente, auto-login habilitado nos dois). Isso significa que a correção de hoje vai ter validação real automática toda noite — checar status depois das 5h é suficiente, não precisa forçar reboot manual.

## ⚠️ Achado durante o teste: OP2 sobrecarrega ao ligar (12 containers simultâneos)

O reboot de teste do OP2 expôs sobrecarga real de memória (`vm_stat` mostrou ~15MB livres de 8GB) quando os 12 containers do docker-compose sobem todos juntos (comportamento padrão do `restart: unless-stopped` quando o Docker inicia). ChromaDB e n8n ficaram intermitentes/inacessíveis por alguns minutos até estabilizar. JPM confirmou: é esperado, é por isso que o boot é agendado pra 5h da manhã (sem uso ativo nesse horário) — mas pediu uma cascata de subida em vez de tudo de uma vez, pra aliviar o pico.

**Correção aplicada:**
- `docker update --restart=no` nos 12 containers (não recria, só desliga o auto-restart simultâneo) + `docker-compose.yml` atualizado como fonte de verdade
- Novo script `/Users/tedop2/ted-docker-cascade.sh` — espera o Docker responder, depois sobe os containers **um a um** com 20s de intervalo, na ordem: postgres → redis → minio → chromadb → caddy → vaultwarden → n8n → uptime-kuma → outline → open-webui → beszel → dozzle (banco/cache primeiro, pesados por último)
- LaunchAgent `com.ted.docker-cascade.plist` (RunAtLoad) registrado em `~/Library/LaunchAgents/` no OP2, dispara a cascata a cada boot
- Log em `/tmp/ted-docker-cascade.log`
- **Efeito colateral corrigido no OP1**: Doc Reader (porta 8012) crashava direto se o ChromaDB não estivesse pronto no boot simultâneo — criado wrapper `wait-and-start.sh` que espera o heartbeat do ChromaDB (até 5 min) antes de subir o uvicorn. Plist `com.ted.docreader.plist` atualizado pra chamar o wrapper.

**Não testado com reboot real ainda** (evitado de propósito, pra não sobrecarregar o OP2 de novo agora) — validação real vai acontecer no ciclo natural de hoje à noite (desliga 00h, liga 5h). Conferir `/tmp/ted-docker-cascade.log` no OP2 depois das 5h.

## 🧠 Lição para outros LaunchAgents do projeto

Qualquer LaunchAgent futuro (do Ted ou de outro serviço) deve ser criado direto em `~/Library/LaunchAgents/` e carregado com `launchctl bootstrap gui/$UID` — não `~/.launchagents/` nem `launchctl load` (deprecated, mascarava o bug porque carrega mas não persiste a associação correta com o boot).
