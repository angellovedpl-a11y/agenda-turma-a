"""Envio de notificacoes por e-mail via Resend (API HTTP direta).

Custo zero: plano free do Resend (3.000 e-mails/mes). Sem SDK — so requests.
Env: RESEND_API_KEY, NOTIFY_FROM_EMAIL (remetente verificado no Resend).
"""
import os
import time
import html
import threading
import requests

import auth as _auth

_RESEND_URL = 'https://api.resend.com/emails'


def _mask_email(e: str) -> str:
    if not e or '@' not in e:
        return '***'
    user, _, dom = e.partition('@')
    return (user[:2] + '***@' + dom) if user else ('***@' + dom)


def _send_email(to_email: str, subject: str, html: str, text: str = '') -> bool:
    api_key = os.environ.get('RESEND_API_KEY', '').strip()
    from_email = os.environ.get('NOTIFY_FROM_EMAIL', '').strip()
    if not api_key or not from_email:
        print('[notify] Resend nao configurado (RESEND_API_KEY/NOTIFY_FROM_EMAIL), e-mail ignorado')
        return False
    try:
        resp = requests.post(
            _RESEND_URL,
            headers={'Authorization': f'Bearer {api_key}'},
            json={
                'from': f'Agenda Turma A <{from_email}>',
                'to': [to_email],
                'subject': subject,
                'html': html,
                'text': text or _strip_html(html),
            },
            timeout=15,
        )
        ok = 200 <= resp.status_code < 300
        if not ok:
            print(f'[notify] Resend status {resp.status_code} ao enviar para {_mask_email(to_email)}')
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
