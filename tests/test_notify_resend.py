"""Testes do envio de e-mail via Resend (sem rede: requests mockado)."""
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _import_notify(monkeypatch):
    monkeypatch.setenv('RESEND_API_KEY', 're_test_123')
    monkeypatch.setenv('NOTIFY_FROM_EMAIL', 'agenda@ac1bot.com')
    import importlib
    import notify
    importlib.reload(notify)
    return notify


def test_send_email_chama_resend_com_payload_correto(monkeypatch):
    notify = _import_notify(monkeypatch)
    with mock.patch('notify.requests.post') as post:
        post.return_value = mock.Mock(status_code=200)
        ok = notify._send_email('destino@ex.com', 'Assunto', '<b>oi</b>')
    assert ok is True
    args, kwargs = post.call_args
    assert args[0] == 'https://api.resend.com/emails'
    assert kwargs['headers']['Authorization'] == 'Bearer re_test_123'
    body = kwargs['json']
    assert body['from'] == 'Agenda Turma A <agenda@ac1bot.com>'
    assert body['to'] == ['destino@ex.com']
    assert body['subject'] == 'Assunto'
    assert body['html'] == '<b>oi</b>'
    assert body['text'] == 'oi'


def test_send_email_sem_api_key_retorna_false(monkeypatch):
    monkeypatch.delenv('RESEND_API_KEY', raising=False)
    import importlib
    import notify
    importlib.reload(notify)
    with mock.patch('notify.requests.post') as post:
        ok = notify._send_email('destino@ex.com', 'Assunto', '<b>oi</b>')
    assert ok is False
    post.assert_not_called()


def test_send_email_status_4xx_retorna_false(monkeypatch):
    notify = _import_notify(monkeypatch)
    with mock.patch('notify.requests.post') as post:
        post.return_value = mock.Mock(status_code=422)
        ok = notify._send_email('destino@ex.com', 'Assunto', '<b>oi</b>')
    assert ok is False
