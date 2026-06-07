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
        'card': None,                  # textos gerados (titulo/bullets/fala/pergunta)
        'card_img_key': None,          # imagem do card de exportacao
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
