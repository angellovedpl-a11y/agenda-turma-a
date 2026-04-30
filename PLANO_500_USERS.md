# Plano de Migração para 500 Users — Agenda Turma A

> **LEIA ESTE ARQUIVO PRIMEIRO** se você é um agente novo ou perdeu contexto.
> Marque cada etapa com ✅ quando concluída. Nunca pule uma etapa sem marcar.

---

## Contexto do Projeto

- **App:** Agenda Turma A (PWA para ferroviários da Vale/STEFEM — Escala 2x2)
- **URL:** https://agenda-turma-a.replit.app
- **Stack atual:** Flask + Python, single-file `index.html` (HTML+CSS+JS), PostgreSQL (produção), localStorage (client)
- **Assistente:** "Viriato" — chatbot com Palácio de Memória (busca semântica com embeddings)
- **Infraestrutura:** Replit Reserved VM (0.5 vCPU / 2 GiB RAM) — South America

---

## Meta

Suportar **500 usuários simultâneos** com boa performance, mantendo todas as funcionalidades existentes.

---

## STATUS ATUAL DAS TAREFAS

### ✅ Já implementado (não refazer)

- [x] Fase 1: Cache LRU de embeddings (`_embed_para_busca` com `@lru_cache(maxsize=128)`)
- [x] Fase 2: BoundedSemaphore para limitar buscas in-flight (`_palace_busca_inflight`)
- [x] Fase 3: ThreadPoolExecutor dedicado com timeout 800ms + métricas (`_palace_metrics`)
- [x] Banco de dados PostgreSQL de produção conectado
- [x] Tarefa #14: Filtro de calendário por tipo de evento (aguardando "Apply changes")

### 🔲 Pendente — executar nesta ordem

#### ETAPA 1 — Aplicar tarefa #14 (filtro calendário)

- [ ] Clicar em "Apply changes to main version" na tarefa #14 no painel do Replit Agent
- [ ] Verificar que o deploy foi bem-sucedido

> **Nota:** Tarefa #14 já foi mergeada automaticamente em `53fb78d`. Esta ETAPA está obsoleta — marcar como `[x]` na próxima revisão.

---

#### ETAPA 2 — Verificar/otimizar config Gunicorn em produção

**Objetivo:** confirmar que a config atual aguenta 500 users e ajustar o que faltar. **NÃO trocar para gevent** — ver nota abaixo.

- [x] Bloco A já em prod: `--workers=2 --worker-class=gthread --threads=8 --keep-alive=5 --timeout=120` (checkpoint `aca180e8`)
- [ ] Validar sob carga real: capturar p50/p95/p99 de `/api/chat/conversas` e `/api/auth/me` com 100+ usuários ativos
- [ ] Se p95 > 1s consistente: aumentar `--threads` de 8 para 16 (testar primeiro em staging)
- [ ] Se memória passar de 1.4 GiB sustentado: reduzir `--threads` para 6 e adicionar `--max-requests=1000 --max-requests-jitter=100` (recicla worker pra evitar leak)
- [ ] Adicionar `--access-logfile=- --error-logfile=- --log-level=info` se ainda não estiver capturando logs

> **Por que NÃO gevent:** gevent exige `monkey.patch_all()` no topo de `server.py`, o que quebra o `ThreadPoolExecutor` dedicado do MemPalace, o `BoundedSemaphore`, o pool threaded do `kvstore.py` e o `concurrent.futures` usado no timeout de 800ms. Toda a Fase 3 foi desenhada para gthread (threading nativo). Migrar para gevent agora seria regressão de 4 blocos já validados em produção.

---

#### ETAPA 3 — Cache de RESULTADO de busca semântica ❌ DESCARTADA

**Status:** avaliada em 2026-04-29 e **descartada por ganho marginal**.

**Premissa errada da versão anterior deste plano:** dizia "completar `_busca_cache_set` (já existe `_busca_cache={}`, lock e `_busca_cache_get`)". Verificado em `server.py` — esses helpers **não existem**. O que existe é:

- `_chat_conversas_cache` (linha 2479) → cache da rota `/api/chat/conversas` (Bloco B), outra coisa
- `_embed_para_busca` com `@lru_cache(maxsize=128)` (linha 854) → cacheia o **embedding** da query, não o resultado

**Por que descartar:**

1. **Ganho marginal:** o custo pesado da `busca_semantica` é o hash TF-IDF do embedding, e isso **já está cacheado** (`_embed_para_busca` lru_cache 128). A query SQL em `pgvector` com `LIMIT 5` é tipicamente <100ms.
2. **Risco de regressão:** invalidação correta exige plugar em 6 rotas de escrita (`/api/memoria/pessoal` POST/DELETE, `/api/memoria/fato` POST/DELETE, `/api/admin/memoria/pendentes/<id>/aprovar`, `/api/admin/memoria/pendentes/<id>/negar`). Esquecer uma = "MemPalace esqueceu o que você acabou de contar" — quebra de regra-mãe.
3. **Anti-backlog já existe:** `_palace_busca_inflight` (`BoundedSemaphore`) + timeout 800ms já blindam o caller contra picos.

**Conclusão:** Fase 3 Bloco D já cobre o hot path. Reabrir só se métricas reais (ETAPA 5) mostrarem que `busca_semantica` virou gargalo p95.

---

#### ETAPA 4 — Rate limiting por matrícula via Postgres ✅ IMPLEMENTADA

**Objetivo:** proteger o app de cliente bugado / bot / pico repentino sem bloquear usuário legítimo. Storage Postgres = limite preciso entre os 2 workers gunicorn (in-memory teria 2x sub-ótimo).

**Implementação (módulo `ratelimit.py` novo + 3 edits em `server.py`):**

- [x] Tabela `ratelimit_buckets(matricula, rota, bucket_min, count, PK composta)` — janela fixa de 1 minuto
- [x] `check_and_increment` atômico via `INSERT ... ON CONFLICT DO UPDATE ... RETURNING count` (1 round-trip)
- [x] **FAIL-OPEN:** qualquer erro do banco retorna `(allowed=True)` — rate limiter nunca derruba o app
- [x] Cleanup probabilístico (1 a cada `RATELIMIT_CLEANUP_EVERY=500` requests, remove buckets > 10 min) — sem cron
- [x] Decorator `@ratelimit.rate_limit(N, env_var=..., route_key=...)` aplicado **depois** de `@auth.require_auth`
- [x] Resposta 429 com headers `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining` + corpo JSON em PT-BR coloquial
- [x] Kill switch operacional: `RATELIMIT_ENABLED=0` desliga tudo

**Limites aplicados:**

| Rota | Limite/min/matrícula | Var de env |
|---|---|---|
| `POST /api/claude` (Viriato chatbot) | **20** | `RATELIMIT_CLAUDE_PER_MIN` |
| `GET /api/chat/conversas` (polling) | **120** | `RATELIMIT_CHAT_CONVERSAS_PER_MIN` |

**Justificativa dos números:**
- Viriato 20/min: chat humano não digita 20 perguntas em 1 min. Acima disso é bot/bug. Protege orçamento Anthropic.
- Polling 120/min: cliente faz 4 req/min (15s) — margem de 30x cobre múltiplas abas + retry burst.

**Fora do escopo desta ETAPA:** rate limit em `/api/auth/login` (anti-brute-force por IP) — vira ETAPA 4b se virar problema.

**Vars de env novas:**
- `RATELIMIT_ENABLED` (default `1`) — kill switch
- `RATELIMIT_CLAUDE_PER_MIN` (default 20)
- `RATELIMIT_CHAT_CONVERSAS_PER_MIN` (default 120)
- `RATELIMIT_CLEANUP_EVERY` (default 500) — frequência do cleanup
- `RATELIMIT_CLEANUP_KEEP_MIN` (default 10) — minutos de histórico mantidos

**Aceite:**
- 21ª chamada na mesma minute window em `/api/claude` retorna `429` com `Retry-After` ✅ validado
- Banco fora → fail-open (request passa, log warning) — não derruba app

**Limitação conhecida (janela fixa):**
- Algoritmo de janela fixa de 1 min permite **burst de até 2x** no boundary entre minutos (ex: 20 chamadas no segundo 59 + 20 chamadas no segundo 0 = 40 em 2s, ainda dentro do limite de cada minuto). Aceito como trade-off de simplicidade. Migrar para sliding window só se métricas reais (ETAPA 6) mostrarem abuso no boundary.

**Hardening pós architect review:**
- Parser seguro de env vars (`_parse_int_env`) com fallback + clamp `>= 1` — evita `ZeroDivisionError` em `RATELIMIT_CLEANUP_EVERY=0` (que viraria fail-open global silencioso) e `ValueError` no import com valor não-numérico.
- Contador de fail-opens com log amostrado (1ª ocorrência + a cada `RATELIMIT_FAILOPEN_LOG_EVERY=100`) — torna "limiter inoperante" detectável sem floodar logs.

---

#### ETAPA 5 — Multi-turma plugado com interruptor seguro ✅ IMPLEMENTADA

**Objetivo:** preparar a estrutura pra Turma B/C/D (decisão concreta tomada em 30/04/2026 — os 500 users vão ser pra todas as turmas juntas), SEM quebrar a memória dos ~500 usuários atuais que estão indexados com `ala='geral'`.

**Estratégia central — código entra DORMENTE no deploy:**
- Comportamento idêntico ao atual até o admin (1) rodar o backfill, (2) ativar a flag explicitamente.
- Sem flag ativa: `_ala_for_query()=None` (busca vê tudo, igual hoje) e `_ala_for_save()='geral'` (default histórico preservado).
- Com flag ativa: `_ala_for_query/save = _get_user_ala(matricula)` filtra por turma.
- Cache local 30s da flag pra não bater no DB a cada chat (hot path).

**Implementação (1 arquivo, server.py, tudo aditivo):**
- [x] **Tabela `user_ala_map`** (TEXT PK, padrão consistente com `kv_store`/`ratelimit_buckets`): `matricula TEXT PRIMARY KEY, ala TEXT, atualizado_em BIGINT, atualizado_por TEXT`. Criada via `_init_user_ala_table()` no import.
- [x] **`_USER_ALA_MAP` carregado** da tabela no startup via `_load_user_ala_map_from_db()` + `_USER_ALA_MAP_LOCK` (RLock thread-safe). Recarregado após cada upsert/delete **+ TTL 30s com lazy reload em `_get_user_ala()`** (fix architect: garante propagação cross-worker dos upserts em ≤30s sem broadcast).
- [x] **`_multi_turma_ativo()`** lê flag de `kv_store['_multi_turma_ativo']`, cache 30s. **FAIL-CLOSED (fix architect):** em erro de DB, PRESERVA o último valor conhecido (mesmo se cache expirou). Caso contrário, falha transitória do DB poderia virar fail-open: flag estava `True`, DB cai por 5min → função retornaria `False` → `_ala_for_query` retornaria `None` → busca não filtraria → vazamento entre turmas. Só defaulta `False` no cold start (cache nunca preenchido).
- [x] **`_ala_for_query(matricula)`** e **`_ala_for_save(matricula)`** — funções intermediárias que respeitam a flag. Plugadas em `fatos_add()`, `regras_tecnicas_add()`, `buscar_fatos()`, `busca_semantica()`, `buscar_regras_tecnicas()` no fluxo do Viriato.
- [x] **Filtro por ala dentro de `buscar_fatos`/`buscar_regras_tecnicas`** (fix architect): `if ala_user and (item.get('ala') or 'geral') != ala_user: continue` no início do loop de scoring. Sem isso, busca por palavras-chave vazaria dados entre turmas mesmo com flag ativa (`busca_semantica` já filtrava no SQL, mas keyword search ficou pendente).
- [x] **`_backfill_ala_geral_to_turma_a(force=False)`** — idempotente via flag `_backfill_ala_geral_to_turma_a_v1` em kv_store + `pg_advisory_xact_lock` (`kvstore.with_lock`) pra serializar entre os 2 workers gunicorn. Backfilla 3 lugares: `palace_embeddings` (UPDATE direto), `fatos_turma` (load+modify+save), `regras_tecnicas` (load+modify+save). Não toca `pendentes_memoria` (não tem coluna `ala`). **Atomicidade (fix architect):** só marca `done=True` se TODAS as 3 seções completaram sem erro; se alguma falhar, retorna `ok=False, erros=[...]` SEM marcar flag — próxima chamada re-executa. **Erros silenciosos (fix architect):** `kvstore.load/save` chamados com `raise_on_error=True` + checagem do retorno de `save` (que default vira `False` em erro) — sem isso, um erro real do DB viraria silenciosamente "n=0 OK" e marcaria done sem ter migrado nada. Tolera legado sem campo `ala` (trata como `'geral'`).

**Endpoints admin novos (todos `@auth.require_admin`):**
- `GET /api/admin/user-ala` — lista mapeamentos
- `POST /api/admin/user-ala` body `{matricula, ala}` — upsert
- `DELETE /api/admin/user-ala/<matricula>` — remove (cai pro default `'turma_a'`)
- `GET /api/admin/multi-turma/status` — `{ativo, backfill_done, mapeamentos_count, contadores}`
- `POST /api/admin/multi-turma/backfill` body opcional `{force: true}` — roda backfill
- `POST /api/admin/multi-turma/ativar` body `{ativo: true|false}` — liga/desliga flag. **PROTEÇÃO:** `ativo=true` retorna `409 backfill_pendente` se backfill ainda não rodou (evita matar memória de todos os usuários por descuido).

**Procedimento operacional pra ativar multi-turma em prod (Angelo):**
1. Deploy do código (zero impacto — flag desativada por default).
2. `POST /api/admin/multi-turma/backfill` (uma vez). Resposta traz contadores. Se vier `ok=False, erros=[...]`, investiga e re-roda (não marca done). Confirmar `ok=True` antes de seguir.
3. **Pra cada** matrícula da Turma B/C/D (cadastrar TODAS antes do passo 4): `POST /api/admin/user-ala {matricula, ala: 'turma_b'}`. Importante: cadastrar antes de ativar evita que durante a janela de propagação (até 30s entre workers) usuários da Turma B sejam tratados como `turma_a` por default.
4. `POST /api/admin/multi-turma/ativar {ativo: true}`. Cache local 30s pode demorar pra propagar entre os 2 workers — esperar 30-60s antes de validar.
5. Pra reverter: `POST /api/admin/multi-turma/ativar {ativo: false}` (volta ao comportamento atual; `palace_embeddings` continua com `ala='turma_a'` mas o WHERE não filtra).

**Janela de propagação cross-worker (consciente):**
- Flag `_multi_turma_ativo`: até 30s entre os 2 workers gunicorn (cache TTL).
- Mapeamentos `_USER_ALA_MAP`: até 30s (lazy reload no `_get_user_ala`).
- Durante a janela, **um** worker pode estar com comportamento antigo enquanto o outro já filtra. **Mitigação operacional:** sempre cadastrar matrículas ANTES de ativar a flag (passo 3 antes do 4), e esperar 30-60s após ativar antes de testar.
- Trade-off consciente: alternativa seria broadcast cross-worker (Postgres NOTIFY/LISTEN), o que adiciona complexidade pra ganho marginal num app que ativa a flag <1x por mês.

**Aceite (validado em dev):**
- [x] App sobe sem regressão: GET `/` → 200, todos endpoints atuais OK
- [x] Tabela `user_ala_map` criada no startup
- [x] `_USER_ALA_MAP` carregado (0 mapeamentos em dev, vazio = OK)
- [x] 6 endpoints admin retornam 401 sem auth
- [x] Backfill 1ª chamada: `ok=True`. 2ª chamada: `skipped: 'ja executado'`. 3ª com `force=True`: re-executa. (Idempotência OK)
- [x] Sem flag: `_ala_for_query=None`, `_ala_for_save='geral'` (comportamento atual preservado)
- [x] Com flag: `_ala_for_query='turma_a'`, `_ala_for_save='turma_a'` (multi-turma ativa)
- [x] `_multi_turma_invalidar_cache()` força releitura imediata após toggle
- [x] **Filtro keyword (fix architect):** `buscar_fatos('pneu', ala_user=None)` retorna 3 fatos (mistos), `ala_user='turma_a'` retorna só 2, `ala_user='turma_b'` retorna só 1. Sem `ala_user`, comportamento idêntico ao anterior. Mesmo aceite pra `buscar_regras_tecnicas`.
- [x] **TTL cross-worker (fix architect):** `_get_user_ala` faz lazy reload quando `_USER_ALA_MAP_TS` > TTL. Cache fresco preservado dentro do TTL. Após TTL expira, próxima chamada recarrega.
- [x] **Atomicidade backfill (fix architect):** com erro forçado em uma seção (`fatos_turma: boom-simulado`), retorna `ok=False, erros=[...]` e flag NÃO é marcada como done. Próxima chamada re-executa.
- [x] **Flag fail-CLOSED (fix architect 2):** com cache `True` conhecido + DB caindo, `_multi_turma_ativo()` retorna `True` (preserva último valor), NÃO `False` (que seria fail-open). Cold start com DB caído defaulta `False`.
- [x] **Erro silencioso de save (fix architect 2):** `kvstore.save` retornando `False` em fatos_turma é capturado (`save retornou False`), retorna `ok=False`, flag NÃO marcada como done.

---

#### ETAPA 6 — Observabilidade ✅ IMPLEMENTADA

**Objetivo:** dar visibilidade do estado do app sob carga sem reagir-no-escuro quando algo degradar.

**Implementação (4 arquivos, tudo aditivo):**

- [x] `ratelimit.py`: contadores `requests_total`, `blocked_total`, `failopens_total` (já existia) + função `get_metrics()` — process-local, com lock próprio
- [x] `kvstore.py`: `get_pool_stats()` introspeção tolerante do `ThreadedConnectionPool` + `BoundedSemaphore` (`em_uso`, `livres_no_pool`, `semaphore_disponivel`, `semaphore_em_espera`) — fail-soft se atributos privados mudarem em update da lib
- [x] `server.py`: contadores `_chat_cache_metrics` (`hits`, `misses`, `not_modified_304`) plugados no handler de `/api/chat/conversas`
- [x] `server.py`: endpoint **`GET /api/admin/metrics`** (`@auth.require_admin`) agrega tudo em 1 JSON; cada bloco em try/except (subsistema quebrado não derruba o resto)
- [x] `server.py`: `_PROCESS_STARTED_AT = time.time()` + `uptime_s` no payload; `worker_pid` pra distinguir entre os 2 workers gunicorn
- [x] `_embed_para_busca.cache_info()` (LRU do Bloco D) exposto em `palace.embed_cache`

**Shape do payload `/api/admin/metrics`:**
```json
{
  "uptime_s": 1234.5,
  "kvstore": {"pool_min": 2, "pool_max": 32, "em_uso": 3, "livres_no_pool": 5, "semaphore_disponivel": 29},
  "ratelimit": {"requests_total": N, "blocked_total": M, "failopens_total": K, "enabled": true, "cleanup_every": 500, "cleanup_keep_min": 10},
  "palace": {"buscas_total": ..., "cache_hits": ..., "timeouts": ..., "fallback_silencioso": ..., "rejeitadas_backlog": ..., "embed_cache": {"hits":..., "misses":..., "maxsize":128, "currsize":...}},
  "chat_conversas_cache": {"hits": ..., "misses": ..., "not_modified_304": ..., "tamanho_atual": ..., "ttl_s": 5, "hit_ratio": 0.95},
  "worker_pid": 42
}
```

**Decisão consciente:** métricas são **process-local** (não agregadas entre os 2 workers). Razão: agregar via storage compartilhado custaria 1 round-trip extra por request crítico; pra trend monitoring de "tá estável ou tá degradando?" 1 worker já dá o sinal. Admin pode chamar 2x e somar se quiser número absoluto.

**Smoke test "5 min de loop com p50/p95":** **descartado** como verificação automática nesta sessão. Motivo: ambiente de dev tem 1 usuário e zero carga real — números seriam ruído. P50/p95 reais virão da prod com 500 users e do próprio `/api/admin/metrics` no painel admin (próxima fase de UI).

**Aceite (validado):**
- [x] App sobe sem regressão: GET `/` → 200, endpoints normais OK
- [x] `/api/admin/metrics` requer admin: sem auth retorna 401
- [x] `ratelimit.get_metrics()` e `kvstore.get_pool_stats()` retornam shapes esperados
- [x] Contadores incrementam (validado por testes diretos)

---

## Estado final do PLANO_500_USERS.md

| ETAPA | Status |
|---|---|
| 1. Tarefa #14 obsoleta | obsoleta |
| 2. gunicorn validar | ok (já estava) |
| 3. cache busca semântica | descartada (ganho marginal) |
| 4. Rate limiting | ✅ implementada + architect PASS |
| 5. Multi-turma `_get_user_ala` | ✅ implementada (interruptor seguro, código dormente até admin ativar) |
| 6. Observabilidade | ✅ implementada |

---

## Observações finais

- **REGRA-MÃE:** só aditivo. Nunca remover funcionalidade existente sem confirmação do dono (Angelo, 497444).
- **Não tocar `.replit` direto** — usar `deployConfig` no code execution.
- **Em dúvida, perguntar antes** de mexer em código de produção.
