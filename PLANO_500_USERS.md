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

#### ETAPA 3 — Cache de busca semântica COM invalidação

**Objetivo:** evitar reembedar queries repetidas, mas garantir que escrita no MemPalace invalida o cache (regra "MemPalace lembra do que acabei de te contar").

- [ ] Em `server.py`, completar `_busca_cache_set` (já tem `_busca_cache={}`, lock e `_busca_cache_get`): gravar `{ts, result}` com TTL 300s
- [ ] Mudar a chave do cache para `(matricula, hash(query))` — NÃO compartilhar cache entre usuários
- [ ] Adicionar `_busca_cache_invalidar(matricula)`: limpa entradas dessa matrícula
- [ ] Plugar invalidação em TODA escrita do MemPalace: `palace_add`, `palace_update`, `palace_delete`, qualquer rota que muda `kvstore`
- [ ] Plugar `_busca_cache_get`/`_busca_cache_set` dentro de `busca_semantica` (antes de chamar `_embed_text`)
- [ ] Aceite: query repetida pelo mesmo user em < 5min vai pro cache; após `palace_add`, próxima busca do mesmo user vai pro DB

---

#### ETAPA 4 — Ativar `_get_user_ala()` nos callsites (multi-turma)

**Objetivo:** Item E da Fase 3 está implementado estruturalmente mas NÃO plugado nas rotas. Sem isso o app continua tratando todo mundo como Turma A.

- [ ] Identificar todos os callsites que hoje assumem `'A'` hardcoded (grep `'A'` em rotas que filtram por turma)
- [ ] Substituir por `_get_user_ala(matricula)` em cada rota
- [ ] Validar que admin (Angelo, 497444) continua vendo todas as turmas
- [ ] Aceite: usuário de outra turma futura vê só os próprios eventos; admin vê tudo

---

#### ETAPA 5 — Observabilidade + smoke test final

**Objetivo:** garantir que dá pra ver o que tá acontecendo sob carga e validar o conjunto.

- [ ] Expor `_palace_metrics` em `/api/admin/metrics` (já existe parcialmente em `/api/palace/status`) — incluir: `cache_hits`, `timeouts`, `buscas_total`, `kvstore_pool_em_uso`, `kvstore_pool_max`
- [ ] Adicionar contador de hits/misses do cache de busca (ETAPA 3) nas mesmas métricas
- [ ] Smoke test: `curl` em loop em `/`, `/api/auth/me`, `/api/chat/conversas` (com If-None-Match), `/api/admin/metrics` por 5 min, capturar p50/p95
- [ ] Architect review focado em ETAPA 3 e 4
- [ ] Aceite: review PASS, métricas reportando, p95 estável

---

## Observações finais

- **REGRA-MÃE:** só aditivo. Nunca remover funcionalidade existente sem confirmação do dono (Angelo, 497444).
- **Não tocar `.replit` direto** — usar `deployConfig` no code execution.
- **Em dúvida, perguntar antes** de mexer em código de produção.
