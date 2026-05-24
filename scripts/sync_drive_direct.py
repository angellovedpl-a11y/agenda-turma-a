"""Sync Google Drive → Biblioteca do Viriato (direto, sem Flask).
Uso: python3 scripts/sync_drive_direct.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    extrair_texto_arquivo,
    fazer_chunks,
    categorizar_doc,
    mem_palace_load,
    mem_palace_save,
    _indexar_biblio_em_batch_async,
)
import drive_sync as ds

print('Iniciando sync do Google Drive...', flush=True)
resultado = ds.drive_sync(
    extrair_texto_fn=extrair_texto_arquivo,
    fazer_chunks_fn=fazer_chunks,
    categorizar_doc_fn=categorizar_doc,
    mem_palace_load_fn=mem_palace_load,
    mem_palace_save_fn=mem_palace_save,
    indexar_batch_fn=_indexar_biblio_em_batch_async,
)

print('\n=== RESULTADO ===')
print(f"Novos: {resultado.get('novos', 0)}")
print(f"Atualizados: {resultado.get('atualizados', 0)}")
print(f"Erros: {len(resultado.get('erros', []))}")
print(f"Tempo: {resultado.get('tempo_s', '?')}s")
if resultado.get('detalhes'):
    print('\nDetalhes:')
    for d in resultado['detalhes']:
        print(f'  {d}')
if resultado.get('erros'):
    print('\nErros:')
    for e in resultado['erros']:
        print(f'  {e}')
