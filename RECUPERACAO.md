# 🚨 GUIA DE RECUPERAÇÃO — Agenda Seiri Operação 1

> Leia este arquivo PRIMEIRO se algo quebrar após uma alteração no código.
> Criado em: 05/05/2026 | Backup da versão: Turma A funcional + multi-turma dormente

---

## 📁 Arquivos de Backup Disponíveis

| Arquivo de Backup | Arquivo Original | O que contém |
|---|---|---|
| `index_backup.html` | `index.html` | Front-end completo (HTML + CSS + JS) da Turma A funcionando |
| `server_backup.py` | `server.py` | Backend Flask completo com multi-turma dormente |

---

## 🔁 Como Restaurar (se algo quebrar)

### Passo 1 — Restaurar pelo Shell do Replit
Abra o Shell (botão "+" → digitar "Shell") e execute:

```bash
cp index_backup.html index.html
cp server_backup.py server.py
```

### Passo 2 — Republicar o app
Clique em **Republish** no topo do editor do Replit.

### Passo 3 — Verificar
Acesse https://agenda-turma-a.replit.app e confirme que o app voltou ao normal.

---

## 🧠 Contexto do Projeto (para o assistente IA)

### Stack
- **Front-end:** `index.html` — arquivo único com todo HTML + CSS + JavaScript
- **Back-end:** `server.py` — Flask + Python
- **Banco:** PostgreSQL (produção) + localStorage (client)
- **Hospedagem:** Replit Reserved VM (0.5 vCPU / 2 GiB RAM) — South America

### O que estava funcionando no backup
- Calendário 2x2 da Turma A (âncora: 04/05/2026)
- Login por matrícula (sistema próprio, sem OAuth)
- Chatbot Viriato com Palácio de Memória (embeddings + pgvector)
- Acervo de documentos (PDF upload + busca semântica)
- Mural da turma, notificações, configurações

### Lógica da Escala 2x2 — REGRA FUNDAMENTAL
A escala funciona em ciclos de 4 dias: 2 trabalhando + 2 folga.
Cada turma tem uma DATA-ÂNCORA diferente (dia em que inicia fase 0 do ciclo):

| Turma | Turno | Horário | Âncora (fase 0) |
|---|---|---|---|
| A | Diurno | 06h–18h | 04/05/2026 |
| B | Diurno | 06h–18h | 06/05/2026 |
| C | Noturno | 18h–06h | 07/05/2026 |
| D | Noturno | 18h–06h | 05/05/2026 |

**Fórmula JavaScript para saber se uma turma está trabalhando num dia:**
```javascript
function estaTrabalhando(turma, data) {
  const ancora = ANCORAS[turma]; // Date object da âncora
  const diff = Math.floor((data - ancora) / 86400000);
  const fase = ((diff % 4) + 4) % 4;
  return fase === 0 || fase === 1; // true = trabalhando, false = folga
}
```

**Situação em 05/05/2026 (data de referência do backup):**
- Turma A → Folga (1º dia)
- Turma B → Trabalho (inicia amanhã 06/05 — estava no 3º dia do ciclo anterior)
- Turma C → Folga (2º dia)
- Turma D → Trabalho (2º dia — finaliza amanhã 06/05)

### Estrutura do sistema multi-turma (já implementado, dormente)
- Tabela `user_ala_map` no PostgreSQL mapeia matrícula → turma
- Flag `_multi_turma_ativo` em kv_store ativa/desativa o filtro
- Endpoints admin: `GET/POST /api/admin/user-ala`, `POST /api/admin/multi-turma/ativar`
- Para ativar: rodar backfill primeiro (`POST /api/admin/multi-turma/backfill`) ANTES de ativar

---

## 🔧 Alterações Planejadas (próximas implementações)

### FASE 1 — Sistema de Login + Turma B
1. Adicionar campo `turma` na tabela de usuários
2. Tela de cadastro com seleção de turma (A, B, C, D)
3. Ao logar, carregar âncora de escala da turma do usuário
4. Turma B com lógica correta (âncora 06/05/2026)

### FASE 2 — Renomeação
- Título: "Agenda Turma A — Escala 2x2" → "Agenda Seiri Operação 1"
- PWA short_name: "Agenda A" → "Seiri Op.1"
- Atualizar manifest.webmanifest

### FASE 3 — Turmas C e D
- Mesma lógica da Fase 1, estendendo para as turmas noturnas

---

## ⚠️ Regras Importantes para o Assistente IA

1. **NUNCA use o Agent Bot do Replit** — usa créditos caros. Toda alteração deve ser manual via Shell ou editor direto.
2. **SEMPRE faça backup antes de alterar** `index.html` ou `server.py`:
   ```bash
   cp index.html index_backup.html && cp server.py server_backup.py
   ```
3. **Teste ANTES de republicar** — use o preview interno do Replit.
4. **O `index.html` é um arquivo muito grande** — altere apenas trechos específicos, nunca substitua o arquivo inteiro sem ler antes.
5. **O banco de produção tem dados reais** — nunca rode comandos DROP ou DELETE sem confirmação do dono (Angelo Silva).
6. **O servidor Flask NÃO deve ser reiniciado manualmente** — o Replit gerencia isso no Republish.

---

## 📞 Dono do Projeto
- **Nome:** Angelo Silva
- **Matrícula Vale:** 497444
- **Conta Replit:** angellovedpl

