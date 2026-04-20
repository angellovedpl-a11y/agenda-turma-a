from flask import Flask, send_from_directory, request, jsonify
import os
from anthropic import Anthropic

app = Flask(__name__, static_folder='.')

# Replit AI Integrations — Anthropic (no API key from user required)
_anthropic_client = Anthropic(
    api_key=os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY", "dummy"),
    base_url=os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/claude', methods=['POST'])
def claude_chat():
    try:
        data = request.json or {}
        messages = data.get('messages', [])
        system = data.get('system', '')
        if not messages:
            return jsonify({'error': 'Nenhuma mensagem enviada'}), 400
        response = _anthropic_client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=8192,
            system=system,
            messages=messages
        )
        return jsonify({'text': response.content[0].text})
    except Exception as e:
        err = str(e)
        if "FREE_CLOUD_BUDGET_EXCEEDED" in err:
            return jsonify({'error': 'Limite de créditos Replit AI atingido.'}), 429
        return jsonify({'error': err}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
