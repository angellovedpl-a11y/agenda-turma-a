# Spec — Login com Google (opção adicional)

**Data:** 2026-08-17
**Projeto:** Agenda Turma A (Flask + SPA + kvstore/Postgres)
**Branch:** `feat/migracao-render`

## Objetivo

Adicionar "Entrar com Google" como **opção extra** de login. Nunca obrigatório:
o login matrícula + senha continua sendo o principal e funciona exatamente
como hoje. Google é um atalho opcional que o usuário conecta se quiser.

## Princípios / não-objetivos

- **Google é aditivo, nunca obrigatório.** Quem não conectar, não percebe diferença.
- **A identidade do app continua sendo a matrícula.** O Google só aponta para uma matrícula já existente.
- **Sem cadastro novo por Google.** Google não cria conta; só liga uma conta Google a uma matrícula já aprovada.
- **A trava de aprovação já existente continua valendo** para qualquer método de login. Novos cadastros seguem pendentes até um aprovador liberar (fluxo atual inalterado — opção A escolhida pelo Angelo: aprovadores atuais mantidos).
- **YAGNI:** sem mudança no modelo de permissão, sem mudança em quem aprova.

## Contexto do código atual (verificado nesta sessão)

- Usuários em `kvstore['users']`, chaveados por **matrícula**. Campos: `role`
  (`admin`/`aprovador`/`user`), `admin_level`, `owner`, `status` (`aprovado`/pendente),
  `funcao`, `email`, `senha` (hash), `legal_acceptance`.
- Sessões: token (`session_create(matricula)`), enviado via `Authorization: Bearer`
  ou header `X-Auth-Token`; validade 30 dias; guardadas no kvstore.
- `get_current_user()` só devolve usuário com `status == 'aprovado'`.
- Rotas de auth em `server.py` (`/api/auth/*`) delegam para funções `handle_*` em `auth.py`.
- **`google-auth==2.49.2` já está no `requirements.txt`** → validação do token do Google sem dependência nova.

## Modelo de dados (adição mínima)

No registro do usuário (`kvstore['users'][matricula]`), dois campos novos, opcionais:

- `google_sub` (str) — o ID único e estável da conta Google (claim `sub`). **Chave do vínculo.**
- `google_email` (str) — e-mail do Google, só para exibição ("conectado como fulano@gmail.com").

Ligação **1-para-1**: um `google_sub` só pode pertencer a uma matrícula. Ausência dos campos = não conectado.

## Fluxos

### 1. Conectar (em Configurações, já logado)
1. Usuário loga normalmente (matrícula + senha).
2. Em **Configurações → Conectar conta Google**, clica no botão Google (GIS) e escolhe a conta.
3. O front envia o **ID token** para `POST /api/auth/google/connect` (autenticado).
4. Servidor valida o token (assinatura + `aud` == CLIENT_ID + `iss` google), extrai `sub`+`email`.
5. Se aquele `sub` já estiver ligado a **outra** matrícula → erro amigável ("essa conta Google já está vinculada a outro usuário").
6. Senão grava `google_sub`/`google_email` no usuário atual. Sucesso: "Conta Google conectada."
7. Existe também **Desconectar** (`POST /api/auth/google/disconnect`, autenticado) que limpa os campos.

### 2. Entrar com Google (tela de login)
1. Botão "Entrar com Google" (GIS) na tela de login.
2. Front envia o ID token para `POST /api/auth/google` (não autenticado).
3. Servidor valida o token, extrai `sub`, procura usuário com `google_sub == sub`:
   - **Encontrado e `status == aprovado`** → `session_create` → devolve token → entra.
   - **Encontrado mas pendente** → 403 amigável: "Seu cadastro está aguardando aprovação de um supervisor."
   - **Nenhum usuário com esse `sub`** → 404 amigável: "Essa conta Google ainda não está vinculada. Entre com sua matrícula e senha e conecte o Google em Configurações."
4. Login matrícula + senha permanece intacto ao lado do botão.

### 3. Aviso amigável (uma vez)
- Banner discreto para usuários existentes: "Novidade: agora dá pra entrar com sua conta Google.
  É opcional — se preferir, continue entrando com matrícula e senha normalmente."
- Fecha e não volta (flag em `localStorage`, ex.: `googleLoginAvisoVisto`).

## Endpoints novos (resumo)

| Método | Rota | Auth | Faz |
|---|---|---|---|
| POST | `/api/auth/google` | não | login via Google (sub → matrícula → sessão) |
| POST | `/api/auth/google/connect` | sim | liga a conta Google ao usuário logado |
| POST | `/api/auth/google/disconnect` | sim | desliga a conta Google do usuário logado |

Todas as validações do token ficam numa função única em `auth.py`
(`verificar_google_token(credential) -> {sub, email}` ou erro), reaproveitada pelas 3 rotas.
Rate limit em `/api/auth/google` igual ao `/api/auth/login` (reuso do decorator existente).

## Configuração / infra

- Env var **`GOOGLE_CLIENT_ID`** (é público, mas fica em env por organização). Declarar no `render.yaml`.
- Angelo cria no **Google Cloud Console**: projeto → tela de consentimento OAuth (External) →
  credencial "ID do cliente OAuth" tipo *Aplicativo da Web* → **Origens JavaScript autorizadas**:
  `https://agenda-turma-a.onrender.com` (e `http://localhost` se um dia testar local).
  Copia o Client ID para o env do Render. (Guiado 1 passo por vez.)
- Front carrega o script do Google Identity Services e usa o Client ID.

## Segurança

- Token do Google **sempre validado no servidor** (`google.oauth2.id_token.verify_oauth2_token`
  com o CLIENT_ID como `audience`). Nunca confiar em dados vindos só do front.
- Vínculo por `sub` (estável), não por e-mail (e-mail pode mudar/ser reutilizado).
- Um `sub` → no máximo uma matrícula (checagem na conexão).
- Login por Google só emite sessão se `status == aprovado` (mesma regra de hoje).
- Nada de novo exposto no client além do Client ID (que é público por design do GIS).

## Testes

- Unidade (`auth.py`, rodando com o padrão do projeto): `verificar_google_token` aceita token
  válido (mock) e rejeita `aud`/`iss` errados; login Google devolve sessão para usuário aprovado,
  403 para pendente, 404 para sub desconhecido; connect grava campos; connect recusa `sub` já usado por outra matrícula; disconnect limpa.
- Manual ao vivo (Angelo, no Render): conectar em Configurações, sair, entrar com Google;
  tentar entrar com Google não vinculado (ver aviso); login por senha continua funcionando.

## Fora de escopo

- Cadastro/registro via Google.
- Mudança em quem aprova novos cadastros (mantido como está — opção A).
- One Tap / login automático.
