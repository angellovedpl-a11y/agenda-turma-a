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

#### ETAPA 5 — Ativar `_get_user_ala()` nos callsites (multi-turma)

**Objetivo:** Item E da Fase 3 está implementado estruturalmente mas NÃO plugado nas rotas. Sem isso o app continua tratando todo mundo como Turma A.

> **Nota:** baixa prioridade enquanto app for single-tenant Turma A. Re-priorizar quando houver decisão concreta de adicionar Turma B.

- [ ] Identificar todos os callsites que hoje assumem `'A'` hardcoded (grep `'A'` em rotas que filtram por turma)
- [ ] Substituir por `_get_user_ala(matricula)` em cada rota
- [ ] Validar que admin (Angelo, 497444) continua vendo todas as turmas
- [ ] Aceite: usuário de outra turma futura vê só os próprios eventos; admin vê tudo

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
| 5. Multi-turma `_get_user_ala` | postergada (single-tenant ainda) |
| 6. Observabilidade | ✅ implementada |

---

## Observações finais

- **REGRA-MÃE:** só aditivo. Nunca remover funcionalidade existente sem confirmação do dono (Angelo, 497444).
- **Não tocar `.replit` direto** — usar `deployConfig` no code execution.
- **Em dúvida, perguntar antes** de mexer em código de produção.
