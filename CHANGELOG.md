# Changelog — Agenda Turma A

Historico detalhado de versoes. Movido do `replit.md` em 2026-05-23.

---

## Diario de Bordo (privado, v3.0)

Aba **Diario de Bordo** no menu lateral, entre "Meus Eventos" e "Chat Turma".
- **Backend** (`server.py`): helpers `diario_load/save` + endpoints `GET/POST /api/diario` (auth obrigatorio). Armazenado em `kvstore` na chave `diario:<matricula>` — escopo individual, sem broadcast.
- **Frontend** (`index.html`): `renderDiario(c)` lista entradas ordenadas por data desc, com texto + thumbs de anexos (clicar abre fullscreen). Botao "Excluir" por entrada.
- **Nova entrada** (`openDiarioForm(dataPre)`): date picker, textarea, 3 botoes — Camera (`capture="environment"`), Galeria (multi), Arquivo (.pdf, .txt, .doc, .docx). Imagens sao comprimidas client-side via canvas (`_compressImage`, max 1280px / JPEG q0.7) antes de virar base64. Limite 8 MB por anexo. Anexos guardados inline como base64 dentro da propria entrada.
- **Botao "Diario" no popup do dia**: trocou o antigo "Anexar" (que mandava pra biblioteca compartilhada). Agora navega pra aba Diario e abre o formulario com a data pre-preenchida.
- **Privacidade por design**: entradas do diario NAO disparam push, NAO entram na biblioteca/Mem Palace, NAO sao listadas pra outros usuarios.
- **Limitacao conhecida (a evoluir)**: POST envia a lista inteira a cada save. Tudo bem por enquanto (limite Flask 80 MB), mas pra diarios grandes (50+ entradas com fotos) vai ficar lento. Proxima iteracao: paginacao + endpoint incremental.

## Escala pra 500 usuarios (v3.2 — abr/2026)

Preparativos pra suportar a entrada de 400 novos usuarios (~500 ativos):

### 1. Pool de conexoes no Postgres (`kvstore.py`)
- Antes: cada operacao abria/fechava conexao nova com o banco (overhead grande, risco de estourar `max_connections`).
- Agora: **`ThreadedConnectionPool`** do psycopg2, com 2 conexoes aquecidas (`KV_POOL_MIN`) e ate 20 simultaneas (`KV_POOL_MAX`). Reuso transparente via context manager `_connect()`.
- Comportamento herdado do `with psycopg2.connect()` preservado: commit automatico ao sair sem erro, rollback em excecao.

### 2. Anexos do Diario no Object Storage (`object_storage.py`)
- Antes: fotos do diario gravadas como base64 dentro do Postgres — inflava o banco rapidamente (1 entrada com 5 fotos ~750 KB).
- Agora: imagens vao pro **Replit Object Storage** (bucket `replit-objstore-67bb6851-...`); o Postgres guarda so metadados leves (`{key, nome, mimetype, size}`) — reducao de ~99,96% no tamanho da entrada.
- Convencao de chave: `diario/<matricula>/<entry_id>/<idx>_<nome_seguro>`.
- Endpoint `GET /api/diario/anexo?key=<key>&t=<token>` serve o binario com checagem de propriedade (impede um usuario acessar foto de outro). Cache de 1 hora no navegador (`Cache-Control: private, max-age=3600`).
- Fallback de auth via query param `?t=<token>` (necessario porque `<img src>` e downloads nao permitem header `Authorization`). Implementado em `auth.py:get_token_from_request()`.
- Limpeza automatica: ao excluir uma entrada, os anexos correspondentes sao removidos do Object Storage (sem lixo acumulado).

### 3. Push notifications em paralelo (`server.py`)
- Antes: `send_push_to_users` iterava sequencialmente — 500 usuarios x ~100 ms FCM/APNs = ~50 segundos travando.
- Agora: **`ThreadPoolExecutor`** com 20 workers (`PUSH_FANOUT_WORKERS`), inicializado lazily. Para listas pequenas (<=2 destinatarios), pula o pool pra evitar overhead.
- Benchmark com 500 usuarios simulados (latencia 100 ms): 50,1 s -> 2,5 s (**~20x mais rapido**).

### Hardening pos code-review (2 rodadas)
1. **Pool aguenta restart do Postgres**: `_connect()` captura `InterfaceError`/`OperationalError`, descarta a conexao morta com `putconn(close=True)`. Proxima request pega uma fresca, sem cair tudo.
2. **Pool nao estoura sob concorrencia alta**: `BoundedSemaphore(_POOL_MAX)` na frente do `getconn()` — quando 100 threads pedem com pool=20, 20 entram e 80 *esperam* (ate `KV_POOL_ACQUIRE_TIMEOUT=10s`) ao inves de levar `PoolError` na cara. Validado: 100 saves paralelos em 1 s, 100/100 OK.
3. **Saves do diario sem corrida e sem segurar conexao durante IO**: `kvstore.with_lock(<chave>)` usa `pg_advisory_xact_lock` e *cede* a conexao. O `diario_save` faz uploads ao Object Storage **fora** do lock (FASE 1), entra no lock so pro read-modify-write (FASE 2), e limpa orfaos depois (FASE 3). `kvstore.load`/`save` aceitam `conn=...` pra reusar a do lock — gasta 1 conexao por save, nao 3.
4. **Token na query string**: `Referrer-Policy: same-origin` aplicado globalmente via `@app.after_request` — token de auth nunca vai no header `Referer` de site externo.
5. **Streaming de download**: a lib `replit.object_storage` so oferece `download_as_bytes` (sem stream nativo). Mitigado pelo cap de 8 MB por anexo + cache de 1 h no navegador.

## v3.4 — Reorganizacao do menu (2026-04-28)

**Mudancas de UX:**
- Removidos do menu lateral: "Meus Eventos" e "Diario de Bordo".
- Esses dois fluxos passaram a ser acessados **so pelo modal de clique no dia** (4 botoes em grid 2x2):
  1. Mural (post publico pra turma)
  2. Meus Eventos (evento privado naquela data)
  3. Diario (entrada de diario daquela data)
  4. Nota (lembrete rapido)
- O modal de dia agora tambem **lista as entradas de Diario** existentes naquele dia (com preview de texto, contagem de anexos e botao de excluir), alem das que ja mostrava (Mural, Meus Eventos privados, Notas).
- O botao Diario no modal **nao navega mais** pra `setSection("diario")` — abre direto o formulario de criacao. Mesmo padrao pra Meus Eventos.
- As funcoes `renderPessoais` e `renderDiario` continuam intactas no codigo (acessiveis via `S.section`), mas sem entrada no menu.

**Menu lateral agora**: Calendario, Mural da Turma, Chat, Acervo, Configuracoes, Manual (PDF), Ativar notificacoes, Prontos.

## v3.5 — FASE 1 MemPalace (palacio de memoria) (2026-04-29)

**Regra-mae da fase**: nada de busca, system prompt, rotas ou comportamento do Viriato foi alterado. Tudo aditivo.

**Item 1 — campos `ala`/`sala` em regras tecnicas (`server.py:496`)**
- `regras_tecnicas_add(regra)` aceita 2 campos novos opcionais no dict: `ala` (contexto/turma) e `sala` (tema operacional).
- Sanitizacao: lowercase + trim + max 60 chars + default `"geral"` se vazio.
- Persistidos no dict da regra ao lado de `conceito`, `regra_de_ouro`, etc.

**Item 2 — campos `ala`/`sala` em fatos da turma (`server.py:462`)**
- `fatos_add(texto, matricula, nome, ala='geral', sala='geral')` aceita 2 params nomeados opcionais no fim da assinatura.
- Mesma sanitizacao do item 1. Os 4 callers existentes (chamada com 3 args posicionais) caem nos defaults — comportamento inalterado.

**Item 3 — busca prioriza por `ala`/`sala` sem descartar nada (`server.py:541-610` e `737-765`)**
- Helpers aditivos: `_coletar_salas_conhecidas`, `_detectar_salas_na_query`, `_palacio_bonus`.
- `buscar_regras_tecnicas` e `buscar_fatos` ganharam dois params opcionais: `ala_user=None` e `query_para_sala=None`.
- Quando ambos sao `None`, ou quando nada bate, o bonus de cada item e 0 — ordenacao **identica** a anterior.
- Score de prioridade aditivo: `+2.0` sala detectada na query, `+1.0` ala do user, `+0.5` ala geral (fallback).
- **Nada e descartado**: items de outras alas/salas continuam no resultado, so ficam mais embaixo.

**Item 4 — parser do marcador `[SALVAR_REGRA ...]` aceita `ala`/`sala` (`server.py:1442-1490`)**
- Regex ganhou "slots" `_slot_extras` entre cada par de campos. Os 5 grupos originais (1-5) **nao foram renumerados**.
- Extracao via regex auxiliar `extras_palacio_rg` aplicada em `m.group(0)`.
- DORMENTE ate decisao do dono: o **system prompt do Viriato NAO foi alterado**.

## v3.5 — FASE 2 MemPalace (busca semantica via pgvector) (2026-04-29)

**Regra-mae mantida**: nada existente foi alterado. Adicoes puras + hooks tolerantes a falha.

**Schema (DB)**
- `CREATE EXTENSION IF NOT EXISTS vector;`
- Tabela `palace_embeddings(id text PK, tipo text, ala text, sala text, conteudo text, embedding vector(256), criado_em timestamptz)` com indices em `ala`, `sala`, `tipo`.

**Caminho de embedding**
- **Fallback ativo**: TF-IDF caseiro 256d (md5 hashing 2 buckets/token, sinal pseudo-aleatorio, normalizacao L2). Usa so stdlib. Deterministico, sem custo de API.
- Limitacao conhecida: cos similarity entre sinonimos diretos fica ~0.5-0.6, abaixo do threshold 0.70.

**Funcoes aditivas (`server.py:612-810`)**
- `_palace_health_check()`, `gerar_embedding(texto)`, `_embed_to_pg(vec)`, `_indexar_no_palace(...)`, `_indexar_async(...)`, `busca_semantica(query, ala, sala, n)`.

**Integracao no system prompt do Viriato**
- `mem_semantica = busca_semantica(ultima, sala=detectada, n=5)` — filtra por `score >= 0.70` (`mem_alta`).
- Dedup: ids semanticos saem de `fatos_relev` e `regras_relev`.
- Bloco novo `### MEMPALACE — ITENS SEMANTICAMENTE RELEVANTES ###` entre MEMORIA PESSOAL e FATOS APRENDIDOS.

**Rota: `GET /api/palace/status`** — retorna estado do pgvector, metricas, contagens.

**Hardening pos code-review**
- Orfaos apos `_remove` corrigido. Colisao de id prefixada (`fato:<id>`, `regra:<id>`). Threads daemon limitadas por `ThreadPoolExecutor(PALACE_INDEX_WORKERS=4)`. Dedup separada por tipo.

**Script SQL pra prod:** `migrations/fase2_palace_embeddings.sql` — idempotente.

## FASE 3 — Escalabilidade pra 500 usuarios simultaneos (29/04/2026)

Tudo aditivo. Sem regressao na Fase 1/2. Endereca gargalos detectados pra carga real de prod.

**Bloco A — Gunicorn gthread + keep-alive** (`.replit` via deployConfig)
- `--worker-class=gthread --threads=8 --keep-alive=5` adicionados.
- 2x8 = 16 requests simultaneos sem aumentar memoria.

**Bloco B — ETag + cache curto em `/api/chat/conversas`**
- Cache module-level com TTL 5s. Suporte a `If-None-Match` retorna `304`.
- Invalidacao (`_chat_conversas_cache_invalidar`) definida mas NAO plugada nos endpoints de mutacao.

**Bloco C — Pool kvstore 20 -> 32**

**Bloco D — MemPalace busca semantica blindada**
- Cache LRU `_embed_para_busca` (maxsize=128). Pool dedicado `_palace_busca_executor` (2 workers).
- Timeout 0.8s via `Future.result(timeout=...)`. Anti-backlog com `BoundedSemaphore`.
- Metricas `_palace_metrics` expostas em `/api/palace/status`.

**Bloco E — Multi-turma estruturado mas nao ativado**
- `_get_user_ala(matricula)` retorna sempre `'turma_a'`.

**Bloco H — Multi-turma com interruptor seguro** (ETAPA 5; 30/04/2026)
- Flag `_multi_turma_ativo` em `kv_store`. Cache local 30s. FAIL-CLOSED.
- Funcoes `_ala_for_query`/`_ala_for_save`. Backfill idempotente.
- Endpoints admin: CRUD mapeamento, status, backfill, ativar/desativar.
- **DORMENTE** ate decisao do dono.

**Bloco G — Observabilidade unificada** (`/api/admin/metrics`)
- Agrega metricas dos 4 subsistemas. Metricas sao process-local.

**Bloco F — Rate limiting por matricula** (`ratelimit.py`)
- Storage em Postgres. Atomico. Janela fixa 1 min. Cleanup probabilistico.
- FAIL-OPEN. Kill switch `RATELIMIT_ENABLED=0`.
- Limites: Viriato 20/min, polling conversas 120/min.

**Bloco I — Extracao de PDF pagina-por-pagina + OCR seletivo**
- Fix para PDFs mistos (digital + scan). OCR seletivo so nas paginas faltantes.
- Runs contiguos, rotulagem correta de batches nao-contiguos, top_k 6->10, max_pages 80->200.

### Hotfixes

**gunicorn `--preload` + `PYTHONUNBUFFERED=1`** (30/04/2026)
- Boot timeout em Reserved VM resolvido com `--preload`.

**SSL "bad record mac"** (`gunicorn.conf.py`; 01/05/2026)
- Pool DB compartilhado entre workers via fork. Fix: `post_fork` hook reseta pool.

**Login fantasma** (`kvstore.py` + `auth.py`; 01/05/2026)
- TCP keepalives no pool DB. Retry automatico em `load()`/`save()`. Login distingue 503 de 401.

**Tema claro — backgrounds escuros** (`index.html`; 30/04/2026)
- Overrides CSS pra modo claro. Inline styles refatorados pra usar variaveis do tema.

**Upload de PDF grande** (`.replit` + `server.py`; 30/04/2026)
- Timeout 120 -> 600s. Logs de timing no upload.

## Filtro de tipos no calendario (29/04/2026)

- `S.evFilter` persistido em `localStorage`. Helpers: `passaFiltroEv`, `toggleEvFilter`, `clearEvFilter`.
- Chips da legenda alternam filtro. Botao "Limpar filtro" quando ha tipos selecionados.
- Filtro aplicado no mural e no popup do dia. Notas e diario NAO filtrados.

## Variaveis de ambiente (referencia completa)

| Variavel | Default | Descricao |
|---|---|---|
| `KV_POOL_MIN` | 2 | Conexoes aquecidas do pool DB |
| `KV_POOL_MAX` | 32 | Max conexoes simultaneas |
| `PUSH_FANOUT_WORKERS` | 20 | Workers de push em paralelo |
| `PALACE_INDEX_WORKERS` | 4 | Workers de indexacao palace |
| `PALACE_BUSCA_WORKERS` | 2 | Workers de busca semantica |
| `PALACE_BUSCA_TIMEOUT` | 0.8 | Timeout busca semantica (s) |
| `RATELIMIT_ENABLED` | 1 | Kill switch rate limit |
| `RATELIMIT_CLAUDE_PER_MIN` | 20 | Limite Viriato/min/matricula |
| `RATELIMIT_CHAT_CONVERSAS_PER_MIN` | 120 | Limite polling conversas |
| `RATELIMIT_CLEANUP_EVERY` | 500 | Frequencia cleanup rate limit |
| `RATELIMIT_CLEANUP_KEEP_MIN` | 10 | Minutos de historico mantidos |
| `CHAT_CONVERSAS_CACHE_TTL` | 5 | TTL cache conversas (s) |
| `VAPID_PUBLIC_KEY` | — | Chave publica VAPID (push) |
| `VAPID_PRIVATE_KEY` | — | Chave privada VAPID (push) |
| `VAPID_SUBJECT` | — | Subject VAPID (email) |
