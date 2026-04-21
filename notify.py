"""Envio de notificacoes por e-mail via SendGrid (integracao Replit).

As credenciais sao buscadas do conector Replit a cada chamada (sem cache:
o token de identidade pode rotacionar).
"""
import os
import time
import html
import threading
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import auth as _auth


def _mask_email(e: str) -> str:
    if not e or '@' not in e:
        return '***'
    user, _, dom = e.partition('@')
    return (user[:2] + '***@' + dom) if user else ('***@' + dom)


def _get_replit_token():
    if os.environ.get('REPL_IDENTITY'):
        return 'repl ' + os.environ['REPL_IDENTITY']
    if os.environ.get('WEB_REPL_RENEWAL'):
        return 'depl ' + os.environ['WEB_REPL_RENEWAL']
    return None


def _get_sendgrid_credentials():
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    token = _get_replit_token()
    if not hostname or not token:
        return None
    try:
        r = requests.get(
            f'https://{hostname}/api/v2/connection',
            params={'include_secrets': 'true', 'connector_names': 'sendgrid'},
            headers={'Accept': 'application/json', 'X-Replit-Token': token},
            timeout=10,
        )
        r.raise_for_status()
        items = (r.json() or {}).get('items') or []
        if not items:
            return None
        s = items[0].get('settings') or {}
        api_key = s.get('api_key')
        from_email = s.get('from_email')
        if not api_key or not from_email:
            return None
        return api_key, from_email
    except Exception as e:
        print(f'[notify] erro ao buscar credenciais SendGrid: {e}')
        return None


def _send_email(to_email: str, subject: str, html: str, text: str = '') -> bool:
    creds = _get_sendgrid_credentials()
    if not creds:
        print('[notify] SendGrid nao configurado, e-mail ignorado')
        return False
    api_key, from_email = creds
    try:
        msg = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=text or _strip_html(html),
            html_content=html,
        )
        sg = SendGridAPIClient(api_key)
        resp = sg.send(msg)
        ok = 200 <= resp.status_code < 300
        if not ok:
            print(f'[notify] SendGrid status {resp.status_code} ao enviar para {_mask_email(to_email)}')
        return ok
    except Exception as e:
        print(f'[notify] erro enviando para {_mask_email(to_email)}: {e}')
        return False


def _strip_html(s: str) -> str:
    import re
    return re.sub(r'<[^>]+>', '', s or '')


def _aprovadores_com_email():
    users = _auth.users_load()
    out = []
    for mat, u in users.items():
        if u.get('role') in ('admin', 'aprovador') and u.get('status') == 'aprovado':
            email = (u.get('email') or '').strip()
            if email:
                out.append((mat, u.get('nome', ''), email))
    return out


def _enviar_lote(destinatarios, matricula, nome):
    quando = time.strftime('%d/%m/%Y às %H:%M')
    nome_safe = html.escape(nome or '', quote=True)
    matricula_safe = html.escape(matricula or '', quote=True)
    for mat, nome_aprov, email in destinatarios:
        primeiro = (nome_aprov or 'aprovador').split()[0] if nome_aprov else 'aprovador'
        primeiro_safe = html.escape(primeiro, quote=True)
        assunto = f'Novo cadastro pendente — {nome}'
        body_html = f"""
        <div style="font-family:system-ui,Arial,sans-serif;max-width:560px;margin:auto;color:#222">
          <div style="background:#008f83;color:#fff;padding:16px 20px;border-radius:8px 8px 0 0">
            <div style="font-size:18px;font-weight:700">Agenda Turma A</div>
            <div style="font-size:13px;opacity:.9">Escala Ferroviária 2x2 (2026-2030)</div>
          </div>
          <div style="border:1px solid #e5e7eb;border-top:0;padding:20px;border-radius:0 0 8px 8px">
            <p>Olá, <b>{primeiro_safe}</b>!</p>
            <p>Um novo colega acabou de se cadastrar e está aguardando aprovação:</p>
            <div style="background:#fdf6e3;border-left:4px solid #fdb913;padding:12px 16px;margin:16px 0;border-radius:4px">
              <div><b>Nome:</b> {nome_safe}</div>
              <div><b>Matrícula:</b> {matricula_safe}</div>
              <div><b>Recebido em:</b> {quando}</div>
            </div>
            <p>Abra o app, toque na coroa do administrador e aprove (ou negue) o cadastro.</p>
            <p style="font-size:12px;color:#666;margin-top:24px">Você está recebendo este e-mail porque é admin ou aprovador na Agenda Turma A.</p>
          </div>
        </div>
        """
        _send_email(email, assunto, body_html)


def notificar_novo_cadastro(matricula: str, nome: str):
    """Dispara e-mails em background para nao atrasar o cadastro."""
    destinatarios = _aprovadores_com_email()
    if not destinatarios:
        return 0
    t = threading.Thread(
        target=_enviar_lote, args=(destinatarios, matricula, nome), daemon=True
    )
    t.start()
    return len(destinatarios)
