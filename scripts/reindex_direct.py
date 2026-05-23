#!/usr/bin/env python3
"""Reindex direto da biblioteca via Voyage, sem passar pelo Flask.

Conecta direto no Postgres ($DATABASE_URL), le sala:biblioteca do kv_store,
gera embeddings (Voyage 1024d batch=128 + TF-IDF 256d local), e faz upsert
em palace_embeddings.

Paridade total com _indexar_no_palace do server.py:
- Mesma logica de TF-IDF (md5 hash, signed bins, normalizacao L2)
- Mesma logica de chunking (id = f'biblio:{doc_id}:{ck_idx}')
- Mesmo truncamento (conteudo[:2000], texto Voyage[:8000])
- Idempotente (ON CONFLICT DO UPDATE)

Por que existe (em vez de usar /api/admin/biblioteca/reindex):
- O endpoint via Flask morria por SIGKILL (provavelmente OOM cgroup) antes de
  completar o reindex. Esse script roda sem o server, evita o problema.
- Batch=128 em vez de 1-a-1 (~50x menos calls Voyage).
- Commit por batch (idempotente, nao perde tudo se falhar no meio).

Uso:
    python3 scripts/reindex_direct.py
"""
import os
import sys
import hashlib
import math

import psycopg2
import voyageai

DB_URL = os.environ["DATABASE_URL"]
DIM_V1 = 256


def tokens_norm(texto):
    """Tokeniza igual server.py:_tokens_norm_p2 (lower, alfanum, len>=2)."""
    if not texto:
        return []
    out, cur = [], []
    for ch in texto.lower():
        if ch.isalnum():
            cur.append(ch)
        else:
            if cur:
                w = "".join(cur)
                if len(w) >= 2:
                    out.append(w)
                cur = []
    if cur:
        w = "".join(cur)
        if len(w) >= 2:
            out.append(w)
    return out


def gerar_embedding_tfidf(texto):
    """TF-IDF hashing 256d normalizado L2 (paridade com server.py:gerar_embedding opcao 3)."""
    tokens = tokens_norm(texto)
    if not tokens:
        return [0.0] * DIM_V1
    counts = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    vec = [0.0] * DIM_V1
    total = float(len(tokens))
    for tok, cnt in counts.items():
        h = hashlib.md5(tok.encode("utf-8")).digest()
        b1 = int.from_bytes(h[0:2], "big") % DIM_V1
        b2 = int.from_bytes(h[2:4], "big") % DIM_V1
        s1 = 1.0 if (h[4] & 1) == 0 else -1.0
        s2 = 1.0 if (h[4] & 2) == 0 else -1.0
        tf = cnt / total
        vec[b1] += s1 * tf
        vec[b2] += s2 * tf
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def emb_to_lit(vec):
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"


def main():
    client = voyageai.Client()

    print("[1/3] carregando biblioteca do kv_store...", flush=True)
    with psycopg2.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT value FROM kv_store WHERE key=%s", ("sala:biblioteca",))
        row = cur.fetchone()
    if not row:
        print("ERRO: sala:biblioteca nao existe", flush=True)
        sys.exit(1)
    biblioteca = row[0]
    docs = biblioteca.get("documentos", [])

    all_items = []
    for doc in docs:
        doc_id = doc.get("id")
        chunks = doc.get("chunks", [])
        for ck_idx, ck_texto in enumerate(chunks):
            if (ck_texto or "").strip():
                all_items.append((f"biblio:{doc_id}:{ck_idx}", ck_texto))

    print(f"[1/3] {len(docs)} docs, {len(all_items)} chunks com conteudo", flush=True)
    if not all_items:
        print("nada pra indexar", flush=True)
        return

    print("[2/3] gerando embeddings via Voyage (batch=128) + TF-IDF local...", flush=True)
    BATCH = 128
    processados = 0
    erros = 0

    with psycopg2.connect(DB_URL) as conn, conn.cursor() as cur:
        for i in range(0, len(all_items), BATCH):
            batch = all_items[i:i + BATCH]
            texts = [t[:8000] for _, t in batch]
            try:
                result = client.embed(texts=texts, model="voyage-4-large", input_type="document")
                embs_v2 = result.embeddings
            except Exception as e:
                erros += len(batch)
                print(f"  ERRO batch {i // BATCH + 1}: {type(e).__name__}: {e}", flush=True)
                continue
            if len(embs_v2) != len(batch):
                erros += len(batch)
                print(f"  ERRO batch {i // BATCH + 1}: voyage retornou {len(embs_v2)} pra {len(batch)} inputs", flush=True)
                continue
            for (id_chunk, conteudo), emb_v2 in zip(batch, embs_v2):
                emb_v1 = gerar_embedding_tfidf(conteudo)
                emb_v1_lit = emb_to_lit(emb_v1)
                emb_v2_lit = emb_to_lit(emb_v2)
                conteudo_trunc = conteudo[:2000]
                cur.execute(
                    """
                    INSERT INTO palace_embeddings (id, tipo, ala, sala, conteudo, embedding, embedding_v2, criado_em)
                    VALUES (%s, %s, %s, %s, %s, %s::vector, %s::vector, NOW())
                    ON CONFLICT (id) DO UPDATE
                    SET tipo = EXCLUDED.tipo,
                        ala = EXCLUDED.ala,
                        sala = EXCLUDED.sala,
                        conteudo = EXCLUDED.conteudo,
                        embedding = EXCLUDED.embedding,
                        embedding_v2 = EXCLUDED.embedding_v2,
                        criado_em = NOW()
                    """,
                    (id_chunk, "biblio", "geral", "biblioteca", conteudo_trunc, emb_v1_lit, emb_v2_lit),
                )
            conn.commit()
            processados += len(batch)
            total_batches = (len(all_items) + BATCH - 1) // BATCH
            print(f"  batch {i // BATCH + 1}/{total_batches}: {processados}/{len(all_items)} OK", flush=True)

    print(f"[3/3] FEITO: {processados} chunks indexados, {erros} erros", flush=True)


if __name__ == "__main__":
    main()
