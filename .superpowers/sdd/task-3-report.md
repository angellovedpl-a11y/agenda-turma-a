# Task 3 Report — Conectar/Desconectar Conta Google

**Status:** CONCLUIDA

## Arquivos modificados

- `auth.py` — adicionado `handle_google_connect`, `handle_google_disconnect`; atualizado `handle_me` com campos `google_conectado`/`google_email`
- `server.py` — adicionadas rotas `POST /api/auth/google/connect` e `POST /api/auth/google/disconnect` com `@auth.require_auth`
- `tests/test_google_auth.py` — adicionada classe `GoogleConnectTests` (3 novos testes)

## Commits

(ver hash apos o commit da Task 3)

## Comando de teste e saida

```
py -3 -m unittest discover tests -v
```

Resultado: `Ran 17 tests in 0.003s — OK`

- 13 testes em `test_google_auth.py` (inclui 3 novos de `GoogleConnectTests`)
- 4 testes em `test_legal_acceptance.py`
- Todos verdes

## Observacoes

- `handle_me` montava o dict manualmente sem `google_conectado`/`google_email`. Campos foram adicionados diretamente (sem usar `build_user_payload` pois o retorno de `handle_me` tem campos extras como `pode_aprovar`, `pendentes`, `funcoes_disponiveis` que nao existem em `build_user_payload`).
- Vínculo 1:1 enforçado: se o `sub` ja pertence a outra matricula, retorna 409.
- `handle_google_disconnect` tolerante: se o usuario nao existe no dict, nao lança erro, retorna `{ok: True}` normalmente.
- Sem dependencias novas adicionadas.
