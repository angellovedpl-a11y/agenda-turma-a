"""Testes do wrapper Supabase Storage (sem rede: requests mockado)."""
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _import_obj(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://abc.supabase.co')
    monkeypatch.setenv('SUPABASE_SERVICE_KEY', 'sbk_test')
    monkeypatch.setenv('SUPABASE_BUCKET', 'anexos')
    import importlib
    import object_storage
    importlib.reload(object_storage)
    return object_storage


def test_upload_faz_post_com_bytes_e_bearer(monkeypatch):
    obj = _import_obj(monkeypatch)
    assert obj.is_enabled() is True
    with mock.patch('object_storage.requests.post') as post:
        post.return_value = mock.Mock(status_code=200)
        ok = obj.upload_bytes('diario/123/e1/000_foto.jpg', b'JPEGDATA', 'image/jpeg')
    assert ok is True
    args, kwargs = post.call_args
    assert args[0] == 'https://abc.supabase.co/storage/v1/object/anexos/diario/123/e1/000_foto.jpg'
    assert kwargs['headers']['Authorization'] == 'Bearer sbk_test'
    assert kwargs['headers']['Content-Type'] == 'image/jpeg'
    assert kwargs['headers']['x-upsert'] == 'true'
    assert kwargs['data'] == b'JPEGDATA'


def test_download_retorna_bytes(monkeypatch):
    obj = _import_obj(monkeypatch)
    with mock.patch('object_storage.requests.get') as get:
        get.return_value = mock.Mock(status_code=200, content=b'JPEGDATA')
        data = obj.download_bytes('diario/123/e1/000_foto.jpg')
    assert data == b'JPEGDATA'


def test_download_404_levanta_erro(monkeypatch):
    obj = _import_obj(monkeypatch)
    with mock.patch('object_storage.requests.get') as get:
        get.return_value = mock.Mock(status_code=404)
        try:
            obj.download_bytes('nao/existe')
            assert False, 'devia ter levantado'
        except RuntimeError:
            pass


def test_sem_env_fica_desabilitado(monkeypatch):
    monkeypatch.delenv('SUPABASE_URL', raising=False)
    monkeypatch.delenv('SUPABASE_SERVICE_KEY', raising=False)
    import importlib
    import object_storage
    importlib.reload(object_storage)
    assert object_storage.is_enabled() is False
    assert object_storage.upload_bytes('k', b'x') is False
    assert object_storage.delete('k') is False
    assert object_storage.exists('k') is False


def test_key_belongs_to_continua_bloqueando_traversal(monkeypatch):
    obj = _import_obj(monkeypatch)
    assert obj.key_belongs_to('diario/123/e1/000_a.jpg', 'diario', '123') is True
    assert obj.key_belongs_to('diario/999/e1/000_a.jpg', 'diario', '123') is False
    assert obj.key_belongs_to('../etc/passwd', 'diario', '123') is False
