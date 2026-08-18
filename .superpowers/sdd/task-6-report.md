# Task 6 Report — Conectar/Desconectar Google em Configuracoes + Aviso Unico

**Status:** DONE

## Arquivos modificados
- `static/app.js`

## node --check
Saida vazia (sem erros).

## Como encaixou no padrao da secao Configuracoes

A secao Configuracoes e renderizada pela funcao `openSetup()` que usa `openModal(titulo, html, bindingsFn)`.
O objeto do usuario logado vem de `CURRENT_USER` (ja disponivel no scope, carregado por `loadMe()`).

Nao foi criado um sistema novo. A implementacao seguiu o padrao existente:
- Criada funcao auxiliar `_renderContaGoogleHtml(u)` que gera o HTML do card Google a partir de `CURRENT_USER`.
- O HTML do card e interpolado no template string do `openModal`, abaixo dos botoes existentes.
- Os bindings (Desconectar / montarBotaoGoogle) sao registrados na callback `bindingsFn`, junto dos outros bindings da secao.
- Ao conectar/desconectar: chama `apiFetch` (que ja carrega o Bearer token automaticamente via `apiFetch`), depois `loadMe()` para atualizar `CURRENT_USER`, fecha e reabre o modal para re-renderizar o card.

## avisoGoogleUmaVez
Funcao adicionada logo apos `openSetup`. Chamada em `loadMe().then(async()=>{ if(CURRENT_USER){render();avisoGoogleUmaVez();} })`.

## Preocupacoes
- `apiFetch` ja injeta o header Authorization automaticamente (via `getToken()`), entao nao foi necessario passar o token manualmente nas chamadas de connect/disconnect — consistente com o restante do codebase.
- O botao Google so renderiza se `googleClientId()` retornar algo (comportamento gracioso herdado de `montarBotaoGoogle`).

## Commit
feat(ui): conectar/desconectar Google em Configuracoes + aviso unico
