# Dados sumiram (eventos, escala, checklist)

## Sintomas
- Abriu o app e os eventos/checklist desapareceram.
- Calendário voltou ao estado inicial.

## Causa provável
1. Limpou o cache do navegador (limpa o localStorage também).
2. Trocou de aparelho (dados ficam em cada aparelho separadamente — não há sincronização).
3. Modo privado/anônimo (não persiste).
4. Desinstalou o PWA com opção "Apagar dados".

## Solução
- **Não há recuperação automática** — localStorage é puramente local.
- **Para o futuro**: usar a função "Exportar dados" (botão no menu) regularmente para fazer backup em arquivo .json.
- **Para sincronizar entre aparelhos**: precisaria de implementar login + banco no servidor (não existe ainda).

## Como o Viriato deve responder
"Os seus eventos ficam guardados só no aparelho. Se trocou de telemóvel ou limpou o cache, infelizmente não consigo recuperar. Para o futuro, exporte os dados regularmente como backup."
