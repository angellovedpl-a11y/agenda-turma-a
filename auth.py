"""Sistema de autenticacao Agenda Turma A.
- Matricula: 6 a 10 digitos
- Senha: 4 digitos
- Primeiro registro vira admin automaticamente
- Admin pode promover ate 3 aprovadores adicionais (total 4 podem aprovar)
- Cadastros novos ficam pendentes ate aprovacao
- Sessoes via token (uuid) salvas em data/sessions.json (validade 30 dias)
"""
import os, json, hashlib, hmac, secrets, time, re
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify
try:
    import bcrypt
    _BCRYPT_AVAILABLE = True
except ImportError:
    _BCRYPT_AVAILABLE = False

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

FUNCOES_VALIDAS = [
    'Função Operacional',
    'Função Administrativa',
]
FUNCOES_OBRIGADAS_PRONTOS = {
    'Função Operacional',
}


def validar_email(e: str) -> bool:
    return bool(e and len(e) <= 120 and EMAIL_RE.match(e))


def validar_funcao(f: str) -> bool:
    return f in FUNCOES_VALIDAS


def obrigado_prontos(funcao: str) -> bool:
    return funcao in FUNCOES_OBRIGADAS_PRONTOS

import kvstore

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
USERS_PATH = os.path.join(DATA_DIR, 'users.json')
SESSIONS_PATH = os.path.join(DATA_DIR, 'sessions.json')

SESSION_DAYS = 30
MAX_APROVADORES = 3  # alem do admin

MATRICULA_RE = re.compile(r'^\d{6,10}$')
SENHA_RE = re.compile(r'^\d{4}$')

LEGAL_TERMS_VERSION = '1.0'
LEGAL_POLICY_VERSION = '1.0'
LEGAL_AUDIT_KEY = 'legal_acceptance_audit'


def users_load():
    return kvstore.load('users')


def users_save(data):
    kvstore.save('users', data)


def sessions_load():
    return kvstore.load('sessions')


def sessions_save(data):
    kvstore.save('sessions', data)


def _legal_now():
    ts = time.time()
    iso = datetime.fromtimestamp(ts, timezone.utc).isoformat().replace('+00:00', 'Z')
    return ts, iso


def legal_acceptance_current(user) -> bool:
    acc = (user or {}).get('legal_acceptance') or {}
    return (
        acc.get('terms_version') == LEGAL_TERMS_VERSION and
        acc.get('policy_version') == LEGAL_POLICY_VERSION
    )


def _legal_user_fields(user) -> dict:
    acc = (user or {}).get('legal_acceptance') or {}
    return {
        'legal_acceptance_required': not legal_acceptance_current(user),
        'legal_terms_version': LEGAL_TERMS_VERSION,
        'legal_policy_version': LEGAL_POLICY_VERSION,
        'legal_acceptance': {
            'terms_version': acc.get('terms_version'),
            'policy_version': acc.get('policy_version'),
            'accepted_at': acc.get('accepted_at'),
            'accepted_at_iso': acc.get('accepted_at_iso'),
        } if acc else None,
    }


def _acceptance_truthy(value) -> bool:
    return value is True or str(value).strip().lower() in ('1', 'true', 'on', 'yes', 'sim')


def _hash_for_audit(value: str):
    salt = os.environ.get('LEGAL_AUDIT_SALT', '').strip()
    if not value or len(salt) < 16:
        return None
    return hmac.new(salt.encode('utf-8'), str(value).encode('utf-8'), hashlib.sha256).hexdigest()


def _client_ip_for_hash():
    forwarded = (request.headers.get('X-Forwarded-For') or '').split(',')[0].strip()
    return forwarded or request.headers.get('X-Real-IP', '').strip() or getattr(request, 'remote_addr', '') or ''


def _new_legal_acceptance(origin: str) -> dict:
    ts, iso = _legal_now()
    return {
        'terms_version': LEGAL_TERMS_VERSION,
        'policy_version': LEGAL_POLICY_VERSION,
        'accepted_at': ts,
        'accepted_at_iso': iso,
        'origin': origin,
    }


def _new_legal_audit_entry(matricula: str, origin: str, accepted_at: float, accepted_at_iso: str) -> dict:
    entry = {
        'matricula': str(matricula),
        'terms_version': LEGAL_TERMS_VERSION,
        'policy_version': LEGAL_POLICY_VERSION,
        'accepted_at': accepted_at,
        'accepted_at_iso': accepted_at_iso,
        'origin': origin,
    }
    ip_hash = _hash_for_audit(_client_ip_for_hash())
    ua_hash = _hash_for_audit(request.headers.get('User-Agent', ''))
    if ip_hash:
        entry['ip_hash'] = ip_hash
    if ua_hash:
        entry['user_agent_hash'] = ua_hash
    return entry


def _append_legal_audit(entry: dict) -> bool:
    try:
        with kvstore.with_lock(LEGAL_AUDIT_KEY) as conn:
            data = kvstore.load(LEGAL_AUDIT_KEY, conn=conn)
            entries = data.get('entries') if isinstance(data, dict) else None
            if not isinstance(entries, list):
                entries = []
            entries.append(entry)
            return kvstore.save(LEGAL_AUDIT_KEY, {'entries': entries}, conn=conn)
    except Exception as e:
        print(f'[legal] falha ao gravar auditoria de aceite: {e}')
        return False


def _mark_legal_acceptance(users: dict, matricula: str, origin: str) -> dict:
    acceptance = _new_legal_acceptance(origin)
    users[matricula]['legal_acceptance'] = acceptance
    return acceptance


def _hash_sha256_legado(matricula: str, senha: str) -> str:
    salt = ('turmaA_' + matricula).encode('utf-8')
    return hashlib.sha256(salt + senha.encode('utf-8')).hexdigest()


def hash_senha(matricula: str, senha: str) -> str:
    if _BCRYPT_AVAILABLE:
        combined = (matricula + ':' + senha).encode('utf-8')
        return bcrypt.hashpw(combined, bcrypt.gensalt(rounds=12)).decode('utf-8')
    return _hash_sha256_legado(matricula, senha)


def verificar_senha(matricula: str, senha: str, stored_hash: str) -> bool:
    if _BCRYPT_AVAILABLE and stored_hash.startswith('$2'):
        combined = (matricula + ':' + senha).encode('utf-8')
        return bcrypt.checkpw(combined, stored_hash.encode('utf-8'))
    return stored_hash == _hash_sha256_legado(matricula, senha)


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


def session_destroy_all_for(matricula: str):
    """Revoga todas as sessões de uma matrícula (usado em reset/troca de senha)."""
    sessions = sessions_load()
    novos = {t: v for t, v in sessions.items() if v.get('matricula') != matricula}
    if len(novos) != len(sessions):
        sessions_save(novos)


def get_token_from_request():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:].strip()
    h = request.headers.get('X-Auth-Token', '').strip()
    if h:
        return h
    # Fallback: query param `t` (necessario pra <img src="..."> e downloads,
    # que nao permitem header customizado). Soh use em GET de recurso privado.
    q = (request.args.get('t') or '').strip()
    return q or None


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


def is_owner(user) -> bool:
    return bool(user and user.get('owner'))


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
        if not legal_acceptance_current(u):
            return jsonify({
                'error': 'legal_acceptance_required',
                'mensagem': 'Aceite os Termos de Uso e a Politica de Seguranca para continuar.',
                'legal_terms_version': LEGAL_TERMS_VERSION,
                'legal_policy_version': LEGAL_POLICY_VERSION,
            }), 428
        request.current_user = u
        return fn(*a, **kw)
    return wrapped


def require_auth_allow_pending_legal(fn):
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
        if not legal_acceptance_current(u):
            return jsonify({
                'error': 'legal_acceptance_required',
                'mensagem': 'Aceite os Termos de Uso e a Politica de Seguranca para continuar.',
                'legal_terms_version': LEGAL_TERMS_VERSION,
                'legal_policy_version': LEGAL_POLICY_VERSION,
            }), 428
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
        if not legal_acceptance_current(u):
            return jsonify({
                'error': 'legal_acceptance_required',
                'mensagem': 'Aceite os Termos de Uso e a Politica de Seguranca para continuar.',
                'legal_terms_version': LEGAL_TERMS_VERSION,
                'legal_policy_version': LEGAL_POLICY_VERSION,
            }), 428
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
    funcao = (data.get('funcao') or '').strip()
    if not _acceptance_truthy(data.get('aceita_termos')):
        return jsonify({'error': 'Aceite os termos de uso e a politica de seguranca para cadastrar'}), 400
    if not validar_matricula(matricula):
        return jsonify({'error': 'A matricula deve ter de 6 a 10 digitos'}), 400
    if not validar_senha(senha):
        return jsonify({'error': 'A senha deve ter exatamente 4 digitos'}), 400
    if not nome or len(nome) < 2:
        return jsonify({'error': 'Informe seu nome (minimo 2 caracteres)'}), 400
    if not validar_funcao(funcao):
        return jsonify({'error': 'Selecione sua função na ferrovia'}), 400
    if not kvstore.health():
        return jsonify({'error': 'Banco de dados indisponivel. Tente novamente em instantes.'}), 503
    users = users_load()
    if matricula in users:
        return jsonify({'error': 'Matricula ja cadastrada. Use login ou recuperacao.'}), 409
    primeiro = (len(users) == 0)
    novo = {
        'nome': nome,
        'funcao': funcao,
        'senha_hash': hash_senha(matricula, senha),
        'status': 'aprovado' if primeiro else 'pendente',
        'role': 'admin' if primeiro else 'user',
        'owner': True if primeiro else False,
        'criado_em': time.time(),
        'aprovado_em': time.time() if primeiro else None,
        'aprovado_por': 'auto-admin' if primeiro else None,
    }
    users[matricula] = novo
    acceptance = _mark_legal_acceptance(users, matricula, 'cadastro')
    users_save(users)
    _append_legal_audit(_new_legal_audit_entry(
        matricula, 'cadastro', acceptance['accepted_at'], acceptance['accepted_at_iso']
    ))
    if not primeiro:
        try:
            import notify
            notify.notificar_novo_cadastro(matricula, nome)
        except Exception as e:
            print(f'[auth] falha ao notificar aprovadores: {e}')
    if primeiro:
        token = session_create(matricula)
        user_payload = {'matricula': matricula, 'nome': nome, 'role': 'admin'}
        user_payload.update(_legal_user_fields(users[matricula]))
        return jsonify({'ok': True, 'admin': True, 'token': token,
                        'mensagem': 'Bem-vindo, administrador! Voce e o primeiro usuario.',
                        'user': user_payload})
    return jsonify({'ok': True, 'pendente': True,
                    'mensagem': 'Cadastro recebido! Aguarde aprovacao de um administrador.'})


def handle_login(data):
    matricula = (data.get('matricula') or '').strip()
    senha = (data.get('senha') or '').strip()
    if not validar_matricula(matricula) or not validar_senha(senha):
        return jsonify({'error': 'Matricula (6 a 10 digitos) ou senha (4 digitos) invalidas'}), 400
    # raise_on_error=True para distinguir "DB fora do ar" (503) de "credencial errada" (401).
    # Antes, qualquer falha de DB retornava {} silenciosamente e o user via "senha incorreta"
    # mesmo digitando os dados corretos (caso classico: conexao SSL morta no pool).
    try:
        users = kvstore.load('users', raise_on_error=True)
    except kvstore.KVStoreError as e:
        print(f'[handle_login] DB indisponivel: {e}')
        return jsonify({'error': 'Servidor temporariamente indisponivel, tente novamente em instantes'}), 503
    u = users.get(matricula)
    if not u:
        return jsonify({'error': 'Matricula ou senha incorretas'}), 401
    if not verificar_senha(matricula, senha, u.get('senha_hash', '')):
        return jsonify({'error': 'Matricula ou senha incorretas'}), 401
    if _BCRYPT_AVAILABLE and not u.get('senha_hash', '').startswith('$2'):
        u['senha_hash'] = hash_senha(matricula, senha)
        users_save(users)
    if u.get('status') == 'pendente':
        return jsonify({'error': 'Cadastro pendente de aprovacao do administrador'}), 403
    if u.get('status') == 'negado':
        return jsonify({'error': 'Cadastro negado pelo administrador'}), 403
    token = session_create(matricula)
    user_payload = {
        'matricula': matricula, 'nome': u.get('nome'), 'role': u.get('role', 'user'),
        'funcao': u.get('funcao', '') if u.get('funcao', '') in FUNCOES_VALIDAS else '',
        'obrigado_prontos': obrigado_prontos(u.get('funcao', ''))
    }
    user_payload.update(_legal_user_fields(u))
    return jsonify({'ok': True, 'token': token, 'user': user_payload})


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
    funcao = u.get('funcao', '')
    if funcao and funcao not in FUNCOES_VALIDAS:
        funcao = ''
    return jsonify({
        'authenticated': True,
        'matricula': u['matricula'],
        'nome': u.get('nome'),
        'role': u.get('role', 'user'),
        'pode_aprovar': can_approve(u),
        'pendentes': pendentes,
        'senha_temp': bool(u.get('senha_temp')),
        'email': u.get('email', ''),
        'funcao': funcao,
        'obrigado_prontos': obrigado_prontos(funcao),
        'funcoes_disponiveis': FUNCOES_VALIDAS,
        **_legal_user_fields(u),
    })


def handle_legal_acceptance(data, user):
    if not _acceptance_truthy(data.get('accepted')):
        return jsonify({'error': 'Aceite os Termos de Uso e a Politica de Seguranca para continuar'}), 400
    users = users_load()
    matricula = user.get('matricula')
    u = users.get(matricula)
    if not u:
        return jsonify({'error': 'Usuario nao encontrado'}), 404
    if not legal_acceptance_current(u):
        acceptance = _mark_legal_acceptance(users, matricula, 'login')
        users_save(users)
        _append_legal_audit(_new_legal_audit_entry(
            matricula, 'login', acceptance['accepted_at'], acceptance['accepted_at_iso']
        ))
        u = users.get(matricula, u)
    payload = _legal_user_fields(u)
    payload.update({'ok': True})
    return jsonify(payload)


def handle_set_funcao(data, user):
    funcao = (data.get('funcao') or '').strip()
    if not validar_funcao(funcao):
        return jsonify({'error': 'Função inválida'}), 400
    users = users_load()
    u = users.get(user['matricula'])
    if not u:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    u['funcao'] = funcao
    users_save(users)
    return jsonify({'ok': True, 'funcao': funcao, 'obrigado_prontos': obrigado_prontos(funcao),
                    'mensagem': 'Função atualizada!'})


def handle_set_email(data, user):
    email = (data.get('email') or '').strip().lower()
    users = users_load()
    u = users.get(user['matricula'])
    if not u:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    if email == '':
        u.pop('email', None)
        users_save(users)
        return jsonify({'ok': True, 'mensagem': 'E-mail removido. Você não receberá mais notificações.', 'email': ''})
    if not validar_email(email):
        return jsonify({'error': 'E-mail inválido. Use o formato nome@dominio.com'}), 400
    u['email'] = email
    users_save(users)
    return jsonify({'ok': True, 'mensagem': 'E-mail salvo com sucesso!', 'email': email})


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
    if u.get('owner') or u.get('role') == 'admin':
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


def _normaliza_nome(s: str) -> str:
    if not s:
        return ''
    s = s.strip().lower()
    import unicodedata
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'\s+', ' ', s)
    return s


def _gera_senha_temp() -> str:
    return ''.join(secrets.choice('0123456789') for _ in range(4))


def handle_recuperar_senha(data):
    """Auto-recuperação: usuário informa matrícula + nome cadastrado.
    Se bater, gera senha temporária de 4 dígitos e retorna uma única vez.
    Senha original NUNCA é revelada (é hash). Esta é a forma do Viriato 'resolver'.
    """
    matricula = (data.get('matricula') or '').strip()
    nome = (data.get('nome') or '').strip()
    if not validar_matricula(matricula):
        return jsonify({'error': 'Matrícula precisa ter de 6 a 10 dígitos'}), 400
    if not nome or len(nome) < 2:
        return jsonify({'error': 'Informe o nome completo cadastrado'}), 400
    users = users_load()
    u = users.get(matricula)
    # resposta genérica para não vazar quem está cadastrado
    erro_generico = jsonify({'error': 'Não consegui confirmar sua identidade. Confira matrícula e nome completo cadastrado, ou peça ao Angelo para resetar.'}), 404
    if not u:
        return erro_generico
    if u.get('status') != 'aprovado':
        return jsonify({'error': 'Seu cadastro ainda não foi aprovado pelo administrador.'}), 403
    if _normaliza_nome(u.get('nome', '')) != _normaliza_nome(nome):
        return erro_generico
    nova = _gera_senha_temp()
    u['senha_hash'] = hash_senha(matricula, nova)
    u['senha_temp'] = True
    u['senha_resetada_em'] = time.time()
    u['senha_resetada_por'] = 'auto-viriato'
    users_save(users)
    session_destroy_all_for(matricula)
    return jsonify({'ok': True, 'mensagem': 'Identidade confirmada! Senha temporária criada.',
                    'senha_temp': nova, 'matricula': matricula, 'nome': u.get('nome')})


def handle_trocar_senha(data, user):
    atual = (data.get('atual') or '').strip()
    nova = (data.get('nova') or '').strip()
    if not validar_senha(atual) or not validar_senha(nova):
        return jsonify({'error': 'Senha atual e nova devem ter 4 dígitos'}), 400
    if atual == nova:
        return jsonify({'error': 'A nova senha precisa ser diferente da atual'}), 400
    users = users_load()
    u = users.get(user['matricula'])
    if not u or not verificar_senha(user['matricula'], atual, u.get('senha_hash', '')):
        return jsonify({'error': 'Senha atual incorreta'}), 401
    u['senha_hash'] = hash_senha(user['matricula'], nova)
    u['senha_temp'] = False
    u['senha_trocada_em'] = time.time()
    users_save(users)
    # Revoga TODAS as sessões antigas e cria uma nova só pra este usuário
    session_destroy_all_for(user['matricula'])
    novo_token = session_create(user['matricula'])
    return jsonify({'ok': True, 'mensagem': 'Senha trocada com sucesso', 'novo_token': novo_token})


def handle_admin_reset_senha(matricula, admin):
    users = users_load()
    u = users.get(matricula)
    if not u:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    if u.get('owner') and admin.get('matricula') != matricula:
        return jsonify({'error': 'Apenas o próprio dono pode resetar sua senha'}), 403
    if u.get('status') != 'aprovado':
        return jsonify({'error': 'Usuário precisa estar aprovado'}), 400
    nova = _gera_senha_temp()
    u['senha_hash'] = hash_senha(matricula, nova)
    u['senha_temp'] = True
    u['senha_resetada_em'] = time.time()
    u['senha_resetada_por'] = admin['matricula']
    users_save(users)
    session_destroy_all_for(matricula)
    return jsonify({'ok': True, 'senha_temp': nova,
                    'mensagem': 'Senha temporária criada. Passe ' + nova + ' para ' + u.get('nome', '') + ' (peça pra trocar no primeiro login).'})


def handle_despromover(matricula, admin):
    users = users_load()
    u = users.get(matricula)
    if not u:
        return jsonify({'error': 'Usuario nao encontrado'}), 404
    if u.get('owner') or u.get('role') == 'admin':
        return jsonify({'error': 'Nao e possivel despromover o admin'}), 403
    if u.get('role') != 'aprovador':
        return jsonify({'error': 'Usuario nao e aprovador'}), 400
    u['role'] = 'user'
    users_save(users)
    return jsonify({'ok': True, 'mensagem': 'Permissao removida'})
