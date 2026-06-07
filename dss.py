"""Modulo DSS (Dialogo de Seguranca e Saude) — Agenda Turma A.

Programa mensal de apresentacoes de DSS da turma:
- supervisor/aprovador escala pessoas com antecedencia (por matricula);
- a pessoa escalada monta o card de exportacao (WhatsApp) e sobe a apresentacao;
- supervisor confirma a realizacao no dia -> vai pro historico (auditavel)
  e gera um evento na agenda da turma.

Dados ficam em kvstore na chave "dss":
    { "escala": [...], "historico": [...] }

Toda escrita acontece dentro de kvstore.with_lock('dss') para evitar
condicoes de corrida (varios supervisores mexendo ao mesmo tempo).
"""
import re
import uuid
from datetime import datetime, date, timezone

from flask import jsonify

import kvstore
import auth

KEY = 'dss'

MAT_RE = re.compile(r'^\d{6,10}$')
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
TOM_OK = {'Direto', 'Educativo', 'Alerta', 'Motivacional'}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _today():
    return date.today().isoformat()


def _gid():
    return uuid.uuid4().hex[:12]


def _normalize(d):
    if not isinstance(d, dict):
        d = {}
    escala = d.get('escala')
    historico = d.get('historico')
    return {
        'escala': escala if isinstance(escala, list) else [],
        'historico': historico if isinstance(historico, list) else [],
    }


def load_all(conn=None):
    return _normalize(kvstore.load(KEY, conn=conn))


def _find(lst, eid):
    return next((x for x in lst if x.get('id') == eid), None)


def _empregado(matricula):
    """Busca o empregado no cadastro do app. Retorna o dict do user ou None."""
    users = auth.users_load() or {}
    u = users.get(matricula)
    if not u or u.get('status') != 'aprovado':
        return None
    return u


# ---------------------------------------------------------------- leitura
def handle_get():
    """GET /api/dss — escala + historico para o mural (qualquer aprovado)."""
    return jsonify(load_all())


def handle_lookup(matricula):
    """GET /api/dss/usuario/<matricula> — resolve nome/funcao (aprovador)."""
    matricula = (matricula or '').strip()
    if not MAT_RE.match(matricula):
        return jsonify({'error': 'matricula_invalida'}), 400
    u = _empregado(matricula)
    if not u:
        return jsonify({'error': 'nao_encontrado'}), 404
    return jsonify({
        'matricula': matricula,
        'nome': u.get('nome') or '',
        'funcao': u.get('funcao') or '',
    })


def handle_buscar(q):
    """GET /api/dss/buscar?q=... — busca empregados por nome OU matricula (admin)."""
    q = (q or '').strip().lower()
    if len(q) < 2:
        return jsonify({'results': []})
    users = auth.users_load() or {}
    out = []
    for mat, u in users.items():
        if not isinstance(u, dict) or u.get('status') != 'aprovado':
            continue
        nome = u.get('nome') or ''
        if q in mat.lower() or q in nome.lower():
            out.append({'matricula': mat, 'nome': nome, 'funcao': u.get('funcao') or ''})
    out.sort(key=lambda x: (x['nome'] or '').lower())
    return jsonify({'results': out[:12]})


# ---------------------------------------------------------------- escrita
def handle_escalar(data, user):
    """POST /api/dss/escala — escala uma pessoa (aprovador)."""
    data = data or {}
    matricula = (data.get('matricula') or '').strip()
    data_prevista = (data.get('data_prevista') or data.get('data') or '').strip()
    tema = (data.get('tema') or '').strip()[:120]
    descricao = (data.get('descricao') or '').strip()[:2000]
    tom = (data.get('tom') or 'Direto').strip()
    if tom not in TOM_OK:
        tom = 'Direto'

    if not MAT_RE.match(matricula):
        return jsonify({'error': 'matricula_invalida',
                        'mensagem': 'Matricula deve ter 6 a 10 digitos'}), 400
    if not DATE_RE.match(data_prevista):
        return jsonify({'error': 'data_invalida',
                        'mensagem': 'Informe a data (YYYY-MM-DD)'}), 400
    u = _empregado(matricula)
    if not u:
        return jsonify({'error': 'empregado_nao_encontrado',
                        'mensagem': 'Matricula nao encontrada no cadastro'}), 404

    entry = {
        'id': _gid(),
        'matricula': matricula,
        'nome': u.get('nome') or '',
        'data_prevista': data_prevista,
        'tema': tema,
        'descricao': descricao,
        'tom': tom,
        'status': 'pendente',          # pendente | card_pronto | revisado
        'card': None,                  # textos gerados (titulo/bullets/fala/pergunta/tom)
        'card_img_key': None,          # imagem do card de exportacao (object_storage)
        'card_img_mime': None,         # mimetype da imagem do card
        'ppt_key': None,               # arquivo de apresentacao original
        'ppt_pdf_key': None,           # apresentacao convertida p/ PDF
        'escalado_por': (user or {}).get('matricula'),
        'criado_em': _now(),
    }
    with kvstore.with_lock(KEY) as conn:
        d = load_all(conn=conn)
        d['escala'].append(entry)
        kvstore.save(KEY, d, conn=conn)
    return jsonify({'ok': True, 'item': entry})


def handle_remover(eid, user):
    """DELETE /api/dss/escala/<id> — remove da escala (aprovador)."""
    with kvstore.with_lock(KEY) as conn:
        d = load_all(conn=conn)
        antes = len(d['escala'])
        d['escala'] = [x for x in d['escala'] if x.get('id') != eid]
        if len(d['escala']) == antes:
            return jsonify({'error': 'nao_encontrado'}), 404
        kvstore.save(KEY, d, conn=conn)
    return jsonify({'ok': True})


def handle_confirmar(eid, user, create_event=None):
    """POST /api/dss/<id>/confirmar — verifica a DSS (admin/aprovador).

    Move a entrada da escala para o historico (append-only) usando a DATA
    REAL do clique e guarda a data prevista. Se `create_event` for passado,
    cria o evento na agenda da turma e guarda o id retornado.
    """
    with kvstore.with_lock(KEY) as conn:
        d = load_all(conn=conn)
        item = _find(d['escala'], eid)
        if not item:
            return jsonify({'error': 'nao_encontrado'}), 404

        data_real = _today()
        evento_id = None
        if create_event:
            try:
                evento_id = create_event(item, data_real)
            except Exception as e:
                print(f'[dss] falha ao criar evento na agenda: {e}')
                evento_id = None

        hist = {
            'id': _gid(),
            'matricula': item.get('matricula'),
            'nome': item.get('nome'),
            'tema': item.get('tema') or 'Tema nao informado',
            'data_prevista': item.get('data_prevista'),
            'data_real': data_real,
            'verificado_por': (user or {}).get('matricula'),
            'evento_id': evento_id,
            'criado_em': _now(),
        }
        d['historico'].insert(0, hist)
        d['escala'] = [x for x in d['escala'] if x.get('id') != eid]
        kvstore.save(KEY, d, conn=conn)
    return jsonify({'ok': True, 'historico': hist})


# ---------------------------------------------------------------- Fase 2: card
def can_edit(item, user):
    """O card so pode ser montado pela pessoa escalada ou por um admin."""
    if not item or not user:
        return False
    if user.get('role') == 'admin':
        return True
    return str(user.get('matricula') or '') == str(item.get('matricula') or '')


def get_item(eid):
    """Retorna o item da escala (nao do historico) ou None — sem lock, so leitura."""
    return _find(load_all()['escala'], eid)


def _sanitize_card(card):
    """Normaliza o card (autoria manual da pessoa) para formato seguro/limitado."""
    if not isinstance(card, dict):
        card = {}
    bullets = card.get('bullets')
    if not isinstance(bullets, list):
        bullets = []
    bullets = [re.sub(r'\s+', ' ', str(b)).strip()[:160]
               for b in bullets if str(b).strip()][:5]
    return {
        'titulo': re.sub(r'\s+', ' ', str(card.get('titulo') or '')).strip()[:80],
        'bullets': bullets,
        'fala': re.sub(r'\s+', ' ', str(card.get('fala') or '')).strip()[:400],
        'pergunta': re.sub(r'\s+', ' ', str(card.get('pergunta') or '')).strip()[:200],
    }


def handle_save_card(eid, data, user):
    """POST /api/dss/<id>/card — salva o card escrito pela propria pessoa."""
    data = data or {}
    card_in = data.get('card') if isinstance(data.get('card'), dict) else data
    with kvstore.with_lock(KEY) as conn:
        d = load_all(conn=conn)
        item = _find(d['escala'], eid)
        if not item:
            return jsonify({'error': 'nao_encontrado'}), 404
        if not can_edit(item, user):
            return jsonify({'error': 'sem_permissao'}), 403
        card = _sanitize_card(card_in)
        if not card['titulo']:
            card['titulo'] = item.get('tema') or 'Dialogo de Seguranca'
        item['card'] = card
        if item.get('status') == 'pendente':
            item['status'] = 'card_pronto'
        kvstore.save(KEY, d, conn=conn)
    return jsonify({'ok': True, 'card': card})


def handle_set_card_img(eid, key, mimetype, user):
    """Aponta o item para a imagem ja enviada ao object_storage.
    Retorna a chave anterior (se houver) para o caller limpar o orfao."""
    with kvstore.with_lock(KEY) as conn:
        d = load_all(conn=conn)
        item = _find(d['escala'], eid)
        if not item:
            return None, jsonify({'error': 'nao_encontrado'}), 404
        if not can_edit(item, user):
            return None, jsonify({'error': 'sem_permissao'}), 403
        old = item.get('card_img_key')
        item['card_img_key'] = key
        item['card_img_mime'] = mimetype
        kvstore.save(KEY, d, conn=conn)
    return (old if old and old != key else None), jsonify({'ok': True}), 200


def handle_clear_card_img(eid, user):
    """Remove a imagem do card. Retorna a chave antiga p/ o caller deletar."""
    with kvstore.with_lock(KEY) as conn:
        d = load_all(conn=conn)
        item = _find(d['escala'], eid)
        if not item:
            return None, jsonify({'error': 'nao_encontrado'}), 404
        if not can_edit(item, user):
            return None, jsonify({'error': 'sem_permissao'}), 403
        old = item.get('card_img_key')
        item['card_img_key'] = None
        item['card_img_mime'] = None
        kvstore.save(KEY, d, conn=conn)
    return old, jsonify({'ok': True}), 200
