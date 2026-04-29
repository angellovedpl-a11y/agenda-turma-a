-- ============================================================================
-- FASE 2 MemPalace — busca semantica via pgvector
-- ============================================================================
-- Aplicar UMA UNICA VEZ no banco de PRODUCAO antes do proximo deploy.
-- Idempotente (CREATE ... IF NOT EXISTS): pode rodar de novo sem efeito.
-- Sem este script aplicado, a Fase 2 fica como no-op em prod (health check
-- detecta ausencia, retorna False, fluxo cai pra Fase 1 sem regressao).
--
-- Como rodar no Replit (painel do banco prod):
--   1. Abrir o painel Database em Production
--   2. Ir em SQL Runner / Query
--   3. Colar este arquivo inteiro
--   4. Executar
--   5. Validar com: SELECT extname FROM pg_extension WHERE extname='vector';
--                   SELECT count(*) FROM palace_embeddings;
--                   (deve retornar a extensao e contagem 0)
-- ============================================================================

-- 1. Extension pgvector (provida pelo Replit Postgres)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tabela de embeddings do MemPalace
--    id: chave prefixada por tipo ('fato:<int>' ou 'regra:<int>') pra
--        evitar colisao em ON CONFLICT entre fatos e regras com mesmo
--        timestamp-em-ms. Tipo TEXT (nao serial) porque o id eh derivado
--        do id natural do item (atribuido por fatos_add/regras_tecnicas_add).
--    embedding: vetor 256d (TF-IDF caseiro de stdlib hoje; preparado pra
--               futura migracao pra modelo real se Anthropic expor .embeddings
--               ou se OPENAI_API_KEY for adicionado).
CREATE TABLE IF NOT EXISTS palace_embeddings (
    id          TEXT        PRIMARY KEY,
    tipo        TEXT        NOT NULL,           -- 'fato' | 'regra' (futuro: 'doc', 'antipadrao'...)
    ala         TEXT        NOT NULL DEFAULT 'geral',
    sala        TEXT        NOT NULL DEFAULT 'geral',
    conteudo    TEXT        NOT NULL,
    embedding   vector(256) NOT NULL,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Indices pra filtros de WHERE em busca_semantica (filtro por ala/sala/tipo)
CREATE INDEX IF NOT EXISTS palace_embeddings_ala_idx  ON palace_embeddings (ala);
CREATE INDEX IF NOT EXISTS palace_embeddings_sala_idx ON palace_embeddings (sala);
CREATE INDEX IF NOT EXISTS palace_embeddings_tipo_idx ON palace_embeddings (tipo);

-- 4. Indice ANN (opcional, recomendado se tabela passar de ~10k linhas).
--    Hoje a tabela cresce ate ~5.2k itens (5000 fatos + 200 regras), entao
--    o ORDER BY embedding <=> %s::vector com seqscan ja eh aceitavel
--    (tempo proporcional, ~5 ms na carga maxima). Se quiser ativar:
--
--    CREATE INDEX IF NOT EXISTS palace_embeddings_emb_hnsw
--    ON palace_embeddings USING hnsw (embedding vector_cosine_ops);
--
--    HNSW exige pgvector >= 0.5.0; se o Replit Postgres tiver versao mais
--    antiga, usar IVFFlat:
--    CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);

-- ============================================================================
-- Validacao pos-execucao (rodar a parte e conferir):
--   SELECT extname FROM pg_extension WHERE extname = 'vector';      -- 1 linha
--   SELECT count(*) FROM palace_embeddings;                          -- 0
--   \d palace_embeddings                                             -- mostra schema
-- ============================================================================
