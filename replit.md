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

## v3.5 — FASE 1 MemPalace (palácio de memória, em andamento) (2026-04-29)

**Regra-mãe da fase**: nada de busca, system prompt, rotas ou comportamento do Viriato foi alterado. Tudo aditivo.

**Item 1 — campos `ala`/`sala` em regras técnicas (`server.py:496`)**
- `regras_tecnicas_add(regra)` aceita 2 campos novos opcionais no dict: `ala` (contexto/turma) e `sala` (tema operacional).
- Sanitização: lowercase + trim + max 60 chars + default `"geral"` se vazio.
- Persistidos no dict da regra ao lado de `conceito`, `regra_de_ouro`, etc.

**Item 2 — campos `ala`/`sala` em fatos da turma (`server.py:462`)**
- `fatos_add(texto, matricula, nome, ala='geral', sala='geral')` aceita 2 params nomeados opcionais no fim da assinatura.
- Mesma sanitização do item 1. Os 4 callers existentes (chamada com 3 args posicionais) caem nos defaults — comportamento inalterado.

**Item 3 — busca prioriza por `ala`/`sala` sem descartar nada (`server.py:541-610` e `737-765`)**
- Helpers aditivos: `_coletar_salas_conhecidas`, `_detectar_salas_na_query`, `_palacio_bonus`.
- `buscar_regras_tecnicas` e `buscar_fatos` ganharam dois params opcionais: `ala_user=None` e `query_para_sala=None`.
- Quando ambos são `None`, ou quando nada bate, o bonus de cada item é 0 → ordenação **idêntica** à anterior (validado em teste com 3 fatos).
- Score de prioridade aditivo:
  - `+2.0` se `item.sala` está nas salas detectadas na query
  - `+1.0` se `item.ala == ala_user`
  - `+0.5` se `item.ala == "geral"` (fallback genérico)
- "Salas detectadas" = nomes de `sala` conhecidos (excluindo `"geral"`) que aparecem como substring na `query_para_sala` (case-insensitive, com `_` ↔ espaço).
- **Nada é descartado**: items de outras alas/salas continuam no resultado, só ficam mais embaixo.
- Call sites (`server.py:1178` e `1216`) passam `query_para_sala=ultima` → bullet 1 ATIVO.
- `ala_user` deixado como `None` nos callers → bullet 2 DORMENTE até definição do mapeamento matrícula→turma (não há campo `turma` no perfil hoje; o app é "Agenda Turma A" então a Turma A é implícita por design — aguardando decisão do dono se ativar `ala_user="turma_a"` por default ou se adicionar campo explícito no perfil).

**Item 4 — parser do marcador `[SALVAR_REGRA ...]` aceita `ala`/`sala` (`server.py:1442-1490`)**
- A regex original (`conceito | regra | borda? | peso? | fonte?`) ganhou "slots" `_slot_extras = (?:\s*\|\s*(?:ala|sala)\s*=\s*"...")*` entre cada par de campos. Os 5 grupos originais (1-5) **não foram renumerados** — código que usa `m.group(1..5)` continua intacto.
- Slot restrito a `ala|sala` (em vez de `\w+`) pra evitar consumo acidental do campo `fonte=` (tentativa anterior com `\w+` quebrou o grupo 5 — corrigido).
- Sintaxe livre: `ala="..."` e `sala="..."` podem aparecer em **qualquer posição** entre `regra` e `]`.
- Extração via regex auxiliar `extras_palacio_rg` aplicada em `m.group(0)` (string completa do marcador). Sanitização: lowercase + trim + max 60 chars + default `"geral"`.
- Suite de 8 testes validada: marcador antigo (compat), exemplo do dono, ordem trocada, só ala, case misto, marcador mínimo, ala/sala depois de fonte, multi-marcadores.
- ⚠️ DORMENTE até decisão do dono: o **system prompt do Viriato NÃO foi alterado** (a regra principal proíbe). Hoje o Viriato emite marcadores sem `ala`/`sala` → caem nos defaults. O parser está pronto pra receber, basta uma fase futura instruir o Viriato.

## v3.5 — FASE 2 MemPalace (busca semântica via pgvector) (2026-04-29)

**Regra-mãe mantida**: nada existente foi alterado. Adições puras + hooks tolerantes a falha (try/except em torno do call assíncrono → save NUNCA quebra por falha de embedding).

**Schema (DB dev — PROD AINDA NÃO TEM)**
- `CREATE EXTENSION IF NOT EXISTS vector;`
- Tabela `palace_embeddings(id text PK, tipo text, ala text, sala text, conteudo text, embedding vector(256), criado_em timestamptz)` com índices em `ala`, `sala`, `tipo`.
- Estado prod (29/abr/2026): **PENDENTE** — health check é tolerante (retorna False silencioso, fluxo segue como Fase 1). Antes do próximo deploy: rodar o SQL acima manualmente no banco prod.

**Caminho de embedding**
- Anthropic SDK não expõe `.embeddings` na versão instalada → fallback.
- OpenAI key ausente (e mesmo se houver, `text-embedding-3-small` produz 1536d → incompatível com `vector(256)`).
- **Fallback ativo**: TF-IDF caseiro 256d (md5 hashing 2 buckets/token, sinal pseudo-aleatório, normalização L2). Usa só stdlib. Determinístico, sem custo de API.
- Limitação conhecida: cos similarity entre sinônimos diretos fica ~0.5–0.6, abaixo do threshold 0.70 da spec → bloco `[mem]` aparece pouco na prática. Sem regressão (cai pra busca por keywords da Fase 1).

**Funções aditivas (`server.py:612-810`)**
- `_palace_health_check()` cacheia tri-state (None/True/False) com Lock.
- `gerar_embedding(texto)` → 256d, nunca lança.
- `_embed_to_pg(vec)` → literal `'[v1,v2,...]'` aceito por `vector(N)` no SQL puro (não depende do pacote `pgvector` Python, que está bloqueado por PEP 668).
- `_indexar_no_palace(id, tipo, ala, sala, conteudo)` → `INSERT ... ON CONFLICT (id) DO UPDATE`.
- `_indexar_async(...)` → dispara em `Thread(daemon=True)` (não bloqueia o caller).
- `busca_semantica(query, ala=None, sala=None, n=5)` → SQL com `1 - (embedding <=> %s::vector) AS score`, ORDER BY score DESC.

**Hooks (apenas duas chamadas, ambas em try/except silencioso)**
- `fatos_add` (~linha 480): após `kvstore.save`, `_indexar_async(id, 'fato', ala, sala, texto)`.
- `regras_tecnicas_add` (~linha 536): após save, `_indexar_async(id, 'regra', ala, sala, conceito+regra+borda)`.

**Integração no system prompt do Viriato (`server.py:1376-1426`)**
- Antes da montagem dos blocos de contexto: `mem_semantica = busca_semantica(ultima, sala=detectada, n=5)` → filtra por `score >= 0.70` (`mem_alta`).
- Dedup: ids semânticos saem de `fatos_relev` (atenção: regras_relev NÃO é deduplicada — pode duplicar se a mesma regra entrar via [mem] e via keyword; ruído de prompt, não regressão).
- Bloco novo entre MEMORIA PESSOAL e FATOS APRENDIDOS:
  ```
  ### MEMPALACE — ITENS SEMANTICAMENTE RELEVANTES ###
  [mem] (fato, score=0.72): conteúdo até 500 chars
  ### FIM MEMPALACE ###
  ```

**Rota nova: `GET /api/palace/status` (`server.py:2502`)** — *não estava na spec original; criada sob demanda*
- `@auth.require_auth` (qualquer usuário aprovado pode ver — só agregados, sem dados sensíveis).
- Retorna: `pgvector_extension`, `tabela_exists`, `health_check_ok`, `total_itens`, `por_tipo`, `por_ala_top`, `por_sala_top`, `mais_recente`, `threshold_busca` (0.7), `embed_dim` (256), `embedding_engine` (`tfidf_hashing_md5`).
- Tolerante a erro: nunca lança; em falha popula `info['erro']`.

**Hardening pós code-review (aplicado na mesma sessão)**

| Achado | Status | Solução |
|---|---|---|
| **J (severo)** órfãos após `_remove` | ✅ corrigido | `_indexar_remove(id)` submetido ao pool dispara `DELETE FROM palace_embeddings WHERE id = %s OR id = %s` (apaga formato novo prefixado E formato legado, por idempotência). Hook em `fatos_remove` e `regras_tecnicas_remove` em try/except silencioso. |
| **F (médio)** colisão de id `int(time()*1000)` | ✅ corrigido | Id no palace agora é prefixado (`'fato:<id>'`, `'regra:<id>'`). Ids principais em `fatos_load`/`regras_tecnicas_load` permanecem `int` — só a chave da `palace_embeddings` muda. |
| **A (médio)** threads daemon sem limite | ✅ corrigido | `_get_palace_executor()` lazy → `ThreadPoolExecutor(max_workers=PALACE_INDEX_WORKERS)`, default 4 workers. Reaproveitado por `_indexar_async` e `_indexar_remove`. Mesmo padrão do `_get_push_executor`. |
| **C (baixo)** dedup só em fatos | ✅ corrigido junto | Ids semânticos agora separados por tipo (`ids_sem_fatos`, `ids_sem_regras`) e cada conjunto deduplica seu lado. `regras_relev` também filtrada. |
| **B (operacional)** cache de health grudado | aceito | Deploy é controlado e a tabela é criada antes via script SQL; se acontecer, basta restart dos workers. Não exposto reload por enquanto. |
| **D (baixo)** threshold alto pro TF-IDF | aceito | Observabilidade fica pra próxima fase; sem impacto correcional. |
| **E (futuro)** sem filtro por ala | postergado | Mapeamento matrícula→turma ainda indefinido; vira risco só quando houver multi-turma. |

**Dedup com prefixos no system prompt (`server.py:~1442`)**
- `ids_sem_fatos = {id.split(':',1)[-1] for m in mem_alta if m['tipo']=='fato'}` (idem `ids_sem_regras`).
- `.split(':',1)[-1]` tolera entradas legadas sem prefixo (caso já existam embeddings antigos sem prefixar — backward-compat).

**Variável de ambiente nova**
- `PALACE_INDEX_WORKERS` (default 4) — tamanho do pool de threads de indexação.

**Script SQL pra prod**
- `migrations/fase2_palace_embeddings.sql` — idempotente (`CREATE EXTENSION IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`). Inclui validação pós-execução e instruções pra ativar índice ANN (HNSW/IVFFlat) caso a tabela passe de ~10k linhas no futuro.

**Item 5 (Fase 1) — `instrucoes_viriato.md` documenta a sintaxe nova (`instrucoes_viriato.md:151-186`)**
- Atualizado APENAS a seção 6 (Sintaxe SALVAR_REGRA), de forma puramente aditiva:
  - Sintaxe formal (linha 161) ganhou `| ala="<contexto, opcional>" | sala="<tema, opcional>"` no fim.
  - Adicionado um segundo bloco de exemplo (linhas 169-172) com o caso "Separação VV" usando `ala`/`sala`. O exemplo original da pressão de alívio L201 continua intacto.
  - Adicionado bullet final na lista "Regras" explicando: opcionais, default `"geral"`, max 60 chars, snake_case, valores típicos pra `ala` (turma_a/turma_b/geral) e `sala` (patio_recepcao/freios/act_vale/escala/seguranca), e quando omitir.
- Esse arquivo é carregado em `server.py:1256` e injetado no system prompt do Viriato. A atualização foi tratada como **documentação aditiva** (descreve params que o item 4 já implementou), não como mudança de comportamento — Viriato continua sem obrigação de emitir esses params, eles são opcionais.

---

## FASE 3 — Escalabilidade pra 500 usuários simultâneos (29/04/2026)

Tudo aditivo. Sem regressão na Fase 1/2. Endereça gargalos detectados pra carga real de prod.

**Bloco A — Gunicorn gthread + keep-alive** (`.replit` via deployConfig)
- `--worker-class=gthread --threads=8 --keep-alive=5` adicionados.
- Mantidos `--workers=2 --timeout=120 --bind=0.0.0.0:5000`.
- Antes (sync, 2 workers): só 2 requests simultâneos. Agora (gthread 2x8): 16 requests simultâneos sem aumentar memória.
- `--keep-alive=5` reaproveita conexões TCP do polling do app (chat 15s, presença, badges).

**Bloco B — ETag + cache curto em `/api/chat/conversas`** (`server.py:2434`)
- Cache module-level `_chat_conversas_cache: {matricula -> (expires_at, payload, etag)}` com `_threading.Lock()`.
- TTL `CHAT_CONVERSAS_CACHE_TTL` (default 5s). Polling de 15s/user × 500 users = 33 req/s; com TTL 5s, ~95% das chamadas viram lookup em dict.
- ETag = `md5(json.dumps(payload, sort_keys=True))[:16]`. Suporte a `If-None-Match` retorna `304 Not Modified` sem body.
- Helper `_chat_conversas_cache_invalidar(matriculas=None)` definido em `server.py:2421` mas **NÃO plugado ainda** nos endpoints de mutação (envio de mensagem, criação de conversa, marcação de lida). Defasagem real máxima = TTL 5s, aceitável dado que polling roda a 15s. Plug nos handlers de mutação fica como follow-up se a defasagem virar reclamação real de UX.

**Bloco C — Pool kvstore 20 → 32** (`kvstore.py`)
- `_POOL_MAX` default `20 → 32`. Tunável via `KV_POOL_MAX`.
- Cálculo de capacidade: `2 workers × 32 conexões = 64`, ainda bem abaixo do limite ~100 do Postgres do Replit.

**Bloco D — MemPalace busca semântica blindada** (`server.py:833+`)
- Cache LRU `_embed_para_busca` (`maxsize=128`, query truncada em 500 chars). Mesma query digitada por N users vira 1 hash TF-IDF em vez de N.
- Pool dedicado `_palace_busca_executor` (`PALACE_BUSCA_WORKERS=2`), separado do pool de indexação.
- Timeout `PALACE_BUSCA_TIMEOUT` (default 0.8s) via `Future.result(timeout=...)`. Em timeout: fallback silencioso `[]` + métrica + log `[fase3]`.
- **Anti-backlog (fix do code review):** `BoundedSemaphore(workers*2 = 4)`. Como `Future.result(timeout=...)` só desiste do caller — a thread continua executando — sem isso a fila do executor cresceria sem limite sob carga + palace lento. Calls que excedem o limite caem em `[]` imediatamente e incrementam `rejeitadas_backlog`. Wrapper `_busca_semantica_release` garante que o semaphore libera quando a thread termina (não quando o caller desiste).
- Métricas `_palace_metrics = {buscas_total, cache_hits, timeouts, fallback_silencioso, rejeitadas_backlog}` com lock próprio.
- `/api/palace/status` ganhou campos: `busca_timeout_s`, `metrics`, `embed_cache` (cache_info do LRU).

**Bloco E — Multi-turma estruturado mas não ativado** (`server.py:925+`)
- `_get_user_ala(matricula)` retorna sempre `'turma_a'` por enquanto (single-tenant). `_USER_ALA_MAP` vazio.
- Função existe pra centralizar o mapeamento; **callsites plugados via interruptor seguro** — ver Bloco H abaixo. Sem flag ativa, comportamento idêntico ao single-tenant atual.

**Bloco H — Multi-turma com interruptor seguro** (`server.py`, ETAPA 5; 30/04/2026)
- **Contexto:** Item E da Fase 3 estava só estrutural; ETAPA 5 plugou nos callsites pra preparar Turma B/C/D (~500 users serão pra todas juntas). Não dava pra plugar diretamente: dados antigos têm `ala='geral'`, filtrar por `'turma_a'` apagaria a memória do palace pra todo mundo em prod.
- **Estratégia:** código entra **dormente** no deploy. Comportamento atual (single-tenant Turma A, sem filtro) preservado até o admin (1) rodar backfill, (2) ativar flag.
- **Tabela `user_ala_map`** (`matricula TEXT PRIMARY KEY, ala TEXT, atualizado_em BIGINT, atualizado_por TEXT`) — padrão TEXT consistente com `kv_store`/`ratelimit_buckets`. Criada no import via `_init_user_ala_table()`. `_USER_ALA_MAP` carregado em RAM com `_USER_ALA_MAP_LOCK` (RLock) **+ TTL 30s** (`_USER_ALA_MAP_TS`/`_USER_ALA_MAP_TTL`): `_get_user_ala()` faz lazy reload se cache > TTL. Garante propagação cross-worker de upserts em ≤30s sem broadcast (fix architect).
- **Flag `_multi_turma_ativo`** em `kv_store`. Cache local 30s pra evitar query a cada chat (hot path). `_multi_turma_invalidar_cache()` força releitura. **FAIL-CLOSED (fix architect):** em erro de DB com cache já preenchido, PRESERVA o último valor conhecido (mesmo expirado) — se a flag estava `True`, o filtro de turmas continua ativo durante a falha do DB; jamais cai pra `False` (que seria fail-open vazando dados). Só defaulta `False` no cold start (cache nunca preenchido).
- **Funções intermediárias `_ala_for_query`/`_ala_for_save`** decidem por flag: sem flag → `None`/`'geral'` (comportamento atual). Com flag → `_get_user_ala(matricula)`. Plugadas em `fatos_add`, `regras_tecnicas_add`, `buscar_fatos`, `busca_semantica`, `buscar_regras_tecnicas`.
- **Filtro por ala em `buscar_fatos`/`buscar_regras_tecnicas`** (fix architect): quando `ala_user` definido (flag ativa), descarta itens de outras turmas no loop de scoring. Quando `ala_user=None` (flag desativada), filtro NÃO executa — comportamento atual preservado. Sem isso, busca por palavras-chave vazaria dados entre turmas mesmo com flag ativa.
- **Backfill `_backfill_ala_geral_to_turma_a(force=False)`** — idempotente: flag em `kv_store['_backfill_ala_geral_to_turma_a_v1']` + `pg_advisory_xact_lock` via `kvstore.with_lock` (serializa os 2 workers). Migra 3 lugares: `palace_embeddings` (UPDATE), `fatos_turma`, `regras_tecnicas` (load+modify+save). **Atomicidade (fix architect):** só marca `done=True` se TODAS as 3 seções completaram sem erro; se alguma falhar, retorna `ok=False, erros=[...]` e flag NÃO é marcada — próxima chamada re-executa do início. **`raise_on_error=True`** em todos `kvstore.load/save` do backfill + checagem de retorno do `save` (que default retorna `False` em erro silencioso) — garante que erros de DB propaguem como exceção em vez de virarem "n=0 OK" e marcarem done indevidamente. Itens legados sem campo `ala` são tratados como `'geral'`.
- **Endpoints admin (`@auth.require_admin`):**
  - CRUD do mapeamento: `GET/POST /api/admin/user-ala`, `DELETE /api/admin/user-ala/<matricula>`.
  - Operacionais: `GET /api/admin/multi-turma/status`, `POST /api/admin/multi-turma/backfill` (`{force?}`), `POST /api/admin/multi-turma/ativar` (`{ativo}`).
  - **Proteção:** ativar com flag=true retorna `409 backfill_pendente` se backfill não rodou.
- **Procedimento ops em prod:** (1) deploy → (2) backfill via endpoint → (3) cadastrar matrículas da Turma B/C/D via POST → (4) ativar flag → (5) esperar 30-60s pro cache propagar entre workers.
- **Reverter:** `POST /api/admin/multi-turma/ativar {ativo: false}`. Dados continuam migrados (`turma_a`), mas o WHERE não filtra mais — comportamento atual restaurado.

**Bloco G — Observabilidade unificada** (`/api/admin/metrics` + getters em 3 módulos)
- Endpoint **`GET /api/admin/metrics`** (`@auth.require_admin`) agrega métricas dos 4 subsistemas em 1 JSON. Cada bloco em try/except → subsistema quebrado não derruba o resto.
- `ratelimit.get_metrics()` → `requests_total`, `blocked_total`, `failopens_total`, `enabled`, `cleanup_every`, `cleanup_keep_min`.
- `kvstore.get_pool_stats()` → introspeção tolerante de `ThreadedConnectionPool._used/_pool` e `BoundedSemaphore._value`: `pool_min`, `pool_max`, `em_uso`, `livres_no_pool`, `semaphore_disponivel`, `semaphore_em_espera`.
- `_chat_cache_metrics` (process-local) → `hits`, `misses`, `not_modified_304`, `tamanho_atual`, `ttl_s`, `hit_ratio`.
- `_palace_metrics` (já existente) + `_embed_para_busca.cache_info()` (LRU do Bloco D).
- Top-level: `uptime_s` (`_PROCESS_STARTED_AT`), `worker_pid` (distingue workers gunicorn).
- **Métricas são process-local**: não agregadas entre os 2 workers gunicorn. Trade-off consciente — agregar custaria round-trip extra por request crítico; pra trend monitoring de degradação 1 worker basta. Admin pode chamar 2x e somar pra número absoluto.

**Bloco F — Rate limiting por matrícula** (`ratelimit.py` novo + 3 edits `server.py`)
- Storage compartilhado em **Postgres** (tabela própria `ratelimit_buckets` com PK composta `(matricula, rota, bucket_min)`) — limite preciso entre os 2 workers gunicorn (in-memory daria 2x sub-ótimo).
- Atômico: `INSERT ... ON CONFLICT DO UPDATE ... RETURNING count` (1 round-trip por request limitado).
- Janela fixa de 1 min. Cleanup probabilístico (1 a cada 500 requests, remove > 10 min) → sem cron.
- **FAIL-OPEN:** qualquer erro do banco → `(allowed=True)`. Rate limiter NUNCA derruba o app (antipadrão clássico).
- Decorator `@ratelimit.rate_limit(N, env_var=..., route_key=...)` aplicado DEPOIS de `@auth.require_auth`.
- 429 com `Retry-After` + `X-RateLimit-*` headers + corpo JSON em PT-BR coloquial.
- Kill switch operacional: `RATELIMIT_ENABLED=0` desliga tudo.
- Limites aplicados: `/api/claude` (Viriato) **20/min/matrícula** (`RATELIMIT_CLAUDE_PER_MIN`); `/api/chat/conversas` (polling) **120/min/matrícula** (`RATELIMIT_CHAT_CONVERSAS_PER_MIN`).

**Bloco I — Extração de PDF página-por-página + OCR seletivo** (`server.py:1405+`; 30/04/2026)
- **Sintoma:** dono reportou "Viriato disse que dados extraídos do PDF estavam incompletos". Causa raiz: `extrair_texto_arquivo` chamava pdfplumber página por página e pulava as vazias **sem aviso**. Fallback OCR só disparava se TODO o PDF tivesse < 200 chars. PDFs mistos (ex.: 40 páginas digitais + 10 scans/imagens) extraíam só os 30k chars das digitais → texto > 200 → OCR full não disparava → as 10 páginas-imagem eram **silenciosamente perdidas**, e o item buscado pelo Viriato sumia.
- **Fix 1 — detecção página-por-página:** `extrair_texto_arquivo` agora marca como falha qualquer página cujo `extract_text().strip()` < 50 chars (limiar empírico pra detectar imagem/scan vs cabeçalho real). Acumula `paginas_falhas: list[int]` (0-based). Texto extraído ganha marcadores `--- Pagina N ---` (debug + contexto pro Claude).
- **Fix 2 — OCR seletivo (`_ocr_pdf_paginas_especificas`):** se `paginas_falhas` mas texto digital > 200, dispara OCR **só nas páginas faltantes** via Vision. Páginas digitais ficam intactas (sem custo OCR). Retorno do upload concatena texto digital + bloco `--- Paginas extraidas via OCR (eram imagens/scan no PDF original) ---`.
- **Fix 3 — runs contíguos no OCR seletivo (fix architect):** páginas falhas esparsas (ex. `[1, 200]`) **não** convertem o range inteiro `min..max` via Poppler. Algoritmo agrupa em runs contíguos e faz 1 chamada `convert_from_bytes` por run. Ex.: `[0,1,2,199,200]` → 2 chamadas (1-3 e 200-201) renderizando 5 páginas em vez de 201.
- **Fix 4 — rotulagem correta de batches não-contíguos (fix architect):** `_ocr_imagens_via_vision` recebe `numeros_pagina: list[int]` (1-based) e detecta se o batch é contíguo. Contíguo: prompt usa "numerando a partir de N". Não-contíguo (ex.: páginas 2 e 10 num mesmo batch): prompt lista explicitamente "estas páginas correspondem aos números: 2, 10" pra evitar Claude rotular como 2 e 3.
- **Fix 5 — preservação do fallback OCR full quando pdfplumber falha (fix architect):** condição do cenário 1 voltou a ser `len(texto_pdf.strip()) < 200` (antes incluía `and n_paginas_total > 0`, regressão funcional — se `pdfplumber.open()` lançasse exceção, `n_paginas_total=0` impedia o OCR full mesmo quando `pdf2image` ainda conseguiria renderizar).
- **Fix 6 — `top_k` no Viriato 6 → 10** (`server.py:1874`): PDFs grandes podem ter o item buscado num chunk com score moderado. 10 trechos cabem no contexto sem inflar custo.
- **Fix 7 — `max_pages` do OCR full 80 → 200**: PDFs ferroviários longos cabem dentro do limite Vision.
- **Aditividade total:** PDF 100% digital → comportamento idêntico (só ganha marcadores `--- Pagina N ---`). PDF 100% scan → continua usando OCR full. PDF misto → cenário NOVO recupera as páginas-imagem antes silenciosamente perdidas.
- **Custo:** OCR seletivo cap em `max_paginas_ocr=80` páginas/PDF (proteção contra PDF onde 200 páginas são imagens — cairia no cenário scan completo). Cada batch = 4 páginas em 1 chamada Haiku (mesmo padrão do OCR full).
- **Validação:** smoke test em 3 cenários — PDF digital normal preserva extração + ganhou marcadores; PDF misto detecta página falha e dispara OCR seletivo só nela; PDF totalmente em branco mantém OCR full. Architect review PASS.

**Variáveis de ambiente novas (todas com default sensato)**
- `PALACE_BUSCA_TIMEOUT=0.8` — timeout em segundos pra busca semântica
- `PALACE_BUSCA_WORKERS=2` — workers do pool de busca (semaphore in-flight = workers*2)
- `RATELIMIT_ENABLED=1` — kill switch global (0 desliga rate limit)
- `RATELIMIT_CLAUDE_PER_MIN=20` — limite Viriato por matrícula
- `RATELIMIT_CHAT_CONVERSAS_PER_MIN=120` — limite polling de conversas
- `RATELIMIT_CLEANUP_EVERY=500` — frequência do cleanup probabilístico
- `RATELIMIT_CLEANUP_KEEP_MIN=10` — minutos de histórico mantidos na tabela
- `CHAT_CONVERSAS_CACHE_TTL=5` — TTL em segundos do cache de `/api/chat/conversas`
- `KV_POOL_MAX=32` — tamanho do pool de conexões Postgres do kvstore

**Smoke tests aplicados**
- ETag ciclo completo: 200 + ETag → 304 com If-None-Match → 200 do cache (mesmo ETag).
- Cache LRU registra hit em query repetida; métrica `cache_hits` incrementa.
- Timeout forçado (0.0001s) cai em fallback silencioso, métrica `timeouts` incrementa.
- Anti-backlog: 8 chamadas concorrentes com palace lento (sleep 2s) → 4 entram no executor, 4 caem em `rejeitadas_backlog`; depois das zumbis terminarem o semaphore volta a 4/4.
- `/api/palace/status` mostra todos os campos novos.
- Boot ok: `[kvstore] pool criado (min=2, max=32)`, `/api/auth/me 200`, `/api/chat/conversas 200`.

## Filtro de tipos no calendário (29/04/2026)

A legenda de cores dos eventos no calendário mensal virou também um filtro interativo.

- `S.evFilter` (array de chaves de `EVENTO_TIPOS`) é persistido em `localStorage` junto com o resto do estado da agenda. Vazio = mostrar todos os tipos.
- Helpers em `index.html`: `passaFiltroEv(e)`, `toggleEvFilter(t)`, `clearEvFilter()`.
- Cada chip da legenda (`.cal-legend-item.legend-btn`) é um `<button>` com `data-tipo` que alterna o filtro. Tipos selecionados ficam realçados; os não selecionados ficam esmaecidos quando há filtro ativo.
- Botão "Limpar filtro" aparece no cabeçalho da legenda quando há tipos selecionados.
- Ao ativar um filtro a legenda é forçada a abrir (`setLegendOpen(true)`) e o botão `?` ganha o ponto verde indicador (`.btn-legend.has-filter`).
- O filtro também é aplicado em `openDia(k)`: tanto a lista do mural quanto a lista de eventos pessoais filtram por `passaFiltroEv`. Um banner mostra os tipos ativos e oferece um botão "Limpar" inline.
- Notas e entradas do diário **não** são filtradas — o filtro é só de tipos de evento.
