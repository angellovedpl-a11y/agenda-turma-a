import copy
import json
import os
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


class LegalAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.store = {
            'users': {},
            'sessions': {},
            'legal_acceptance_audit': {},
        }
        self._orig_load = auth.kvstore.load
        self._orig_save = auth.kvstore.save
        self._orig_health = auth.kvstore.health
        self._orig_with_lock = auth.kvstore.with_lock
        self._orig_salt = os.environ.get('LEGAL_AUDIT_SALT')
        os.environ['LEGAL_AUDIT_SALT'] = 'test-salt-for-legal-audit-32'

        def fake_load(key, raise_on_error=False, conn=None):
            return copy.deepcopy(self.store.get(key, {}))

        def fake_save(key, value, raise_on_error=False, conn=None):
            self.store[key] = copy.deepcopy(value)
            return True

        @contextmanager
        def fake_with_lock(key):
            yield None

        auth.kvstore.load = fake_load
        auth.kvstore.save = fake_save
        auth.kvstore.health = lambda: True
        auth.kvstore.with_lock = fake_with_lock
        auth.request.headers = {}
        auth.request.args = {}

    def tearDown(self):
        auth.kvstore.load = self._orig_load
        auth.kvstore.save = self._orig_save
        auth.kvstore.health = self._orig_health
        auth.kvstore.with_lock = self._orig_with_lock
        if self._orig_salt is None:
            os.environ.pop('LEGAL_AUDIT_SALT', None)
        else:
            os.environ['LEGAL_AUDIT_SALT'] = self._orig_salt

    def _json(self, response):
        if isinstance(response, tuple):
            body, status = response
        else:
            body, status = response, response.status_code
        return body.get_json(), status

    def test_registration_requires_explicit_legal_acceptance(self):
        payload = {
            'nome': 'Usuario Teste',
            'matricula': '123456',
            'funcao': 'Função Operacional',
            'senha': '1234',
            'aceita_termos': False,
        }
        data, status = self._json(auth.handle_registrar(payload))

        self.assertEqual(status, 400)
        self.assertIn('termos', data['error'].lower())
        self.assertEqual(self.store['users'], {})

    def test_registration_stores_acceptance_audit_without_raw_ip_or_user_agent(self):
        payload = {
            'nome': 'Usuario Teste',
            'matricula': '123456',
            'funcao': 'Função Operacional',
            'senha': '1234',
            'aceita_termos': True,
        }
        headers = {
            'X-Forwarded-For': '203.0.113.10',
            'User-Agent': 'Browser-De-Teste/1.0',
        }
        auth.request.headers = headers
        _data, status = self._json(auth.handle_registrar(payload))

        self.assertEqual(status, 200)
        user = self.store['users']['123456']
        self.assertEqual(user['legal_acceptance']['terms_version'], auth.LEGAL_TERMS_VERSION)
        self.assertEqual(user['legal_acceptance']['policy_version'], auth.LEGAL_POLICY_VERSION)

        entries = self.store['legal_acceptance_audit']['entries']
        self.assertEqual(len(entries), 1)
        entry_text = json.dumps(entries[0], sort_keys=True)
        self.assertIn('"matricula": "123456"', entry_text)
        self.assertNotIn('203.0.113.10', entry_text)
        self.assertNotIn('Browser-De-Teste/1.0', entry_text)
        self.assertRegex(entries[0]['ip_hash'], r'^[0-9a-f]{64}$')
        self.assertRegex(entries[0]['user_agent_hash'], r'^[0-9a-f]{64}$')

    def test_legacy_login_returns_legal_acceptance_required(self):
        self.store['users']['123456'] = {
            'nome': 'Usuario Legado',
            'funcao': 'Função Operacional',
            'senha_hash': auth.hash_senha('123456', '1234'),
            'status': 'aprovado',
            'role': 'user',
        }
        payload = {'matricula': '123456', 'senha': '1234'}
        data, status = self._json(auth.handle_login(payload))

        self.assertEqual(status, 200)
        self.assertTrue(data['user']['legal_acceptance_required'])
        self.assertEqual(data['user']['legal_terms_version'], auth.LEGAL_TERMS_VERSION)

    def test_acceptance_endpoint_updates_user_and_audit_log(self):
        self.store['users']['123456'] = {
            'nome': 'Usuario Legado',
            'funcao': 'Função Operacional',
            'senha_hash': auth.hash_senha('123456', '1234'),
            'status': 'aprovado',
            'role': 'user',
        }
        user = {'matricula': '123456', **self.store['users']['123456']}
        payload = {'accepted': True}
        data, status = self._json(auth.handle_legal_acceptance(payload, user))

        self.assertEqual(status, 200)
        self.assertFalse(data['legal_acceptance_required'])
        stored = self.store['users']['123456']['legal_acceptance']
        self.assertEqual(stored['terms_version'], auth.LEGAL_TERMS_VERSION)
        self.assertEqual(len(self.store['legal_acceptance_audit']['entries']), 1)


if __name__ == '__main__':
    unittest.main()
