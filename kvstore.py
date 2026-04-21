"""Armazenamento persistente em PostgreSQL para os JSONs do app.

Substitui a leitura/gravacao em arquivos dentro de data/ que era apagada
em cada novo deploy. As chaves continuam sendo nomes ('users', 'sessions',
'escala', etc.) e os valores sao dicionarios JSON (igual ao formato antigo).
"""
import os
import sys
import json
import threading
import subprocess

_install_lock_path = os.path.join(os.path.dirname(__file__), '.kvstore_pip.lock')

def _ensure_psycopg2():
    """Garante que psycopg2 esta disponivel; usa lock-file para evitar
    corrida entre workers gunicorn instalando ao mesmo tempo."""
    try:
        import psycopg2  # noqa
        return
    except ImportError:
        pass
    try:
        import fcntl
        with open(_install_lock_path, 'w') as lf:
            fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
            try:
                import psycopg2  # noqa
                return
            except ImportError:
                pass
            print('[kvstore] psycopg2 ausente, instalando psycopg2-binary (lock adquirido)...')
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', '--quiet', '--disable-pip-version-check', 'psycopg2-binary'],
                stdout=subprocess.DEVNULL,
            )
    except Exception as _e:
        print(f'[kvstore] erro instalando psycopg2-binary: {_e}')

_ensure_psycopg2()
import psycopg2
from psycopg2.extras import Json

_DB_URL = os.environ.get('DATABASE_URL', '')
_lock = threading.Lock()


class KVStoreError(Exception):
    pass


def _connect():
    if not _DB_URL:
        raise RuntimeError('DATABASE_URL nao configurada')
    return psycopg2.connect(_DB_URL)


def init_schema():
    if not _DB_URL:
        return
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_store (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            conn.commit()
    except Exception as e:
        print(f'[kvstore] erro init_schema: {e}')


def load(key: str, raise_on_error: bool = False) -> dict:
    if not _DB_URL:
        if raise_on_error:
            raise KVStoreError('DATABASE_URL nao configurada')
        return {}
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute('SELECT value FROM kv_store WHERE key = %s', (key,))
            row = cur.fetchone()
            if not row:
                return {}
            v = row[0]
            if isinstance(v, (dict, list)):
                return v
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except Exception:
                    return {}
            return {}
    except Exception as e:
        print(f'[kvstore] erro load({key}): {e}')
        if raise_on_error:
            raise KVStoreError(str(e))
        return {}


def save(key: str, value, raise_on_error: bool = False) -> bool:
    if not _DB_URL:
        if raise_on_error:
            raise KVStoreError('DATABASE_URL nao configurada')
        return False
    with _lock:
        try:
            with _connect() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO kv_store (key, value, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (key) DO UPDATE
                    SET value = EXCLUDED.value, updated_at = NOW()
                    """,
                    (key, Json(value)),
                )
                conn.commit()
            return True
        except Exception as e:
            print(f'[kvstore] erro save({key}): {e}')
            if raise_on_error:
                raise KVStoreError(str(e))
            return False


def migrar_de_arquivo(key: str, path: str) -> bool:
    """Migra um JSON de disco para o banco se a chave ainda nao existir.
    Atomico: usa INSERT ... ON CONFLICT DO NOTHING, entao multiplos workers
    nao sobrescrevem dados ja gravados em produção."""
    if not _DB_URL or not os.path.isfile(path):
        return False
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with _connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO kv_store (key, value, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (key) DO NOTHING
                """,
                (key, Json(data)),
            )
            inseriu = cur.rowcount > 0
            conn.commit()
        if inseriu:
            print(f'[kvstore] migrado {path} -> kv_store[{key}]')
        return inseriu
    except Exception as e:
        print(f'[kvstore] erro migrar {path}: {e}')
    return False


def health() -> bool:
    if not _DB_URL:
        return False
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute('SELECT 1')
            return cur.fetchone()[0] == 1
    except Exception as e:
        print(f'[kvstore] erro health: {e}')
        return False
