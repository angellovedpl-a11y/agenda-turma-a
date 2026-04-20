from flask import Flask, send_from_directory, request, jsonify
import os
import json
from datetime import datetime
from anthropic import Anthropic

app = Flask(__name__, static_folder='.')

# === MEM PALACE ===
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

SALAS = ['escala', 'eventos', 'documentos', 'checklist', 'biblioteca']

def mem_palace_load(sala: str) -> dict:
    path = os.path.join(DATA_DIR, f'{sala}.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def mem_palace_save(sala: str, data: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f'{sala}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def mem_palace_context(data: dict, date_str: str = None) -> str:
    parts = []
    for sala in SALAS:
        d = mem_palace_load(sala)
        if d:
            parts.append(f"[{sala.upper()}] {json.dumps(d, ensure_ascii=False)[:800]}")
    if date_str and parts:
        parts.insert(0, f"[DATA_REFERENCIA] {date_str}")
    return '\n'.join(parts)

def docs_por_dia(date_str: str) -> list:
    docs_sala = mem_palace_load('documentos')
    tipos = docs_sala.get('tipos', [])
    return tipos

# === ANTHROPIC CLIENT (Replit AI Integrations) ===
_anthropic_client = Anthropic(
    api_key=os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY", "dummy"),
    base_url=os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
)

# === ROTAS ESTATICAS ===
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    return send_from_directory('.', path)

# === API CLAUDE COM MEM PALACE ===
@app.route('/api/claude', methods=['POST'])
def claude_chat():
    try:
        data = request.json or {}
        messages = data.get('messages', [])
        system = data.get('system', '')
        date_str = data.get('date', datetime.today().strftime('%Y-%m-%d'))

        if not messages:
            return jsonify({'error': 'Nenhuma mensagem enviada'}), 400

        palace = mem_palace_context(data, date_str)
        full_system = system + '\n\n=== MEM PALACE (MEMORIA ESTRUTURADA) ===\n' + palace if palace else system

        response = _anthropic_client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=8192,
            system=full_system,
            messages=messages
        )
        return jsonify({'text': response.content[0].text})
    except Exception as e:
        err = str(e)
        if "FREE_CLOUD_BUDGET_EXCEEDED" in err:
            return jsonify({'error': 'Limite de creditos Replit AI atingido.'}), 429
        return jsonify({'error': err}), 500

# === API BIBLIOTECA ===
@app.route('/api/biblioteca', methods=['GET'])
def biblioteca():
    data = mem_palace_load('biblioteca')
    return jsonify(data)

@app.route('/api/biblioteca/<tipo>', methods=['GET'])
def biblioteca_tipo(tipo):
    data = mem_palace_load('biblioteca')
    if tipo == 'regulamentos':
        return jsonify(data.get('regulamentos', []))
    elif tipo == 'boletins':
        return jsonify(data.get('boletins', []))
    else:
        item = next((r for r in data.get('regulamentos', []) if r['id'] == tipo), None)
        if not item:
            item = next((b for b in data.get('boletins', []) if b['id'] == tipo), None)
        if item:
            return jsonify(item)
        return jsonify({'error': 'Item nao encontrado'}), 404

# === API DOCS POR DIA ===
@app.route('/api/docs/<date_str>', methods=['GET'])
def docs_dia(date_str):
    docs = docs_por_dia(date_str)
    return jsonify({'data': date_str, 'documentos': docs})

# === API MEM PALACE CRUD ===
@app.route('/api/mem/<sala>', methods=['GET'])
def mem_get(sala):
    if sala not in SALAS:
        return jsonify({'error': 'Sala invalida'}), 400
    return jsonify(mem_palace_load(sala))

@app.route('/api/mem/<sala>', methods=['POST'])
def mem_update(sala):
    if sala not in SALAS:
        return jsonify({'error': 'Sala invalida'}), 400
    try:
        data = request.json or {}
        existing = mem_palace_load(sala)
        existing.update(data)
        mem_palace_save(sala, existing)
        return jsonify({'ok': True, 'sala': sala})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
