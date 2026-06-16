# Prompt — Atualizar o Manual de Instruções (Replit Agent)

> Cole o conteúdo abaixo no Replit Agent. Ele reconstrói o manual a partir do código,
> sem omitir detalhes e sem manter funções que não existem mais.

---

## Tarefa

Atualizar o manual de instruções do app (`gerar_manual.py` → `manual_agenda_turma_a.pdf`) para refletir **exatamente todas as funções que existem hoje no código** — sem omitir nenhum detalhe e sem manter nenhuma função que não exista mais.

## Fonte da verdade = o código

**Não use o manual atual como referência de funcionalidades — ele está defasado.** Antes de escrever qualquer linha, faça um inventário completo de funções lendo:

- **`server.py`** → todas as rotas `@app.route('/api/...')` (é a lista oficial de funcionalidades do backend)
- **`dss.py`** → módulo de Diálogo de Segurança e Saúde (DSS)
- **`static/app.js`** → todas as telas/seções e funções `render*` (`renderDSS`, `dssRenderMural`, `dssRenderRealizados`, `dssRanking`, `dssExtratoSVG`, chat, acervo, checklist, viriato, painel admin, etc.)
- **`index.html`, `notify.py`, `drive_sync.py`** → PWA, notificações push e integrações

## Método (siga em ordem)

1. Liste **toda** funcionalidade encontrada no código (uma linha por feature/rota/tela).
2. Compare essa lista com o conteúdo atual de `gerar_manual.py`.
3. Para cada item:
   - **ADICIONE** o que falta no manual;
   - **CORRIJA** o que mudou;
   - **REMOVA** do manual qualquer função/capítulo/menu que não exista mais no código.
4. Atualize o **Sumário**, a **numeração dos capítulos** e o **glossário** para baterem com o resultado final.
5. Regenere o PDF rodando: `python gerar_manual.py`
6. **Bump da versão** (ex.: "Versão 2.6") na capa e no rodapé, com o mês/ano atuais.

## Gaps que eu já sei que existem (confirme no código e documente em detalhe)

- **O módulo DSS (Diálogo de Segurança e Saúde) NÃO está no manual** e precisa de um capítulo completo cobrindo:
  - a **escala mensal de apresentação**;
  - o fluxo **self-service** (a própria pessoa se escala pelo botão **"SUA VEZ DE APRESENTAR"**, escolhe data e tema e monta o card);
  - as **ações do dono** ("Já apresentei" / "Cancelar");
  - o **painel REALIZADOS** no topo (filtro por nome/tema/matrícula + paginação de **5 por página**);
  - a **auditoria por empregado** (toque no nome → total de DSS, temas apresentados e histórico);
  - o **extrato em SVG**, que é **exclusivo de admin** (o botão só aparece para `role = admin`) e agora inclui, no topo, um **RANKING DE ENGAJAMENTO** (barras horizontais, do mais ao menos engajado, pódio dos 3 primeiros e contagem de DSS por pessoa, com indicação de atrasos).
- Verifique também se há recursos no código ainda **não documentados** (ex.: notificações push, diário pessoal, multi-turma) e inclua os que forem voltados ao usuário/admin.

## Regras rígidas

- **NÃO invente** funcionalidade que não esteja no código. Em dúvida se algo existe, confirme na rota/função antes de escrever.
- **NÃO preserve nada obsoleto**: se o manual descreve algo que não está mais no código, apague.
- **MANTENHA o estilo visual e a estrutura** do `gerar_manual.py` (estilos H1/H2/H3, tabelas, badges, capa Vale, notas/avisos) — é só atualizar o conteúdo.
- Escreva na **mesma linguagem** do manual atual: simples, ferroviária, "de maquinista para maquinistas".

## Entregue no final

1. `gerar_manual.py` atualizado e `manual_agenda_turma_a.pdf` regenerado (rode o script e confirme que gerou sem erro).
2. Um **relatório curto** listando: (a) capítulos/itens **ADICIONADOS**, (b) **CORRIGIDOS**, (c) **REMOVIDOS** — para eu revisar.
