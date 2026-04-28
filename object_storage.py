"""Wrapper fino do Replit Object Storage para anexos do Diario de Bordo
e outros binarios que nao devem inflar o Postgres.

Convencao de chave: <prefixo>/<matricula>/<entry_id>/<idx>_<nome_seguro>
A checagem de propriedade (so o dono acessa) eh feita no endpoint da API.
"""
import os
import re
import io
import time

_BUCKET_ID = os.environ.get('DEFAULT_OBJECT_STORAGE_BUCKET_ID', '').strip() or None
try:
    from replit.object_storage import Client
    _client = Client(bucket_id=_BUCKET_ID) if _BUCKET_ID else Client()
    _enabled = True
    print(f'[object_storage] cliente inicializado (bucket={_BUCKET_ID or "default"})')
except Exception as _e:
    print(f'[object_storage] indisponivel: {_e}')
    _client = None
    _enabled = False


def is_enabled() -> bool:
    return _enabled


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
        _client.upload_from_bytes(key, data)
        return True
    except Exception as e:
        print(f'[object_storage] erro upload {key}: {e}')
        return False


def download_bytes(key: str) -> bytes:
    if not _enabled:
        raise RuntimeError('object storage indisponivel')
    return _client.download_as_bytes(key)


def delete(key: str) -> bool:
    if not _enabled:
        return False
    try:
        _client.delete(key)
        return True
    except Exception as e:
        print(f'[object_storage] erro delete {key}: {e}')
        return False


def exists(key: str) -> bool:
    if not _enabled:
        return False
    try:
        _client.exists(key)
        return True
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
