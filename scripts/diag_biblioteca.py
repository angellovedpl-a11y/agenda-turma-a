"""Diagnostico da biblioteca do Viriato.
Uso: python3 scripts/diag_biblioteca.py [termo]
Exemplo: python3 scripts/diag_biblioteca.py 40.5
"""
import sys
import json

sys.path.insert(0, '.')
import kvstore

termo = sys.argv[1] if len(sys.argv) > 1 else None

raw = kvstore.kv_get('sala:biblioteca')
if not raw:
    print('ERRO: biblioteca vazia no kv_store')
    sys.exit(1)

bib = json.loads(raw)
docs = bib.get('documentos', [])
print(f'Documentos na biblioteca: {len(docs)}\n')

for doc in docs:
    nome = doc.get('nome', '?')
    cat = doc.get('categoria', '?')
    chunks = doc.get('chunks', [])
    print(f'  [{cat}] {nome} — {len(chunks)} chunks')

    if termo:
        for i, chunk in enumerate(chunks):
            limpo = chunk.replace(' ', '')
            if termo in chunk or termo in limpo:
                preview = chunk[:120].replace('\n', ' ')
                print(f'    >>> chunk {i}: "{preview}..."')

if termo:
    print(f'\nBusca por "{termo}" concluida.')
