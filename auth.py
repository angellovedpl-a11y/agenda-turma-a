"""Sistema de autenticacao Agenda Turma A.
- Matricula: 6 digitos
- Senha: 4 digitos
- Primeiro registro vira admin automaticamente
- Admin pode promover ate 3 aprovadores adicionais (total 4 podem aprovar)
- Cadastros novos ficam pendentes ate aprovacao
- Sessoes via token (uuid) salvas em data/sessions.json (validade 30 dias)
"""
import os, json, hashlib, secrets, time, re
from functools import wraps
from flask import request, jsonify

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
USERS_PATH = os.path.join(DATA_DIR, 'users.json')
SESSIONS_PATH = os.path.join(DATA_DIR, 'sessions.json')

SESSION_DAYS = 30
MAX_APROVADORES = 3  # alem do admin

MATRICULA_RE = re.compile(r'^\d{6}$')
SENHA_RE = re.compile(r'^\d{4}$')


def _load(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save(path, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def users_load():
    return _load(USERS_PATH)


def users_save(data):
    _save(USERS_PATH, data)


def sessions_load():
    return _load(SESSIONS_PATH)


def sessions_save(data):
    _save(SESSIONS_PATH, data)


def hash_senha(matricula: str, senha: str) -> str:
    salt = ('turmaA_' + matricula).encode('utf-8')
    return hashlib.sha256(salt + senha.encode('utf-8')).hexdigest()


def validar_matricula(m: str) -> bool:
    return bool(m and MATRICULA_RE.match(m))


def validar_senha(s: str) -> bool:
    return bool(s and SENHA_RE.match(s))


def session_create(matricula: str) -> str:
    sessions = sessions_load()
    # limpa expiradas e do mesmo user
    agora = time.time()
    limite = agora - SESSION_DAYS * 86400
    sessions = {t: v for t, v in sessions.items()
                if v.get('criado', 0) > limite and v.get('matricula') != matricula}
    token = secrets.token_urlsafe(24)
    sessions[token] = {'matricula': matricula, 'criado': agora}
    sessions_save(sessions)
    return token


def session_get(token: str):
    if not token:
        return None
    sessions = sessions_load()
    s = sessions.get(token)
    if not s:
        return None
    if time.time() - s.get('criado', 0) > SESSION_DAYS * 86400:
        return None
    return s


def session_destroy(token: str):
    sessions = sessions_load()
    if token in sessions:
        del sessions[token]
        sessions_save(sessions)


def get_token_from_request():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:].strip()
    return request.headers.get('X-Auth-Token', '').strip() or None


def get_current_user():
    token = get_token_from_request()
    s = session_get(token)
    if not s:
        return None
    users = users_load()
    u = users.get(s['matricula'])
    if not u or u.get('status') != 'aprovado':
        return None
    return {'matricula': s['matricula'], **u}


def can_approve(user) -> bool:
    if not user:
        return False
    return user.get('role') in ('admin', 'aprovador')


def require_auth(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        u = get_current_user()
        if not u:
            return jsonify({'error': 'auth_required', 'mensagem': 'Faca login'}), 401
        request.current_user = u
        return fn(*a, **kw)
    return wrapped


def require_approver(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        u = get_current_user()
        if not u:
            return jsonify({'error': 'auth_required'}), 401
        if not can_approve(u):
            return jsonify({'error': 'forbidden', 'mensagem': 'Apenas aprovadores'}), 403
        request.current_user = u
        return fn(*a, **kw)
    return wrapped


def require_admin(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        u = get_current_user()
        if not u:
            return jsonify({'error': 'auth_required'}), 401
        if u.get('role') != 'admin':
            return jsonify({'error': 'forbidden', 'mensagem': 'Apenas admin'}), 403
        request.current_user = u
        return fn(*a, **kw)
    return wrapped


# === ENDPOINTS HANDLERS ===

def handle_registrar(data):
    matricula = (data.get('matricula') or '').strip()
    senha = (data.get('senha') or '').strip()
    nome = (data.get('nome') or '').strip()[:60]
    if not validar_matricula(matricula):
        return jsonify({'error': 'A matricula deve ter exatamente 6 digitos'}), 400
    if not validar_senha(senha):
        return jsonify({'error': 'A senha deve ter exatamente 4 digitos'}), 400
    if not nome or len(nome) < 2:
        return jsonify({'error': 'Informe seu nome (minimo 2 caracteres)'}), 400
    users = users_load()
    if matricula in users:
        return jsonify({'error': 'Matricula ja cadastrada. Use login ou recuperacao.'}), 409
    primeiro = (len(users) == 0)
    novo = {
        'nome': nome,
        'senha_hash': hash_senha(matricula, senha),
        'status': 'aprovado' if primeiro else 'pendente',
        'role': 'admin' if primeiro else 'user',
        'criado_em': time.time(),
        'aprovado_em': time.time() if primeiro else None,
        'aprovado_por': 'auto-admin' if primeiro else None,
    }
    users[matricula] = novo
    users_save(users)
    if primeiro:
        token = session_create(matricula)
        return jsonify({'ok': True, 'admin': True, 'token': token,
                        'mensagem': 'Bem-vindo, administrador! Voce e o primeiro usuario.',
                        'user': {'matricula': matricula, 'nome': nome, 'role': 'admin'}})
    return jsonify({'ok': True, 'pendente': True,
                    'mensagem': 'Cadastro recebido! Aguarde aprovacao de um administrador.'})


def handle_login(data):
    matricula = (data.get('matricula') or '').strip()
    senha = (data.get('senha') or '').strip()
    if not validar_matricula(matricula) or not validar_senha(senha):
        return jsonify({'error': 'Matricula (6 digitos) ou senha (4 digitos) invalidas'}), 400
    users = users_load()
    u = users.get(matricula)
    if not u:
        return jsonify({'error': 'Matricula ou senha incorretas'}), 401
    if u.get('senha_hash') != hash_senha(matricula, senha):
        return jsonify({'error': 'Matricula ou senha incorretas'}), 401
    if u.get('status') == 'pendente':
        return jsonify({'error': 'Cadastro pendente de aprovacao do administrador'}), 403
    if u.get('status') == 'negado':
        return jsonify({'error': 'Cadastro negado pelo administrador'}), 403
    token = session_create(matricula)
    return jsonify({'ok': True, 'token': token, 'user': {
        'matricula': matricula, 'nome': u.get('nome'), 'role': u.get('role', 'user')
    }})


def handle_logout():
    token = get_token_from_request()
    if token:
        session_destroy(token)
    return jsonify({'ok': True})


def handle_me():
    u = get_current_user()
    if not u:
        return jsonify({'authenticated': False}), 200
    pendentes = 0
    if can_approve(u):
        users = users_load()
        pendentes = sum(1 for x in users.values() if x.get('status') == 'pendente')
    return jsonify({
        'authenticated': True,
        'matricula': u['matricula'],
        'nome': u.get('nome'),
        'role': u.get('role', 'user'),
        'pode_aprovar': can_approve(u),
        'pendentes': pendentes,
    })


def handle_pendentes():
    users = users_load()
    out = []
    for mat, u in users.items():
        if u.get('status') == 'pendente':
            out.append({'matricula': mat, 'nome': u.get('nome'), 'criado_em': u.get('criado_em')})
    out.sort(key=lambda x: x.get('criado_em', 0))
    return jsonify({'total': len(out), 'pendentes': out})


def handle_listar_usuarios():
    users = users_load()
    out = []
    for mat, u in users.items():
        out.append({
            'matricula': mat,
            'nome': u.get('nome'),
            'status': u.get('status'),
            'role': u.get('role', 'user'),
            'criado_em': u.get('criado_em'),
            'aprovado_por': u.get('aprovado_por'),
        })
    out.sort(key=lambda x: (x.get('status') != 'pendente', x.get('nome', '')))
    return jsonify({'total': len(out), 'usuarios': out})


def handle_aprovar(matricula, aprovador):
    users = users_load()
    u = users.get(matricula)
    if not u:
        return jsonify({'error': 'Usuario nao encontrado'}), 404
    if u.get('status') == 'aprovado':
        return jsonify({'ok': True, 'mensagem': 'Ja estava aprovado'})
    u['status'] = 'aprovado'
    u['aprovado_em'] = time.time()
    u['aprovado_por'] = aprovador['matricula']
    users_save(users)
    return jsonify({'ok': True, 'mensagem': 'Cadastro aprovado'})


def handle_negar(matricula, aprovador):
    users = users_load()
    u = users.get(matricula)
    if not u:
        return jsonify({'error': 'Usuario nao encontrado'}), 404
    if u.get('role') == 'admin':
        return jsonify({'error': 'Nao e possivel negar o admin'}), 403
    if u.get('status') != 'pendente':
        return jsonify({'error': 'Apenas cadastros pendentes podem ser negados'}), 400
    u['status'] = 'negado'
    u['negado_em'] = time.time()
    u['negado_por'] = aprovador['matricula']
    users_save(users)
    return jsonify({'ok': True, 'mensagem': 'Cadastro negado'})


def handle_promover(matricula, admin):
    users = users_load()
    u = users.get(matricula)
    if not u:
        return jsonify({'error': 'Usuario nao encontrado'}), 404
    if u.get('status') != 'aprovado':
        return jsonify({'error': 'Usuario precisa estar aprovado primeiro'}), 400
    if u.get('role') == 'admin':
        return jsonify({'error': 'Ja e admin'}), 400
    if u.get('role') == 'aprovador':
        return jsonify({'ok': True, 'mensagem': 'Ja era aprovador'})
    aprovadores_atuais = sum(1 for x in users.values() if x.get('role') == 'aprovador')
    if aprovadores_atuais >= MAX_APROVADORES:
        return jsonify({'error': f'Limite de {MAX_APROVADORES} aprovadores atingido. Despromova outro antes.'}), 400
    u['role'] = 'aprovador'
    users_save(users)
    return jsonify({'ok': True, 'mensagem': u.get('nome') + ' agora pode aprovar cadastros'})


def handle_despromover(matricula, admin):
    users = users_load()
    u = users.get(matricula)
    if not u:
        return jsonify({'error': 'Usuario nao encontrado'}), 404
    if u.get('role') == 'admin':
        return jsonify({'error': 'Nao e possivel despromover o admin'}), 403
    if u.get('role') != 'aprovador':
        return jsonify({'error': 'Usuario nao e aprovador'}), 400
    u['role'] = 'user'
    users_save(users)
    return jsonify({'ok': True, 'mensagem': 'Permissao removida'})
