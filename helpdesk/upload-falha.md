# Upload de documento falha

## Sintomas
- "Arquivo maior que 5MB!"
- "Armazenamento cheio! Remova documentos antigos."
- Anexo parece aceito mas não fica salvo após recarregar a página.

## Causa provável
1. Arquivo acima de 5MB (limite do localStorage do navegador).
2. localStorage do navegador cheio (cota de ~5-10MB total).
3. Modo privado/anônimo do navegador (não persiste dados).

## Solução
- **Tamanho**: comprimir o PDF antes de anexar.
- **localStorage cheio**: ir em vários dias e remover documentos antigos com o botão ✕.
- **Modo privado**: usar o navegador em modo normal.
- **Limpar tudo**: nas ferramentas do navegador (F12 → Application → Local Storage) apagar `turmaA_v10` (perde tudo!).

## Como o Viriato deve responder
"Anexos ficam guardados no seu próprio aparelho (localStorage). Se está cheio, é só remover documentos antigos de outros dias. A biblioteca da Turma A no servidor não tem esse limite."
