-- ============================================================================
-- FASE 4 — Embeddings reais via Voyage AI (voyage-4-large, 1024d)
-- ============================================================================
-- Aplicar UMA UNICA VEZ no banco de PRODUCAO antes do proximo deploy.
-- Idempotente (ADD COLUMN IF NOT EXISTS): pode rodar de novo sem efeito.
--
-- O QUE FAZ:
-- - Adiciona coluna `embedding_v2 vector(1024)` em palace_embeddings.
-- - A coluna antiga `embedding vector(256)` (TF-IDF hash) CONTINUA EXISTINDO
--   como fallback. Indexacao popula AMBAS quando Voyage disponivel; busca
--   por tipo='biblio' usa embedding_v2 (Voyage), busca por tipo='fato'/'regra'
--   continua usando embedding (TF-IDF) ate eventual backfill.
-- - Sem este script, indexacao Voyage cai silencioso pra TF-IDF (fallback).
--
-- COMO RODAR no Replit (painel do banco prod):
--   1. Abrir o painel Database em Production
--   2. Ir em SQL Runner / Query
--   3. Colar este arquivo inteiro
--   4. Executar
--   5. Validar com:
--      \d palace_embeddings              -- deve mostrar embedding E embedding_v2
--      SELECT count(*) FROM palace_embeddings WHERE embedding_v2 IS NULL;
-- ============================================================================

-- 1. Coluna nova (1024d pro voyage-4-large)
ALTER TABLE palace_embeddings
    ADD COLUMN IF NOT EXISTS embedding_v2 vector(1024);

-- 2. Indice ANN opcional pra acelerar busca quando tabela passar de ~10k rows.
--    Hoje (~5k fatos+regras + ~700 chunks biblio = ~5.7k) seqscan ja eh OK
--    (~5-10ms). Quando passar de 10k linhas com embedding_v2 NOT NULL, criar:
--
--    CREATE INDEX IF NOT EXISTS palace_embeddings_emb_v2_hnsw
--    ON palace_embeddings USING hnsw (embedding_v2 vector_cosine_ops);
--
--    HNSW exige pgvector >= 0.5.0. Se versao for mais antiga, usar IVFFlat.

-- ============================================================================
-- Validacao pos-execucao:
--   SELECT count(*) FROM palace_embeddings;                       -- N total
--   SELECT count(*) FROM palace_embeddings WHERE embedding_v2 IS NOT NULL;
--   -- (deve ser 0 antes do backfill, >0 depois)
-- ============================================================================
