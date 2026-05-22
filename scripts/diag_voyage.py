#!/usr/bin/env python3
"""Diagnostico Voyage: confirma key + SDK + API + embed funcional."""
import os
import sys
import time

print("=== DIAG VOYAGE ===")
key = os.environ.get('VOYAGE_API_KEY', '')
print(f"VOYAGE_API_KEY len: {len(key)} (deve ser > 30)")
if not key:
    print("FALHA: VOYAGE_API_KEY ausente no env")
    sys.exit(1)

try:
    import voyageai
    print(f"voyageai version: {voyageai.__version__}")
except ImportError as e:
    print(f"FALHA: voyageai nao instalado ({e})")
    sys.exit(1)

print("\nChamando embed (1 texto teste)...")
sys.stdout.flush()
t0 = time.time()
try:
    client = voyageai.Client()
    result = client.embed(
        texts=["teste de embedding com mangote ferroviario"],
        model="voyage-4-large",
        input_type="document",
    )
    print(f"OK em {time.time()-t0:.1f}s")
    print(f"  Dim do vetor: {len(result.embeddings[0])} (esperado 1024)")
    print(f"  Tokens usados: {result.total_tokens}")
    print(f"  Primeiros 5 floats: {result.embeddings[0][:5]}")
except Exception as e:
    print(f"FALHA na chamada Voyage ({time.time()-t0:.1f}s): {type(e).__name__}: {e}")
    sys.exit(1)
