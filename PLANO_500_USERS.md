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
