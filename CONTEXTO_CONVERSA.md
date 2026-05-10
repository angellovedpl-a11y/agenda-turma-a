# 📋 CONTEXTO DA CONVERSA — Agenda Seiri Operação 1
> Salvo em: 05/05/2026 | Para: assistente IA retomar o contexto sem precisar reler tudo

---

## 👤 Sobre o Dono
- **Nome:** Angelo Silva | **Matrícula Vale:** 497444 | **Replit:** angellovedpl
- Trabalha na Vale — operações de pátio ferroviário (TFPM, São Luís/MA)
- Criou o app sozinho com auxílio do Replit Agent (que cobra caro por uso)
- **Decisão tomada:** parar de usar o Agent Bot e usar somente o assistente IA (Claude) para evoluir o projeto

---

## 📱 Sobre o App Atual

### Nome atual (a mudar): "Agenda Turma A — Escala 2x2"
### Nome novo definido: **"Agenda Seiri Operação 1"**
- "Seiri" = primeiro dos 5S japoneses = organização/ordenação
- "Operação 1" = contexto das operações de pátio da Vale

### O que o app faz hoje (Turma A):
- Calendário com escala 2x2 calculada automaticamente
- Login por matrícula
- Chatbot "Viriato" com Palácio de Memória (embeddings + pgvector + Claude Haiku)
- Acervo de documentos (PDF upload + busca semântica)
- Mural da turma, Chat, Notificações, Configurações
- Filtro de eventos no calendário por tipo (aniversário, médico, viagem, etc.)
- PWA instalável no celular

### Stack:
- Front-end: `index.html` (arquivo ÚNICO com todo HTML+CSS+JS — muito grande)
- Back-end: `server.py` (Flask + Python)
- Banco: PostgreSQL (produção, 32MB/100GB) + localStorage (client)
- Hospedagem: Replit Reserved VM 0.5vCPU/2GiB — South America
- URL produção: https://agenda-turma-a.replit.app

---

## 🏭 Contexto Operacional (IMPORTANTE)

O app é para as **4 turmas de pátio da Vale** que se revezam em escala 2×2:

| Turma | Turno | Horário | Âncora escala |
|---|---|---|---|
| A | Diurno | 06h–18h | 04/05/2026 (fase 0) |
| B | Diurno | 06h–18h | 06/05/2026 (fase 0) |
| C | Noturno | 18h–06h | 07/05/2026 (fase 0) |
| D | Noturno | 18h–06h | 05/05/2026 (fase 0) |

**Situação em 05/05/2026:**
- Turma A → finalizou ciclo hoje (folga a partir de hoje)
- Turma D → noturno, termina amanhã 06/05 (entregando para Turma B)
- Turma B → inicia ciclo amanhã 06/05 (diurno)
- Turma C → folga hoje e amanhã, volta 07/05

**Fórmula da escala (JavaScript):**
```js
const ANCORAS = {
  A: new Date(2026,4,4), // 04/05/2026
  B: new Date(2026,4,6), // 06/05/2026
  C: new Date(2026,4,7), // 07/05/2026
  D: new Date(2026,4,5)  // 05/05/2026
};
function trabalhando(turma, data) {
  const diff = Math.floor((data - ANCORAS[turma]) / 86400000);
  const fase = ((diff % 4) + 4) % 4;
  return fase < 2; // 0,1=trabalho | 2,3=folga
}
```

---

## 🎯 Decisões Tomadas nesta Conversa

### Design
- **Manter exatamente o mesmo design** do app atual (cores verdes/escuras, estilo, layout)
- NÃO criar interfaces diferentes por turma — todos veem o mesmo visual
- O que muda é apenas a LÓGICA DE ESCALA conforme a turma do usuário

### Fluxo de navegação novo:
1. **Splash** (igual ao atual)
2. **Tela de Login / Cadastro** (nova — duas opções)
3. **Cadastro:** usuário informa matrícula, nome, senha e **seleciona sua turma**
4. **Login:** matrícula + senha
5. **App abre** exatamente igual ao atual, mas com a escala da turma do usuário

### Backend:
- A tabela de usuários ganha campo `turma` (A, B, C ou D)
- A data-âncora do cálculo muda conforme turma do usuário logado
- O sistema multi-turma já está implementado e DORMENTE no server.py (ETAPA 5 do PLANO_500_USERS)
- Viriato filtra memórias por turma automaticamente quando ativado

---

## 📦 Estado dos Arquivos Hoje (05/05/2026)

| Arquivo | Estado |
|---|---|
| `index.html` | ✅ Front-end Turma A funcionando |
| `server.py` | ✅ Backend com multi-turma dormente |
| `index_backup.html` | ✅ **BACKUP** criado hoje |
| `server_backup.py` | ✅ **BACKUP** criado hoje |
| `RECUPERACAO.md` | ✅ Guia de recuperação criado hoje |
| `PLANO_500_USERS.md` | ✅ Plano de escalabilidade (ETAPAs 1-6 concluídas) |
| `replit.md` | ✅ Documentação técnica do projeto |
| `instrucoes_viriato.md` | ✅ Contexto operacional do Viriato (TFPM, ACT) |

---

## 🔧 Próximas Implementações (ordem definida)

### FASE 1 — Login + Turma B (PRÓXIMA A FAZER)
**Arquivos a alterar:** `index.html` (tela de login/cadastro + lógica escala) + `server.py` (campo turma no cadastro)

Passos:
1. Adicionar campo `turma` na tabela de usuários no banco
2. Criar tela de cadastro com seleção de turma no `index.html`
3. Modificar a lógica de escala no front para usar a turma do usuário logado
4. Ativar o sistema multi-turma no backend (já implementado)

**Como fazer SEM o Agent:**
- Usar Shell do Replit para comandos
- Editar arquivos direto no editor do Replit
- Assistente IA prepara o código, Angelo cola no editor

### FASE 2 — Renomeação
- `<title>` no index.html: → "Agenda Seiri Operação 1"
- `manifest.webmanifest`: name → "Agenda Seiri Operação 1", short_name → "Seiri Op.1"
- Cabeçalho visual do app

### FASE 3 — Turmas C e D
- Mesma lógica da Fase 1

---

## ⚠️ Regras para o Assistente IA

1. **JAMAIS usar o Agent Bot do Replit** — muito caro
2. Toda edição via Shell ou editor manual
3. Sempre backup antes de alterar index.html ou server.py:
   `cp index.html index_backup.html && cp server.py server_backup.py`
4. index.html é ENORME — alterar apenas trechos específicos
5. Nunca DROP/DELETE no banco sem confirmação do Angelo
6. O app não tem relação com STEFEM — o ACT é só um PDF na biblioteca do Viriato
7. O app é para equipes de PÁTIO DA VALE, não é do sindicato

