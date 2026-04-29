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

## Diário de Bordo (privado, v3.0)

Aba **📓 Diário de Bordo** no menu lateral, entre "Meus Eventos" e "Chat Turma".
- **Backend** (`server.py`): helpers `diario_load/save` + endpoints `GET/POST /api/diario` (auth obrigatório). Armazenado em `kvstore` na chave `diario:<matricula>` — escopo individual, sem broadcast.
- **Frontend** (`index.html`): `renderDiario(c)` lista entradas ordenadas por data desc, com texto + thumbs de anexos (clicar abre fullscreen). Botão "Excluir" por entrada.
- **Nova entrada** (`openDiarioForm(dataPre)`): date picker, textarea, 3 botões — **📷 Câmera** (`capture="environment"`), **🖼️ Galeria** (multi), **📎 Arquivo** (.pdf, .txt, .doc, .docx). Imagens são comprimidas client-side via canvas (`_compressImage`, max 1280px / JPEG q0.7) antes de virar base64. Limite 8 MB por anexo. Anexos guardados inline como base64 dentro da própria entrada.
- **Botão "Diário" no popup do dia**: trocou o antigo "Anexar" (que mandava pra biblioteca compartilhada). Agora navega pra aba Diário e abre o formulário com a data pré-preenchida.
- **Privacidade por design**: entradas do diário NÃO disparam push, NÃO entram na biblioteca/Mem Palace, NÃO são listadas pra outros usuários.
- **Limitação conhecida (a evoluir)**: POST envia a lista inteira a cada save. Tudo bem por enquanto (limite Flask 80 MB), mas pra diários grandes (50+ entradas com fotos) vai ficar lento. Próxima iteração: paginação + endpoint incremental.

## Escala pra 500 usuários (v3.2 — abr/2026)

Preparativos pra suportar a entrada de 400 novos usuários (~500 ativos):

### 1. Pool de conexões no Postgres (`kvstore.py`)
- Antes: cada operação abria/fechava conexão nova com o banco (overhead grande, risco de estourar `max_connections`).
- Agora: **`ThreadedConnectionPool`** do psycopg2, com 2 conexões aquecidas (`KV_POOL_MIN`) e até 20 simultâneas (`KV_POOL_MAX`). Reuso transparente via context manager `_connect()`.
- Comportamento herdado do `with psycopg2.connect()` preservado: commit automático ao sair sem erro, rollback em exceção.

### 2. Anexos do Diário no Object Storage (`object_storage.py`)
- Antes: fotos do diário gravadas como base64 dentro do Postgres → inflava o banco rapidamente (1 entrada com 5 fotos ~750 KB).
- Agora: imagens vão pro **Replit Object Storage** (bucket `replit-objstore-67bb6851-...`); o Postgres guarda só metadados leves (`{key, nome, mimetype, size}`) — redução de ~99,96% no tamanho da entrada.
- Convenção de chave: `diario/<matricula>/<entry_id>/<idx>_<nome_seguro>`.
- Endpoint `GET /api/diario/anexo?key=<key>&t=<token>` serve o binário com checagem de propriedade (impede um usuário acessar foto de outro). Cache de 1 hora no navegador (`Cache-Control: private, max-age=3600`).
- Fallback de auth via query param `?t=<token>` (necessário porque `<img src>` e downloads não permitem header `Authorization`). Implementado em `auth.py:get_token_from_request()`.
- Limpeza automática: ao excluir uma entrada, os anexos correspondentes são removidos do Object Storage (sem lixo acumulado).

### 3. Push notifications em paralelo (`server.py`)
- Antes: `send_push_to_users` iterava sequencialmente — 500 usuários x ~100 ms FCM/APNs = ~50 segundos travando.
- Agora: **`ThreadPoolExecutor`** com 20 workers (`PUSH_FANOUT_WORKERS`), inicializado lazily. Para listas pequenas (≤2 destinatários), pula o pool pra evitar overhead.
- Benchmark com 500 usuários simulados (latência 100 ms): 50,1 s → 2,5 s (**~20× mais rápido**).

### Variáveis de ambiente novas
- `KV_POOL_MIN` (default 2), `KV_POOL_MAX` (default 20)
- `PUSH_FANOUT_WORKERS` (default 20)
- `DEFAULT_OBJECT_STORAGE_BUCKET_ID` (configurada automaticamente pelo blueprint)

### Hardening pós code-review (2 rodadas)
1. **Pool aguenta restart do Postgres**: `_connect()` captura `InterfaceError`/`OperationalError`, descarta a conexão morta com `putconn(close=True)`. Próxima request pega uma fresca, sem cair tudo.
2. **Pool não estoura sob concorrência alta**: `BoundedSemaphore(_POOL_MAX)` na frente do `getconn()` — quando 100 threads pedem com pool=20, 20 entram e 80 *esperam* (até `KV_POOL_ACQUIRE_TIMEOUT=10s`) ao invés de levar `PoolError` na cara. Validado: 100 saves paralelos em 1 s, 100/100 OK.
3. **Saves do diário sem corrida e sem segurar conexão durante IO**: `kvstore.with_lock(<chave>)` usa `pg_advisory_xact_lock` e *cede* a conexão. O `diario_save` faz uploads ao Object Storage **fora** do lock (FASE 1), entra no lock só pro read-modify-write (FASE 2), e limpa órfãos depois (FASE 3). `kvstore.load`/`save` aceitam `conn=...` pra reusar a do lock — gasta 1 conexão por save, não 3.
4. **Token na query string**: `Referrer-Policy: same-origin` aplicado globalmente via `@app.after_request` — token de auth nunca vai no header `Referer` de site externo.
5. **Streaming de download**: a lib `replit.object_storage` só oferece `download_as_bytes` (sem stream nativo). Mitigado pelo cap de 8 MB por anexo + cache de 1 h no navegador.

## v3.4 — Reorganização do menu (2026-04-28)

**Mudanças de UX:**
- Removidos do menu lateral: "Meus Eventos" e "Diário de Bordo".
- Esses dois fluxos passaram a ser acessados **só pelo modal de clique no dia** (4 botões em grid 2x2):
  1. 📢 Mural (post público pra turma)
  2. 🔒 Meus Eventos (evento privado naquela data)
  3. 📓 Diário (entrada de diário daquela data)
  4. 📝 Nota (lembrete rápido)
- O modal de dia agora também **lista as entradas de Diário** existentes naquele dia (com preview de texto, contagem de anexos e botão de excluir), além das que já mostrava (Mural, Meus Eventos privados, Notas).
- O botão Diário no modal **não navega mais** pra `setSection("diario")` — abre direto o formulário de criação. Mesmo padrão pra Meus Eventos.
- As funções `renderPessoais` e `renderDiario` continuam intactas no código (acessíveis via `S.section`), mas sem entrada no menu.

**Menu lateral agora**: Calendário, Mural da Turma, Chat, Acervo, Configurações, Manual (PDF), Ativar notificações, Prontos.

## v3.6 — Viriato menos preguiçoso (2026-04-29)

**Problema reportado:** Viriato dizia "você não me ensinou" mesmo tendo fatos relacionados na memória; quando insistido, dava resposta parcial e ficava pedindo mais detalhes em vez de usar o que sabia.

**Correções:**
1. **`instrucoes_viriato.md` §3.5** — substituída a regra "diga não sei" por uma instrução explícita: varrer TODAS as fontes (memória pessoal, fatos, biblioteca, manual) procurando sinônimos antes de qualquer "não sei"; compartilhar primeiro tudo que sabe; só depois perguntar a peça específica que falta. **PROIBIDO** dizer "você não me ensinou" se houver qualquer fato relacionado.
2. **`server.py` `KEYWORDS_CRITICAS`** — adicionados ~50 termos do vocabulário operacional da Turma A (separação, corte, recepção, despacho, formação, classificação, pera, viradores, granel, pier, TFPM, minério, GDU, lote, estacionamento, ACT, PLR, embarque, descarga, circulação etc). Agora perguntas do dia-a-dia disparam o Modo Deliberativo (carrega regras técnicas + anti-padrões).
3. **`buscar_fatos`** — top_k subiu de 4→12 (no call site `/api/claude`); adicionada tabela `_SINONIMOS_BUSCA` aplicada na expansão de tokens (ex.: "separação" também busca "corte"/"despacho"; "minério" também busca "GDT"/"vagão"; "recepção" também busca "VV01-VV06"). Isso amplia o recall sem precisar de embeddings.

**Refinamentos pós-revisão (mesmo dia):**
- **`KEYWORDS_CRITICAS` enxutas:** removidos termos genéricos do PT-BR que disparariam Modo Deliberativo em conversa não-técnica (`vale`, `baixo`, `cima`, `partida(s)`, `chegada(s)`, `carga`, `descarga`, `embarque`, `desembarque`, `trem(s)`, `mineiro(s)`). Ex.: "Pode me lembrar da partida do jogo?" não vira mais pergunta crítica.
- **Sinônimos só na query:** a expansão de `_SINONIMOS_BUSCA` agora é aplicada **só do lado da query**, não do lado dos fatos. Evita falso positivo do tipo: fato sobre "corte de madeira" casando com pergunta sobre "separação de trem" porque ambos seriam expandidos para o mesmo conjunto.
- **Limiar mínimo de score 1.0** em `buscar_fatos`: matches de só-substring (score 0.5) eram ruído — agora exige pelo menos um token-match real ou substring forte (>=1.5).
