# Agenda Turma A — Escala Ferroviaria 2x2

PWA para ferroviarios da Vale (Turma A) gerenciarem escalas 2x2, documentos, eventos e comunicacao interna.

## Stack

- **Backend:** Flask + Python 3.11 + PostgreSQL (Replit Reserved VM)
- **Frontend:** PWA — `index.html` + `static/style.css` + `static/app.js`
- **IA:** Claude Haiku 4.5 via Anthropic (chatbot Viriato)
- **Embeddings:** voyage-4-large (1024d) + TF-IDF 256d fallback
- **DB vetorial:** pgvector em `palace_embeddings`
- **Deploy:** gunicorn gthread 2x8 com `--preload` + `gunicorn.conf.py` (post_fork reseta pool DB)
- **Storage:** Replit Object Storage (anexos diario), Postgres kvstore (tudo mais)

## Funcionalidades

- Calculadora de escala 2x2 (2026-2030)
- Calendario com filtro de tipos de evento (mural + pessoais)
- Chatbot Viriato com memoria persistente (MemPalace), busca semantica, modo deliberativo
- Biblioteca/Acervo de PDFs com OCR via Vision (PDFs mistos digital+scan)
- Diario de Bordo privado com anexos
- Chat entre usuarios (1:1 e grupo)
- Push notifications (Web Push + VAPID)
- Notificacao de novos cadastros por email (SendGrid)
- Helpdesk com troubleshooting automatico
- Rate limiting por matricula (Postgres)
- Multi-turma estruturado mas DORMENTE (aguardando ativacao)

## Como rodar

```
gunicorn -c gunicorn.conf.py server:app --bind 0.0.0.0:5000 --workers 2 --worker-class gthread --threads 8 --timeout 600 --keep-alive 5 --preload
```

## Endpoints principais

### Auth
- `POST /api/auth/login`, `/api/auth/registrar`, `/api/auth/recuperar-senha`
- `GET /api/auth/me`, `POST /api/auth/email`

### Viriato (chat IA)
- `POST /api/claude` — mensagem ao Viriato (rate limit 20/min)

### Biblioteca/Acervo
- `GET /api/biblioteca`, `POST /api/biblioteca/upload`, `POST /api/biblioteca/buscar`, `DELETE /api/biblioteca/<id>`

### Chat entre usuarios
- `GET /api/chat/usuarios`, `/api/chat/conversas`, `/api/chat/conversa/<cid>/mensagens`
- `POST /api/chat/conversa`, `/api/chat/conversa/<cid>/mensagem`

### Eventos e calendario
- `GET/POST /api/eventos`, `DELETE /api/eventos/<id>`

### MemPalace
- `GET /api/palace/status`

### Push
- `GET /api/push/vapid-public-key`, `POST /api/push/subscribe`, `/api/push/unsubscribe`, `/api/push/test`

### Diagnostico
- `GET /api/diag/health`, `/api/diag/biblioteca`

### Admin
- `GET /api/admin/metrics` — metricas unificadas (pool, cache, rate limit, palace)
- `GET/POST /api/admin/user-ala`, `DELETE /api/admin/user-ala/<matricula>`
- `GET /api/admin/multi-turma/status`, `POST .../backfill`, `POST .../ativar`

## Viriato — como funciona

A cada mensagem, o backend monta um system prompt dinamico com:
1. Indice da biblioteca (nome + categoria + resumo de cada PDF)
2. Top 10 chunks relevantes por keyword (busca TF-IDF nos chunks)
3. Busca semantica via pgvector (Voyage 1024d ou TF-IDF 256d fallback), threshold 0.70
4. Fatos da turma + regras tecnicas (priorizados por ala/sala)
5. Memoria pessoal do usuario
6. Anti-padroes e modo deliberativo (Sistema 2) para perguntas tecnicas/seguranca
7. Helpdesk guides
8. Instrucoes de tom (coloquial ferroviario, sem markdown, curto)
9. Regra de fidelidade textual (NUNCA parafrasear trechos de documentos/regulamentos)

Marcadores pos-resposta: `[SALVAR_MEMORIA]`, `[SALVAR_EVENTO]`, `[SALVAR_REGRA]` — processados e removidos antes de devolver ao usuario.

## Estado atual e pendencias

- Turma A em producao (https://agenda-turma-a.replit.app)
- Multi-turma DORMENTE (backfill + flag + mapeamento matricula->turma prontos, aguardando ativacao)
- FASE 1 multi-turma pendente (campo `turma` no cadastro + logica de escala por turma)
- Voyage AI indexando chunks da biblioteca (embedding_v2 1024d)

## Historico de versoes

Ver `CHANGELOG.md` para detalhes de v3.0 a v3.5 (Diario, Escala 500, Menu, MemPalace, Escalabilidade, hotfixes).
