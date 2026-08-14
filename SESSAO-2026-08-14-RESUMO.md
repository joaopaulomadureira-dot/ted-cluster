# Sessão 14/08/2026 — Resumo (Bug crítico Tailscale autostart corrigido)

**Status geral**: Bug encontrado e corrigido nos 4 nós, validado com reboot real em todos. Cluster confirmado 4/4 online na tailnet ao final da sessão. Depois, primeira leva de 6 MCP servers instalada e testada de ponta a ponta em GERENTE e COORD. Em seguida, n8n MCP instalado e testado; Outline MCP bloqueado (sem auth configurado).

---

## 🔧 Municiamento — n8n MCP (GERENTE + COORD)

n8n já tem MCP nativo desde a v2.34 (confirmado — instância roda 2.34.5). Habilitado via UI (`Settings → Instance-level MCP → Enable MCP access`, sem endpoint REST pra isso, só a UI mesmo) — automatizado via Safari + AppleScript (System Events, clicando elementos AXButton pelo nome, não por coordenada de tela — coordenadas de pixel se mostraram pouco confiáveis nesse ambiente).

- **Server URL**: `http://op2-ted.tail2a272d.ts.net:5678/mcp-server/http`
- **Auth**: Bearer token dedicado de MCP (gerado na própria tela de conexão, diferente da API key pública do n8n)
- **Exposição**: todos os workflows expostos ("Expose all workflows to MCP") — só existem os 2 de teste hoje, sem risco
- **Teste real**: handshake MCP completo via curl, retornou capabilities + instruções detalhadas do SDK de workflow (confirma servidor 100% funcional, não só "conectado")
- **Registrado**: Claude Code (`claude mcp add`, GERENTE e COORD, ambos "✔ Connected") + OpenCode (`opencode.jsonc` dos dois)
- **Vaultwarden**: item "TED MCP - n8n" criado com o token

### Nota técnica — automação de browser sem ferramenta dedicada
Não há Playwright/browser-MCP disponível nesta sessão. O caminho que funcionou: Safari via `osascript`, permissões **Accessibility** e **Screen Recording** liberadas pelo JPM (System Settings), e cliques via System Events **por referência de elemento AXButton encontrado por nome** (`entire contents of window`, filtra `role is "AXButton"` + `name is "X"`, depois `click e`) — não por coordenada de tela, que se mostrou não-confiável nesse display (múltiplos scale factors conflitantes entre screencapture e System Events causaram cliques errados, inclusive um clique acidental que abriu a App Store). Guardar esse padrão pra qualquer automação de UI futura no TED.

## ✅ Municiamento — Outline MCP (GERENTE + COORD)

O bloqueio inicial ("nenhuma conta existe") estava incompleto — JPM já tinha uma sessão de navegador ativa e logada no workspace "ted" (avatar "Joao Paulo"), então a checagem automática via `/api/auth.config` não capturou isso certo. Com a sessão já aberta, gerar a chave foi direto:

- **Endpoint**: `http://op2-ted.tail2a272d.ts.net:3002/mcp` (confirmado no doc oficial: self-hosted usa `<seu-domínio>/mcp`, só streamable HTTP, sem SSE)
- **Auth**: API key pessoal gerada em Settings → API e Acesso → Nova chave de API (nome "TED MCP", sem expiração)
- **Automação**: Safari + System Events, navegação direta pela sidebar (`Chaves de acesso` foi tentativa errada — é passkey biométrico, não API key; `API e Acesso` é a seção certa)
- **Teste real**: handshake MCP via curl retornou capabilities completas + instructions do servidor "outline" v1.9.2 (regras de formatação de documento, mentions, templates, attachments)
- **Registrado**: Claude Code (GERENTE + COORD, ambos "✔ Connected") + OpenCode (`opencode.jsonc` dos dois)
- **Vaultwarden**: item "TED MCP - Outline" criado

### Nota — Bitwarden CLI (`bw`) precisa de pty real
`bw unlock` via `--passwordenv` ou stdin pipe **crasha** (`ERR_USE_AFTER_CLOSE` no readline) nesta versão (2026.7.0) rodando sem TTY de verdade. Contornado com `expect` (`/usr/bin/expect`, já vem no macOS) simulando um terminal interativo de verdade. Guardar esse padrão pra qualquer uso futuro do `bw` neste cluster — os métodos "documentados" de automação não funcionam aqui.

## 🔧 Municiamento — 6 MCP servers instalados (GERENTE + COORD)

Primeira leva do catálogo levantado nesta sessão (research completa em conversa, não documentada em arquivo separado). Instalados e testados de ponta a ponta em **GERENTE e COORD** — Claude Code (`claude mcp add`, escopo `user`) e OpenCode (`~/.config/opencode/opencode.jsonc`):

| MCP | Onde aponta | Teste real feito |
|---|---|---|
| Filesystem | `~/Ted` (GERENTE) / home do usuário (COORD) | Conectado via handshake MCP |
| Sequential Thinking | local, sem estado | Conectado |
| Fetch | local (Python/uvx) | Conectado após fix de versão (ver abaixo) |
| Postgres | `ted_core` no OP2 (100.122.103.89:5432) | Conectado via handshake MCP |
| Docker | Docker/Colima do OP2, via túnel SSH | **Teste funcional real**: `list-containers` retornou os 12 containers reais (`ted-infra-*`) |
| GitHub | Endpoint oficial hospedado `api.githubcopilot.com/mcp/` | **Teste funcional real**: handshake + capabilities reais confirmados via curl |

### Bugs reais encontrados e corrigidos durante a instalação
- **`mcp-server-fetch`** (pip/uvx) quebra com a versão mais recente do SDK `mcp` (`ImportError: McpError` — renomeado pra `MCPError` upstream). Fix: pin `mcp==1.14.0` via `uvx --with "mcp==1.14.0" mcp-server-fetch`.
- **`docker-mcp`** (pip/uvx) quebra pelo mesmo motivo (`AttributeError: 'Server' object has no attribute 'list_prompts'`) e também exige Python ≥3.12 explícito. Fix: `uvx --python 3.12 --with "mcp==1.9.4" docker-mcp`.
- **GitHub MCP** não precisou de binário/Docker — existe um endpoint remoto oficial hospedado (`https://api.githubcopilot.com/mcp/`, auth via `Authorization: Bearer <PAT>`), muito mais simples que rodar `github-mcp-server` localmente.

### Decisão técnica — Docker MCP e o acesso remoto ao OP2
O Docker MCP precisa falar com o socket do Colima, que só existe localmente no OP2 (`unix:///Users/tedop2/.colima/default/docker.sock`, sem TCP exposto). Em vez de expor esse socket na rede (mais arriscado numa máquina já frágil), o comando registrado usa `ssh -i <chave> tedop2@100.122.103.89 'uvx ... docker-mcp'` — o processo roda no OP2, mas o stdio é tunelado pra quem chamou (GERENTE/COORD), sem precisar expor nada novo na rede. `uv`/`uvx` instalado no OP2 via Homebrew pra isso (rodou sem problema no hardware 2011, sem SIGILL).

### Bloqueio real — OP1 não consegue rodar nenhum destes agora
Duas causas independentes, nenhuma criada por esta sessão:
1. **Sem Node/npx/uvx nativo** — CPU 2011 sem AVX2 (mesma causa raiz documentada pro Tailscale CLI e OpenCode nativo).
2. **O Colima do OP1** (usado só pro wrapper Docker do OpenCode) está **quebrado**: `vz driver is running but host agent is not`. Precisa de `colima delete` + rebuild ou reinstalação — não tentei corrigir agora porque é destrutivo e fora do escopo desta tarefa.

Config das 6 entradas já está escrita em `~/.opencode-docker-state/.config/opencode/opencode.jsonc` do OP1 (com nota explicando o bloqueio), pronta pra funcionar assim que o Colima for corrigido. OP1 também não tem `~/.ssh/id_ed25519` (só existe no COORD) — a entrada Docker do OP1 vai precisar de uma chave própria quando for reativada.

**OP2**: tem seu próprio Colima funcionando normalmente (é o que hospeda o `ted-infra` e agora também o Docker MCP via túnel). Não configurei o OpenCode dele com as 6 entradas — o wrapper Docker do OpenCode lá usa uma imagem cujo entrypoint não é um shell simples, não investiguei mais fundo (fora do escopo principal desta tarefa, fica como pendência se fizer sentido no futuro).

### Vaultwarden
Instalado Bitwarden CLI (`bw`) no GERENTE, logado na conta pessoal do JPM (`https://100.122.103.89/`, self-signed — precisa `NODE_TLS_REJECT_UNAUTHORIZED=0` pro `bw` aceitar o certificado). Criado o item **"TED MCP - GitHub"** com o PAT usado pelo GitHub MCP. Primeira chave real migrada pro Vaultwarden desde que ele subiu (13/08) — o resto ainda está só no `TED_INFRA_CHAVES.md`.

### Pendências reais desta frente
1. Corrigir o Colima do OP1 (`colima delete` + rebuild) pra desbloquear os 6 MCPs lá
2. Investigar o wrapper OpenCode-Docker do OP2 (entrypoint da imagem) se fizer sentido registrar os MCPs lá também
3. Migrar o resto das chaves do `TED_INFRA_CHAVES.md` pro Vaultwarden (só o GitHub MCP foi migrado agora)
4. Próxima leva do catálogo (Skills oficiais docx/pdf/pptx/xlsx, subagentes) — aguardando decisão do JPM sobre o que instalar em seguida

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
