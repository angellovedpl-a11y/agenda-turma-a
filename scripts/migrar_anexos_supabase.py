"""Copia todos os objetos do Replit Object Storage -> Supabase Storage.

RODAR NO SHELL DO REPLIT:
  export SUPABASE_URL='https://xxx.supabase.co'
  export SUPABASE_SERVICE_KEY='...'
  export SUPABASE_BUCKET='anexos'
  python scripts/migrar_anexos_supabase.py

Idempotente: roda de novo sem duplicar (upsert). Nao apaga nada na origem.
"""
import os
import sys
import mimetypes
import requests
from replit.object_storage import Client

SUPABASE_URL = os.environ['SUPABASE_URL'].rstrip('/')
SERVICE_KEY = os.environ['SUPABASE_SERVICE_KEY']
BUCKET = os.environ.get('SUPABASE_BUCKET', 'anexos')

bucket_id = os.environ.get('DEFAULT_OBJECT_STORAGE_BUCKET_ID', '').strip() or None
client = Client(bucket_id=bucket_id) if bucket_id else Client()

objetos = list(client.list())
print(f'{len(objetos)} objeto(s) no bucket Replit')

ok = err = 0
for o in objetos:
    key = o.name
    try:
        data = client.download_as_bytes(key)
        ctype = mimetypes.guess_type(key)[0] or 'application/octet-stream'
        r = requests.post(
            f'{SUPABASE_URL}/storage/v1/object/{BUCKET}/{key}',
            headers={
                'Authorization': f'Bearer {SERVICE_KEY}',
                'Content-Type': ctype,
                'x-upsert': 'true',
            },
            data=data,
            timeout=60,
        )
        if r.status_code in (200, 201):
            ok += 1
            print(f'  OK  {key} ({len(data)} bytes)')
        else:
            err += 1
            print(f'  ERR {key}: status {r.status_code} {r.text[:120]}')
    except Exception as e:
        err += 1
        print(f'  ERR {key}: {e}')

print(f'\nResultado: {ok} copiado(s), {err} erro(s)')
sys.exit(1 if err else 0)
