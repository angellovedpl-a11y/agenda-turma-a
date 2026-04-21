# Viriato não responde / demora muito

## Sintomas
- Mensagem fica em "Pensando..." por mais de 30 segundos.
- Aparece erro vermelho "Erro no servidor Claude".
- Resposta vem em branco.

## Causa provável
1. Limite mensal de créditos Replit AI atingido (mensagem "FREE_CLOUD_BUDGET_EXCEEDED" / 429).
2. Conexão de internet instável (móvel em túnel, etc.).
3. Servidor reiniciando após deploy.
4. Pergunta longa demais com biblioteca grande.

## Solução
- **Erro 429 / créditos**: aguardar próximo mês ou trocar para outra API (Gemini, Groq) configurando chave em "Configurar APIs".
- **Conexão**: tentar de novo em local com Wi-Fi.
- **Servidor reiniciando**: aguardar 30s e tentar de novo.
- **Pergunta longa**: dividir em perguntas menores.

## Como o Viriato deve responder
"Pode ser limite de créditos do Claude. Se quiser, configure uma chave Gemini gratuita (gemini.google.com) no botão de configurações — eu funciono com várias APIs."
