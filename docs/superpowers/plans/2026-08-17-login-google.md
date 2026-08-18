# Login com Google (opção adicional) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar "Entrar com Google" como opção extra de login, sem mexer no login matrícula+senha existente.

**Architecture:** Frontend usa Google Identity Services (GIS) para obter um ID token; o backend Flask valida esse token com `google-auth` (já instalado), casa o `sub` do Google com uma matrícula já existente e emite a sessão normal. Vínculo 1:1 gravado no registro do usuário no kvstore. Google é 100% aditivo e degrada graciosamente (botão só aparece se `GOOGLE_CLIENT_ID` estiver configurado).

**Tech Stack:** Python 3.11 / Flask / kvstore (Postgres) no backend; SPA vanilla JS (`static/app.js`) no frontend; `google-auth==2.49.2` (já em `requirements.txt`); Google Identity Services (script `https://accounts.google.com/gsi/client`).

## Global Constraints

- **Google é opcional, nunca obrigatório.** Login matrícula+senha (`/api/auth/login`) permanece inalterado e funcional.
- **Identidade = matrícula.** Google só aponta para matrícula já existente; não cria cadastro.
- **Vínculo 1:1:** um `google_sub` pertence no máximo a uma matrícula.
- **Vínculo por `sub`** (claim estável), nunca por e-mail.
- **Sessão só para `status == 'aprovado'`** (mesma regra de hoje).
- **Sem dependência nova:** usar `google-auth` já presente. NÃO adicionar libs.
- **Sem mudança no fluxo de aprovação** de novos cadastros (opção A).
- Token do Google **sempre validado no servidor** com `GOOGLE_CLIENT_ID` como `audience`.
- Padrão de teste do projeto: `unittest` com `flask` e `kvstore` fakes injetados em `sys.modules` (ver `tests/test_legal_acceptance.py`). Rodar: `python -m pytest tests/ -v` ou `python -m unittest`.
- Rodar Python local no Windows: `set PYTHONUTF8=1` antes (cp1252 quebra acento).

---

### Task 1: Backend — validação do token do Google + config

**Files:**
- Modify: `auth.py` (adicionar imports, `GOOGLE_CLIENT_ID`, `GoogleAuthError`, `google_login_habilitado`, `verificar_google_token`)
- Modify: `server.py` (rota `GET /api/auth/google/client-id`)
- Test: `tests/test_google_auth.py` (novo)

**Interfaces:**
- Produces:
  - `auth.GOOGLE_CLIENT_ID: str`
  - `auth.GoogleAuthError(Exception)`
  - `auth.google_login_habilitado() -> bool`
  - `auth.verificar_google_token(credential: str) -> dict` — retorna `{'sub': str, 'email': str}` ou levanta `GoogleAuthError`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/test_google_auth.py`. Reusar o boilerplate de fakes de `tests/test_legal_acceptance.py` (copiar o bloco `fake_flask`/`fake_kvstore` das linhas 9-48) e então:

```python
import auth

class VerificarGoogleTokenTests(unittest.TestCase):
    def setUp(self):
        self._orig_cid = auth.GOOGLE_CLIENT_ID
        auth.GOOGLE_CLIENT_ID = 'client-123.apps.googleusercontent.com'
        self._orig_verify = auth.google_id_token.verify_oauth2_token

    def tearDown(self):
        auth.GOOGLE_CLIENT_ID = self._orig_cid
        auth.google_id_token.verify_oauth2_token = self._orig_verify

    def test_token_valido_retorna_sub_email(self):
        auth.google_id_token.verify_oauth2_token = lambda *a, **k: {
            'iss': 'https://accounts.google.com', 'sub': '999', 'email': 'Fulano@Gmail.com'}
        info = auth.verificar_google_token('tok')
        self.assertEqual(info['sub'], '999')
        self.assertEqual(info['email'], 'fulano@gmail.com')  # normalizado minusculo

    def test_emissor_invalido_levanta(self):
        auth.google_id_token.verify_oauth2_token = lambda *a, **k: {
            'iss': 'evil.com', 'sub': '1'}
        with self.assertRaises(auth.GoogleAuthError):
            auth.verificar_google_token('tok')

    def test_token_vazio_levanta(self):
        with self.assertRaises(auth.GoogleAuthError):
            auth.verificar_google_token('')

    def test_sem_client_id_levanta(self):
        auth.GOOGLE_CLIENT_ID = ''
        with self.assertRaises(auth.GoogleAuthError):
            auth.verificar_google_token('tok')

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m unittest tests.test_google_auth -v`
Expected: FAIL — `AttributeError: module 'auth' has no attribute 'google_id_token'` (ou `verificar_google_token`).

- [ ] **Step 3: Implementar em `auth.py`**

No topo de `auth.py`, junto dos outros imports, adicionar:

```python
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
```

Perto das outras constantes/config (ex.: após `MAX_APROVADORES`):

```python
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '').strip()


class GoogleAuthError(Exception):
    """Falha ao validar o login com Google (token invalido ou nao configurado)."""


def google_login_habilitado() -> bool:
    return bool(GOOGLE_CLIENT_ID)


def verificar_google_token(credential: str) -> dict:
    """Valida o ID token do Google Identity Services.
    Retorna {'sub', 'email'} ou levanta GoogleAuthError."""
    if not GOOGLE_CLIENT_ID:
        raise GoogleAuthError('Login com Google nao esta configurado')
    if not credential or not isinstance(credential, str):
        raise GoogleAuthError('Token do Google ausente')
    try:
        info = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), GOOGLE_CLIENT_ID)
    except Exception:
        raise GoogleAuthError('Token do Google invalido')
    if info.get('iss') not in ('accounts.google.com', 'https://accounts.google.com'):
        raise GoogleAuthError('Emissor do token invalido')
    sub = info.get('sub')
    if not sub:
        raise GoogleAuthError('Token do Google sem identificador')
    return {'sub': str(sub), 'email': (info.get('email') or '').strip().lower()}
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m unittest tests.test_google_auth -v`
Expected: PASS (4 testes).

- [ ] **Step 5: Adicionar a rota pública do client-id em `server.py`**

Logo após o bloco de rotas `/api/auth/*` (após `api_me`, por volta de `server.py:2116`):

```python
@app.route('/api/auth/google/client-id', methods=['GET'])
def api_google_client_id():
    return jsonify({'clientId': auth.GOOGLE_CLIENT_ID,
                    'enabled': auth.google_login_habilitado()})
```

- [ ] **Step 6: Commit**

```bash
git add auth.py server.py tests/test_google_auth.py
git commit -m "feat(auth): validacao do token Google + rota client-id"
```

---

### Task 2: Backend — login via Google

**Files:**
- Modify: `auth.py` (`build_user_payload`, `_find_user_by_google_sub`, `handle_google_login`; refatorar `handle_login` para usar `build_user_payload`)
- Modify: `server.py` (rota `POST /api/auth/google`)
- Test: `tests/test_google_auth.py` (adicionar classe)

**Interfaces:**
- Consumes: `auth.verificar_google_token`, `auth.session_create`, `auth.admin_level`, `auth.kvstore`
- Produces:
  - `auth.build_user_payload(matricula: str, u: dict) -> dict`
  - `auth._find_user_by_google_sub(users: dict, sub: str) -> tuple[str|None, dict|None]`
  - `auth.handle_google_login(data: dict)` — Flask response. Sucesso: `{'ok': True, 'token': str, 'user': {...}}`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar em `tests/test_google_auth.py`:

```python
class GoogleLoginTests(unittest.TestCase):
    def setUp(self):
        auth.GOOGLE_CLIENT_ID = 'cid'
        auth.google_id_token.verify_oauth2_token = lambda *a, **k: {
            'iss': 'https://accounts.google.com', 'sub': 'g-1', 'email': 'a@b.com'}
        self.store = {'users': {}, 'sessions': {}}
        auth.kvstore.load = lambda key, raise_on_error=False, conn=None: self.store.get(key, {})
        def _save(key, value, raise_on_error=False, conn=None):
            self.store[key] = value; return True
        auth.kvstore.save = _save

    def _add_user(self, mat, **kw):
        u = {'nome': 'X', 'role': 'user', 'status': 'aprovado', 'senha_hash': 'h'}
        u.update(kw)
        self.store['users'][mat] = u

    def test_login_ok_usuario_aprovado_vinculado(self):
        self._add_user('123456', google_sub='g-1')
        resp = auth.handle_google_login({'credential': 'tok'})
        payload = resp[0].get_json() if isinstance(resp, tuple) else resp.get_json()
        self.assertTrue(payload.get('ok'))
        self.assertIn('token', payload)

    def test_login_google_nao_vinculado_404(self):
        resp = auth.handle_google_login({'credential': 'tok'})
        body, status = resp
        self.assertEqual(status, 404)

    def test_login_google_pendente_403(self):
        self._add_user('123456', google_sub='g-1', status='pendente')
        resp = auth.handle_google_login({'credential': 'tok'})
        body, status = resp
        self.assertEqual(status, 403)

    def test_token_invalido_400(self):
        auth.google_id_token.verify_oauth2_token = lambda *a, **k: (_ for _ in ()).throw(ValueError())
        resp = auth.handle_google_login({'credential': 'x'})
        body, status = resp
        self.assertEqual(status, 400)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m unittest tests.test_google_auth -v`
Expected: FAIL — `handle_google_login` não existe.

- [ ] **Step 3: Implementar em `auth.py`**

Extrair o payload do usuário (usado hoje inline em `handle_login`) para uma função e criar o login Google:

```python
def build_user_payload(matricula: str, u: dict) -> dict:
    payload = {
        'matricula': matricula, 'nome': u.get('nome'), 'role': u.get('role', 'user'),
        'owner': bool(u.get('owner')), 'admin_level': admin_level(u),
        'funcao': u.get('funcao', '') if u.get('funcao', '') in FUNCOES_VALIDAS else '',
        'obrigado_prontos': obrigado_prontos(u.get('funcao', '')),
        'google_conectado': bool(u.get('google_sub')),
        'google_email': u.get('google_email', ''),
    }
    payload.update(_legal_user_fields(u))
    return payload


def _find_user_by_google_sub(users: dict, sub: str):
    for mat, u in users.items():
        if u.get('google_sub') and u.get('google_sub') == sub:
            return mat, u
    return None, None


def handle_google_login(data):
    credential = (data or {}).get('credential') or ''
    try:
        info = verificar_google_token(credential)
    except GoogleAuthError as e:
        return jsonify({'error': str(e)}), 400
    try:
        users = kvstore.load('users', raise_on_error=True)
    except kvstore.KVStoreError:
        return jsonify({'error': 'Servidor temporariamente indisponivel, tente novamente em instantes'}), 503
    matricula, u = _find_user_by_google_sub(users, info['sub'])
    if not u:
        return jsonify({'error': 'Essa conta Google ainda nao esta vinculada. Entre com sua matricula e senha e conecte o Google em Configuracoes.',
                        'code': 'nao_vinculado'}), 404
    if u.get('status') == 'pendente':
        return jsonify({'error': 'Seu cadastro esta aguardando aprovacao de um supervisor.'}), 403
    if u.get('status') == 'negado':
        return jsonify({'error': 'Cadastro negado pelo administrador'}), 403
    token = session_create(matricula)
    return jsonify({'ok': True, 'token': token, 'user': build_user_payload(matricula, u)})
```

Depois, em `handle_login`, **substituir** o bloco que monta `user_payload` (as linhas de `user_payload = {...}` + `user_payload.update(_legal_user_fields(u))`) por:

```python
    token = session_create(matricula)
    return jsonify({'ok': True, 'token': token, 'user': build_user_payload(matricula, u)})
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m unittest tests.test_google_auth -v`
Expected: PASS. Também rodar a suíte toda pra garantir que o refactor de `handle_login` não quebrou nada:
Run: `python -m unittest discover tests -v`
Expected: PASS (incluindo os testes legais existentes).

- [ ] **Step 5: Adicionar a rota em `server.py`**

Após `api_login` (por volta de `server.py:2103`):

```python
@app.route('/api/auth/google', methods=['POST'])
@ratelimit.rate_limit_by_request(10, env_var='RATELIMIT_LOGIN_PER_MIN',
                                  route_key='google_login', body_key=None)
def api_google_login():
    return auth.handle_google_login(request.json or {})
```

- [ ] **Step 6: Commit**

```bash
git add auth.py server.py tests/test_google_auth.py
git commit -m "feat(auth): login via Google (sub -> matricula -> sessao)"
```

---

### Task 3: Backend — conectar / desconectar conta Google

**Files:**
- Modify: `auth.py` (`handle_google_connect`, `handle_google_disconnect`; adicionar campos google ao `handle_me`)
- Modify: `server.py` (rotas connect/disconnect)
- Test: `tests/test_google_auth.py` (adicionar classe)

**Interfaces:**
- Consumes: `auth.verificar_google_token`, `auth._find_user_by_google_sub`, `auth.users_save`
- Produces:
  - `auth.handle_google_connect(data: dict, current_user: dict)` — sucesso `{'ok': True, 'google_email': str}`
  - `auth.handle_google_disconnect(current_user: dict)` — `{'ok': True}`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar em `tests/test_google_auth.py`:

```python
class GoogleConnectTests(unittest.TestCase):
    def setUp(self):
        auth.GOOGLE_CLIENT_ID = 'cid'
        auth.google_id_token.verify_oauth2_token = lambda *a, **k: {
            'iss': 'https://accounts.google.com', 'sub': 'g-1', 'email': 'a@b.com'}
        self.store = {'users': {'123456': {'nome': 'X', 'status': 'aprovado'}}}
        auth.kvstore.load = lambda key, raise_on_error=False, conn=None: self.store.get(key, {})
        def _save(key, value, raise_on_error=False, conn=None):
            self.store[key] = value; return True
        auth.kvstore.save = _save

    def test_connect_grava_sub_email(self):
        resp = auth.handle_google_connect({'credential': 'tok'}, {'matricula': '123456'})
        payload = resp.get_json() if not isinstance(resp, tuple) else resp[0].get_json()
        self.assertTrue(payload.get('ok'))
        self.assertEqual(self.store['users']['123456']['google_sub'], 'g-1')

    def test_connect_recusa_sub_de_outra_matricula_409(self):
        self.store['users']['999999'] = {'google_sub': 'g-1'}
        resp = auth.handle_google_connect({'credential': 'tok'}, {'matricula': '123456'})
        body, status = resp
        self.assertEqual(status, 409)

    def test_disconnect_limpa_campos(self):
        self.store['users']['123456']['google_sub'] = 'g-1'
        self.store['users']['123456']['google_email'] = 'a@b.com'
        resp = auth.handle_google_disconnect({'matricula': '123456'})
        self.assertNotIn('google_sub', self.store['users']['123456'])
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m unittest tests.test_google_auth -v`
Expected: FAIL — `handle_google_connect` não existe.

- [ ] **Step 3: Implementar em `auth.py`**

```python
def handle_google_connect(data, current_user):
    credential = (data or {}).get('credential') or ''
    try:
        info = verificar_google_token(credential)
    except GoogleAuthError as e:
        return jsonify({'error': str(e)}), 400
    try:
        users = kvstore.load('users', raise_on_error=True)
    except kvstore.KVStoreError:
        return jsonify({'error': 'Servidor temporariamente indisponivel'}), 503
    matricula = current_user['matricula']
    outra, _ = _find_user_by_google_sub(users, info['sub'])
    if outra and outra != matricula:
        return jsonify({'error': 'Essa conta Google ja esta vinculada a outro usuario'}), 409
    u = users.get(matricula)
    if not u:
        return jsonify({'error': 'Usuario nao encontrado'}), 404
    u['google_sub'] = info['sub']
    u['google_email'] = info['email']
    users_save(users)
    return jsonify({'ok': True, 'google_email': info['email']})


def handle_google_disconnect(current_user):
    users = kvstore.load('users')
    u = users.get(current_user['matricula'])
    if u:
        u.pop('google_sub', None)
        u.pop('google_email', None)
        users_save(users)
    return jsonify({'ok': True})
```

No `handle_me`, no ramo autenticado (onde monta a resposta com o usuário), garantir que devolve os campos google. Se `handle_me` usa `build_user_payload`, já vem de graça; senão, incluir no dict de resposta:

```python
        'google_conectado': bool(u.get('google_sub')),
        'google_email': u.get('google_email', ''),
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m unittest tests.test_google_auth -v`
Expected: PASS.

- [ ] **Step 5: Rotas em `server.py`**

Após `api_google_login`:

```python
@app.route('/api/auth/google/connect', methods=['POST'])
@auth.require_auth
def api_google_connect():
    return auth.handle_google_connect(request.json or {}, request.current_user)

@app.route('/api/auth/google/disconnect', methods=['POST'])
@auth.require_auth
def api_google_disconnect():
    return auth.handle_google_disconnect(request.current_user)
```

- [ ] **Step 6: Commit**

```bash
git add auth.py server.py tests/test_google_auth.py
git commit -m "feat(auth): conectar/desconectar conta Google"
```

---

### Task 4: Config — CSP + `GOOGLE_CLIENT_ID` no render.yaml

**Files:**
- Modify: `server.py` (CSP em `_security_headers`)
- Modify: `render.yaml` (declarar `GOOGLE_CLIENT_ID`)

**Interfaces:**
- Produces: CSP que permite o GIS; env var `GOOGLE_CLIENT_ID` disponível no servidor.

- [ ] **Step 1: Liberar o Google na CSP (`server.py`)**

Em `_security_headers`, trocar as três linhas indicadas:

```python
                            "script-src 'self' 'unsafe-inline' https://accounts.google.com; "
                            "connect-src 'self' https://accounts.google.com https://*.push.services.mozilla.com https://fcm.googleapis.com https://*.notify.windows.com; "
                            "frame-src https://accounts.google.com; "
```

(A linha `frame-src` é nova — inserir junto ao bloco. Manter `frame-ancestors 'none'`.)

- [ ] **Step 2: Declarar a env var no `render.yaml`**

Na lista `envVars`, adicionar:

```yaml
      - key: GOOGLE_CLIENT_ID
        sync: false
```

- [ ] **Step 3: Verificar sintaxe do render.yaml**

Run: `python -c "import yaml; yaml.safe_load(open('render.yaml')); print('yaml ok')"`
Expected: `yaml ok`

- [ ] **Step 4: Commit**

```bash
git add server.py render.yaml
git commit -m "chore(auth): CSP libera Google Identity + GOOGLE_CLIENT_ID no render"
```

---

### Task 5: Frontend — botão "Entrar com Google" na tela de login

**Files:**
- Modify: `index.html` (carregar o script do GIS)
- Modify: `static/app.js` (renderizar o botão na tela de login; callback que chama `/api/auth/google`)

**Interfaces:**
- Consumes: `GET /api/auth/google/client-id`, `POST /api/auth/google`, `setToken()` (app.js:843)

- [ ] **Step 1: Carregar o script do GIS no `index.html`**

No `<head>` (após as fontes, antes do `</head>`):

```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

- [ ] **Step 2: Adicionar o botão e o callback no `static/app.js`**

Na função que renderiza a tela de login (onde hoje há o `fetch("/api/auth/login", ...)`, por volta de `app.js:919`), depois do formulário de matrícula+senha, injetar um container e inicializar o GIS. Adicionar estas funções auxiliares (perto de `getToken`/`setToken`, app.js:842):

```javascript
async function googleClientId(){
  try{
    const r=await fetch("/api/auth/google/client-id");
    const j=await r.json();
    return j.enabled ? j.clientId : "";
  }catch(_){ return ""; }
}

async function montarBotaoGoogle(containerEl, onToken){
  const cid=await googleClientId();
  if(!cid || !window.google || !google.accounts){ return; } // degrada: some o botao
  google.accounts.id.initialize({ client_id: cid, callback: (resp)=>onToken(resp.credential) });
  google.accounts.id.renderButton(containerEl, { theme:"outline", size:"large", width:260, text:"signin_with", locale:"pt-BR" });
}

async function loginComGoogle(credential){
  const r=await fetch("/api/auth/google",{method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({credential})});
  const j=await r.json().catch(()=>({}));
  if(r.ok && j.token){ setToken(j.token); location.reload(); return; }
  alert(j.error || "Nao foi possivel entrar com o Google.");
}
```

No HTML da tela de login, adicionar um divisor + container logo abaixo do botão "Entrar":

```html
<div class="login-google-sep">ou</div>
<div id="googleBtn" class="login-google-btn"></div>
```

E, após renderizar a tela de login, chamar:

```javascript
montarBotaoGoogle(document.getElementById("googleBtn"), loginComGoogle);
```

- [ ] **Step 3: Verificação manual ao vivo (após deploy + `GOOGLE_CLIENT_ID` no Render)**

1. Abrir a tela de login → o botão "Entrar com Google" aparece.
2. Clicar com uma conta Google **não vinculada** → aparece o aviso de "não vinculada".
   (Sem `GOOGLE_CLIENT_ID` configurado, o botão simplesmente não aparece — login normal intacto.)

- [ ] **Step 4: Commit**

```bash
git add index.html static/app.js
git commit -m "feat(ui): botao Entrar com Google na tela de login"
```

---

### Task 6: Frontend — conectar/desconectar em Configurações + aviso único

**Files:**
- Modify: `static/app.js` (seção Configurações: status + botões conectar/desconectar; banner de aviso único)

**Interfaces:**
- Consumes: `montarBotaoGoogle` (Task 5), `POST /api/auth/google/connect`, `POST /api/auth/google/disconnect`, `/api/auth/me` (campos `google_conectado`, `google_email`), `getToken()`

- [ ] **Step 1: Bloco "Conta Google" em Configurações**

Na função que renderiza a seção `setup`/Configurações, adicionar um cartão. Usar o estado do usuário atual (de `/api/auth/me`, campos `google_conectado`/`google_email`):

```javascript
function renderContaGoogle(me){
  const conectado = me && me.google_conectado;
  const email = (me && me.google_email) || "";
  return `
  <div class="card">
    <h3>Conta Google (opcional)</h3>
    ${conectado
      ? `<p>Conectado como <b>${email}</b>.</p>
         <button id="googleDisc" class="btn-secondary">Desconectar Google</button>`
      : `<p>Conecte pra poder entrar com um clique. Continua opcional.</p>
         <div id="googleConnBtn"></div>`}
  </div>`;
}
```

Depois de inserir no DOM:

```javascript
const discBtn=document.getElementById("googleDisc");
if(discBtn){
  discBtn.onclick=async()=>{
    await fetch("/api/auth/google/disconnect",{method:"POST",
      headers:{"Authorization":"Bearer "+getToken()}});
    location.reload();
  };
}
const connEl=document.getElementById("googleConnBtn");
if(connEl){
  montarBotaoGoogle(connEl, async(credential)=>{
    const r=await fetch("/api/auth/google/connect",{method:"POST",
      headers:{"Content-Type":"application/json","Authorization":"Bearer "+getToken()},
      body:JSON.stringify({credential})});
    const j=await r.json().catch(()=>({}));
    if(r.ok){ alert("Conta Google conectada!"); location.reload(); }
    else { alert(j.error || "Nao foi possivel conectar."); }
  });
}
```

- [ ] **Step 2: Banner de aviso único**

Após o login bem-sucedido (onde a app entra no estado logado), mostrar uma vez:

```javascript
function avisoGoogleUmaVez(){
  try{
    if(localStorage.getItem("turmaA_googleAvisoVisto")==="1") return;
    // so avisa se o recurso estiver habilitado no servidor
    googleClientId().then(cid=>{
      if(!cid) return;
      localStorage.setItem("turmaA_googleAvisoVisto","1");
      alert("Novidade: agora da pra entrar com sua conta Google. E opcional — se preferir, continue entrando com matricula e senha normalmente. Conecte em Configuracoes.");
    });
  }catch(_){}
}
```

Chamar `avisoGoogleUmaVez()` uma vez ao montar a home logada.

- [ ] **Step 3: Verificação manual ao vivo**

1. Logar normal → aviso aparece 1x (e não volta).
2. Configurações → Conectar conta Google → escolher conta → "conectada".
3. Sair, "Entrar com Google" → entra direto.
4. Configurações → Desconectar → volta ao estado inicial.

- [ ] **Step 4: Commit**

```bash
git add static/app.js
git commit -m "feat(ui): conectar/desconectar Google em Configuracoes + aviso unico"
```

---

## Pré-requisito operacional (Angelo, fora do código)

Antes do teste ao vivo, criar o Client ID no **Google Cloud Console** (guiado 1 passo por vez):
1. Criar projeto.
2. Tela de consentimento OAuth → External.
3. Credenciais → Criar → "ID do cliente OAuth" → Aplicativo da Web.
4. **Origens JavaScript autorizadas:** `https://agenda-turma-a.onrender.com`.
5. Copiar o **Client ID** → colar no env `GOOGLE_CLIENT_ID` do serviço no Render → deploy.

Sem essa env var, o recurso fica invisível e o app segue 100% normal (login matrícula+senha).

## Self-Review (feito)

- **Cobertura da spec:** validação de token (T1), login Google com estados aprovado/pendente/negado/não-vinculado (T2), connect/disconnect + 1:1 (T3), CSP+env (T4), botão login (T5), Configurações+aviso (T6). ✓
- **Sem placeholders:** todo passo tem código/coman­do real. ✓
- **Consistência de tipos:** `verificar_google_token`→`{sub,email}`; `build_user_payload`, `_find_user_by_google_sub`, `handle_google_*` batem entre tasks e rotas. ✓
