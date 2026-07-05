"""Wrapper fino do Supabase Storage para anexos do Diario de Bordo
e outros binarios que nao devem inflar o Postgres.

Convencao de chave: <prefixo>/<matricula>/<entry_id>/<idx>_<nome_seguro>
A checagem de propriedade (so o dono acessa) eh feita no endpoint da API.

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_BUCKET (default 'anexos').
Bucket deve ser PRIVADO — todo acesso passa por aqui com a service key.
"""
import os
import re
import time
import requests

_SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip().rstrip('/')
_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '').strip()
_BUCKET = os.environ.get('SUPABASE_BUCKET', 'anexos').strip() or 'anexos'
_enabled = bool(_SUPABASE_URL and _SERVICE_KEY)
if _enabled:
    print(f'[object_storage] Supabase Storage ativo (bucket={_BUCKET})')
else:
    print('[object_storage] indisponivel: SUPABASE_URL/SUPABASE_SERVICE_KEY ausentes')


def is_enabled() -> bool:
    return _enabled


def _object_url(key: str) -> str:
    return f'{_SUPABASE_URL}/storage/v1/object/{_BUCKET}/{key}'


def _headers(extra: dict = None) -> dict:
    h = {'Authorization': f'Bearer {_SERVICE_KEY}'}
    if extra:
        h.update(extra)
    return h


def _safe_name(nome: str, max_len: int = 60) -> str:
    if not nome:
        return 'arquivo'
    nome = re.sub(r'[^A-Za-z0-9._-]', '_', nome)
    nome = nome.strip('._') or 'arquivo'
    if len(nome) > max_len:
        base, dot, ext = nome.rpartition('.')
        if dot and len(ext) <= 6:
            nome = base[:max_len - len(ext) - 1] + '.' + ext
        else:
            nome = nome[:max_len]
    return nome


def make_key(prefixo: str, matricula: str, entry_id, idx: int, nome: str) -> str:
    """Gera chave previsivel e segura. matricula vai como identificador do dono."""
    mat = re.sub(r'[^A-Za-z0-9_-]', '_', str(matricula or 'anon'))
    eid = re.sub(r'[^A-Za-z0-9_-]', '_', str(entry_id or int(time.time() * 1000)))
    return f'{prefixo}/{mat}/{eid}/{int(idx):03d}_{_safe_name(nome)}'


def upload_bytes(key: str, data: bytes, content_type: str = 'application/octet-stream') -> bool:
    if not _enabled:
        return False
    try:
        r = requests.post(
            _object_url(key),
            headers=_headers({'Content-Type': content_type, 'x-upsert': 'true'}),
            data=data,
            timeout=30,
        )
        if r.status_code not in (200, 201):
            print(f'[object_storage] erro upload {key}: status {r.status_code}')
            return False
        return True
    except Exception as e:
        print(f'[object_storage] erro upload {key}: {e}')
        return False


def download_bytes(key: str) -> bytes:
    if not _enabled:
        raise RuntimeError('object storage indisponivel')
    r = requests.get(_object_url(key), headers=_headers(), timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f'download {key}: status {r.status_code}')
    return r.content


def delete(key: str) -> bool:
    if not _enabled:
        return False
    try:
        r = requests.delete(_object_url(key), headers=_headers(), timeout=15)
        return r.status_code == 200
    except Exception as e:
        print(f'[object_storage] erro delete {key}: {e}')
        return False


def exists(key: str) -> bool:
    if not _enabled:
        return False
    try:
        r = requests.get(
            _object_url(key),
            headers=_headers({'Range': 'bytes=0-0'}),
            timeout=15,
        )
        return r.status_code in (200, 206)
    except Exception:
        return False


def key_belongs_to(key: str, prefixo: str, matricula: str) -> bool:
    """Verifica que a chave eh do dono esperado. Bloqueia path traversal."""
    if not key or '..' in key or key.startswith('/'):
        return False
    mat = re.sub(r'[^A-Za-z0-9_-]', '_', str(matricula or ''))
    if not mat:
        return False
    return key.startswith(f'{prefixo}/{mat}/')
