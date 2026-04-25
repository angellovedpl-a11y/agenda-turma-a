# Agenda Turma A - Escala Ferroviária 2x2 (2026-2030)

## Project Overview

A progressive web application (PWA) for railway workers ("Turma A") to manage their work schedules, time-off (folgas), mandatory documents, and professional audits.

## Architecture

- **Type:** Static single-page application (no build step required)
- **Core file:** `index.html` — contains all HTML, CSS, and JavaScript
- **Data persistence:** Browser `localStorage` (key: `turmaA_v10`)
- **No external dependencies** — fully self-contained

## Key Features

- Railway 2x2 shift rotation calculator (2026–2030)
- Document management (ASO) with expiration alerts
- Audit period visualization on calendar
- "Viriato" assistant chatbot for schedule queries
- Built-in alarm clock and browser notification support
- Dark/light theme

## Running the App

The app is served via Python's built-in HTTP server on port 5000:

```
python3 -m http.server 5000 --bind 0.0.0.0
```

## Viriato Library (Mem Palace inteligente)

PDFs e arquivos de texto anexados a qualquer dia da agenda são também enviados ao servidor (`/api/biblioteca/upload`), onde:
1. `pdfplumber` extrai o texto real
2. Claude Haiku categoriza (acordo_coletivo, norma_tecnica, manual, lei, etc.), gera resumo de 1 frase e 5 palavras-chave
3. O texto é dividido em chunks de ~600 palavras
4. Tudo é gravado em `data/biblioteca.json`

A cada mensagem ao Viriato, o servidor:
- Inclui o ÍNDICE da biblioteca (nome + categoria + resumo) no system prompt
- Faz busca por palavras-chave na pergunta do utilizador e injeta apenas os 3 trechos mais relevantes (com delimitadores `<<<DOC>>>` para mitigar prompt injection)

Endpoints novos:
- `GET /api/biblioteca` — lista metadados de todos os documentos indexados
- `POST /api/biblioteca/upload` — `{nome, mimetype, data: base64}` → indexa
- `POST /api/biblioteca/buscar` — `{query, top_k}` → top trechos relevantes
- `DELETE /api/biblioteca/<id>` — remove documento

Limite: 5MB por upload. PDFs digitalizados (imagem) não funcionam (sem OCR).

## Helpdesk e Diagnóstico

Pasta `helpdesk/` contém guias `.md` de troubleshooting (1 problema por arquivo: sintomas, causa, solução). O servidor inclui esses guias no system prompt do Viriato — quando o utilizador relata um erro, o Viriato consulta os guias e responde com a frase humorada **"🚦 *Parada pelo Governador!*"** (gíria ferroviária) seguida da explicação.

Endpoints:
- `GET /api/helpdesk` — lista guias disponíveis
- `GET /api/helpdesk/<arquivo.md>` — conteúdo de um guia
- `GET /api/diag/health` — status do servidor (data dir, pdfplumber, claude, helpdesk)
- `GET /api/diag/biblioteca` — estatísticas da biblioteca (totais, categorias, tamanho)

## Notificação por e-mail (novos cadastros)

- Integração SendGrid (Replit connector) — credenciais buscadas em runtime via `REPLIT_CONNECTORS_HOSTNAME` + `REPL_IDENTITY`/`WEB_REPL_RENEWAL`, sem cache.
- Módulo `notify.py`: `notificar_novo_cadastro(matricula, nome)` envia em background thread (não bloqueia o registro). HTML é escapado (`html.escape`). E-mails de log são mascarados.
- Cada admin/aprovador cadastra seu próprio e-mail em `POST /api/auth/email` (campo `email` salvo em `users.json`); endpoint protegido por `@require_approver`.
- `handle_registrar` chama `notify.notificar_novo_cadastro` (em try/except) somente para cadastros não-primeiros. Falha silenciosa se SendGrid não estiver configurado.
- UI: nova aba "E-mail" no painel admin/aprovador (`renderAdminPanel` em `index.html`), com input + botões Salvar/Remover e indicador de status.
- `handle_me` retorna `email` do próprio usuário (escopo individual, não vaza para listagem).

Botão **🩺 Diagnóstico** no header do Viriato abre modal com checklist visual de saúde (verde/vermelho).

## Notificações Push (Web Push)

PWA recebe notificações reais mesmo com o app fechado e celular bloqueado:
- **Backend** (`server.py`): biblioteca `pywebpush`, chaves VAPID em env vars (`VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`).
  - Helpers: `push_subs_load/save/add/remove`, `send_push_to_user`, `send_push_to_users` (auto-remove subs expiradas com status 404/410).
  - Subs por usuário em `kv_store` na chave `push_subs:<matricula>` (lista de subscriptions, suporta múltiplos dispositivos).
  - Endpoints: `GET /api/push/vapid-public-key`, `POST /api/push/subscribe`, `POST /api/push/unsubscribe`, `POST /api/push/test`.
  - Hooks: `chat_msg_enviar` notifica outros participantes; `mem_update` (sala='eventos') faz broadcast pra todos os aprovados ao detectar evento novo no mural.
- **Service Worker** (`sw.js` na raiz, escopo `/`): handler de `push` mostra `Notification` + faz `postMessage` pra abas abertas; handler `notificationclick` foca/abre janela e avisa o cliente.
- **Frontend** (`index.html`): registro do SW no boot, botão "🔔 Ativar notificações" no menu lateral, função `enablePushNotifications()` pede permissão + assina + envia ao servidor + dispara push de teste.
- **Buzina do trem** (`buzina_trem.mp3` na raiz): tocada via `Audio` quando push chega em foreground OU quando usuário clica em notificação. Limitação: com app fechado e celular bloqueado, o sistema toca o som padrão do OS (restrição de iOS/Android Web Push, não dá pra forçar MP3 customizado).
- **iOS**: requer iOS 16.4+ e PWA instalado na tela inicial. **Android**: funciona em qualquer Chrome.

## Deployment

Configured as a **static** deployment with `publicDir: "."`.
