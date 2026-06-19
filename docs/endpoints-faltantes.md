# Endpoints faltantes / incompletos para o frontend

> Documento gerado após portar o protótipo `front-saas` para `apps/web`.  
> Todos os endpoints listados abaixo já possuem **interface no frontend** mas o backend
> ainda não os implementa (ou retorna campos insuficientes).

---

## 1. Enriquecer resposta de Agendamentos com `patient_nome`

**Endpoint atual:** `GET /scheduling/appointments?date=YYYY-MM-DD`

**Problema:** A resposta retorna `patient_id` (UUID), mas o frontend precisa do **nome** para exibir
na grade da agenda (visão semana/dia) e nas "próximas consultas" do Dashboard. Hoje o frontend
faz um `GET /patients` completo e faz o lookup em memória — funciona, mas é ineficiente quando
a lista de pacientes for grande.

**Campo faltando:**
```jsonc
{
  "id": "uuid",
  "patient_id": "uuid",
  "patient_nome": "Ana Souza",   // ← FALTANDO
  "starts_at": "2026-06-18T09:00:00Z",
  "status": "confirmed"
}
```

**Onde implementar:** `backend/app/modules/scheduling/schemas.py` (adicionar `patient_nome: str | None`)  
e `backend/app/modules/scheduling/service.py` (JOIN na tabela `patients`).

---

## 2. Enriquecer resposta de Cobranças com `patient_nome`

**Endpoint atual:** `GET /billing/charges`

**Problema:** `Payment` retorna `patient_id` mas não o nome. A tabela de cobranças exibe
"Referência" (charge_id) em vez do nome do paciente porque o tipo `Payment` não tem `patient_nome`.

**Campo faltando:**
```jsonc
{
  "id": "uuid",
  "patient_id": "uuid",
  "patient_nome": "João Silva",   // ← FALTANDO
  "valor": "250.00",
  "descricao": "Limpeza",
  "status": "pending",
  "charge_id": "...",
  "qr_code": "...",
  "qr_code_base64": "..."
}
```

**Onde implementar:** `backend/app/modules/billing/schemas.py` + `service.py` (JOIN em `patients`).

---

## 3. Campo `tipo` nos Agendamentos

**Endpoint atual:** `POST /scheduling/appointments` e `GET /scheduling/appointments`

**Problema:** O protótipo exibe o **tipo da consulta** (Avaliação, Limpeza, Restauração, Canal,
Clareamento, Cirurgia) com cores na grade semanal. A tabela `appointments` do backend não tem
esse campo.

**Migration necessária:**
```sql
ALTER TABLE appointments ADD COLUMN tipo VARCHAR(30) DEFAULT 'avaliacao';
```

**Schemas a adicionar:**
```python
class AppointmentTipo(str, Enum):
    avaliacao   = "avaliacao"
    limpeza     = "limpeza"
    restauracao = "restauracao"
    canal       = "canal"
    clareamento = "clareamento"
    cirurgia    = "cirurgia"
```

**Arquivos:** `backend/alembic/versions/0008_appointment_tipo.py` + `schemas.py` + `service.py`.

---

## 4. Agendamentos em range de datas (visão semanal)

**Endpoint atual:** `GET /scheduling/appointments?date=YYYY-MM-DD` — retorna apenas **um dia**.

**Problema:** A visão semanal (`view=week`) precisa dos 7 dias da semana de uma vez. Hoje o
frontend exibe apenas os agendamentos do dia selecionado no grid semanal (os outros dias ficam
vazios).

**Proposta:** Suportar range opcional:
```
GET /scheduling/appointments?date=2026-06-15          # dia único (retro-compatível)
GET /scheduling/appointments?from=2026-06-15&to=2026-06-21  # range de uma semana
```

**Onde implementar:** `backend/app/modules/scheduling/router.py` + `service.py`  
(o método `list_in_range` já existe e é usado pelo `/stats` — reaproveitar).

---

## 5. Contador de conversas não lidas

**Endpoint atual:** `GET /conversations` — não tem flag de "não lida".

**Problema:** O sidebar mostra um badge com a contagem de conversas não respondidas
(`unreadCount`), mas está hardcoded em `0` porque a API não retorna essa informação.

**Opção A — Campo na resposta da lista:**
```jsonc
{
  "id": "uuid",
  "unread": true,        // ← FALTANDO
  "last_message_at": "..."
}
```

**Opção B — Endpoint separado:**
```
GET /conversations/unread-count  →  { "count": 3 }
```

**Regra de negócio:** considera "não lida" toda conversa onde `last_message_sender = "patient"`
e a clínica ainda não enviou resposta após a última mensagem do paciente.

**Onde implementar:** `backend/app/modules/conversations/service.py` + `schemas.py`.

---

## 6. Busca/filtro de conversas

**Endpoint atual:** `GET /conversations` — sem filtro.

**Problema:** O frontend tem um campo de busca na inbox de conversas, mas não envia query para
o backend. A busca deve filtrar por nome do paciente ou número de telefone.

**Proposta:**
```
GET /conversations?q=Ana
```

**Onde implementar:** `backend/app/modules/conversations/router.py` + `service.py`.

---

## 7. ~~Atualizar conversa (toggle IA)~~ ✅ JÁ EXISTE

**Endpoint:** `PATCH /conversations/{id}` — **implementado** em `conversations/router.py:66`.

Aceita `{ "ai_enabled": bool }` e devolve `ConversationOut` com o item atualizado.
O hook `useToggleAI` no frontend já está conectado corretamente.

---

## 8. Página de Configurações (futuro)

**Endpoint necessário (ainda não definido):**

A página `/config` está como placeholder. Quando for implementada, precisará de:

| Endpoint | Descrição |
|---|---|
| `GET /clinics/me/settings` | Horário de funcionamento, fuso, config IA |
| `PATCH /clinics/me/settings` | Atualizar configurações |
| `GET /ai/whatsapp/numbers` | Listar números WhatsApp cadastrados |
| `POST /ai/whatsapp/numbers` | Registrar novo número |

---

## Resumo de prioridade

| # | Endpoint / Campo | Impacto visual | Esforço |
|---|---|---|---|
| 1 | `patient_nome` em appointments | Alto — grades da agenda e dashboard | Baixo (JOIN) |
| 2 | `patient_nome` em charges | Médio — tabela de cobranças | Baixo (JOIN) |
| 7 | `PATCH /conversations/{id}` | ~~Crítico~~ **✅ Já implementado** | — |
| 4 | Range de agendamentos | Alto — visão semanal completa | Médio |
| 5 | Contador de não lidas | Médio — badge no sidebar | Médio |
| 3 | Campo `tipo` em appointments | Médio — cores na grade | Médio (migration) |
| 6 | Busca de conversas | Baixo — UI já existe | Baixo |
| 8 | Config | Baixo — placeholder | Alto (escopo novo) |
