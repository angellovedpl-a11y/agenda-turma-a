import sys
import types
import unittest
from contextlib import contextmanager

fake_flask = types.ModuleType('flask')


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def get_json(self):
        return self._payload


class FakeRequest:
    headers = {}
    args = {}
    current_user = None


fake_flask.request = FakeRequest()
fake_flask.jsonify = lambda payload=None, **kwargs: FakeResponse(payload if payload is not None else kwargs)
sys.modules.setdefault('flask', fake_flask)

fake_kvstore = types.ModuleType('kvstore')


class FakeKVStoreError(Exception):
    pass


@contextmanager
def fake_default_lock(_key):
    yield None


fake_kvstore.KVStoreError = FakeKVStoreError
fake_kvstore.load = lambda key, raise_on_error=False, conn=None: {}
fake_kvstore.save = lambda key, value, raise_on_error=False, conn=None: True
fake_kvstore.health = lambda: True
fake_kvstore.with_lock = fake_default_lock
sys.modules.setdefault('kvstore', fake_kvstore)

import auth


class VerificarGoogleTokenTests(unittest.TestCase):
    def setUp(self):
        self._orig_cid = auth.GOOGLE_CLIENT_ID
        auth.GOOGLE_CLIENT_ID = 'client-123.apps.googleusercontent.com'
        self._orig_verify = auth.google_id_token.verify_oauth2_token

    def tearDown(self):
        auth.GOOGLE_CLIENT_ID = self._orig_cid
        auth.google_id_token.verify_oauth2_token = self._orig_verify

    def test_token_valido_retorna_sub_email_nome(self):
        auth.google_id_token.verify_oauth2_token = lambda *a, **k: {
            'iss': 'https://accounts.google.com', 'sub': '999',
            'email': 'Fulano@Gmail.com', 'name': 'Fulano Silva'}
        info = auth.verificar_google_token('tok')
        self.assertEqual(info['sub'], '999')
        self.assertEqual(info['email'], 'fulano@gmail.com')  # normalizado minusculo
        self.assertEqual(info['nome'], 'Fulano Silva')

    def test_emissor_invalido_levanta(self):
        auth.google_id_token.verify_oauth2_token = lambda *a, **k: {
            'iss': 'evil.com', 'sub': '1'}
        with self.assertRaises(auth.GoogleAuthError):
            auth.verificar_google_token('tok')

    def test_token_vazio_levanta(self):
        with self.assertRaises(auth.GoogleAuthError):
            auth.verificar_google_token('')

    def test_sem_client_id_levanta(self):
        auth.GOOGLE_CLIENT_ID = ''
        with self.assertRaises(auth.GoogleAuthError):
            auth.verificar_google_token('tok')


if __name__ == '__main__':
    unittest.main()
