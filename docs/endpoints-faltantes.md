# Endpoints faltantes / incompletos para o frontend

> Documento gerado após portar o protótipo `front-saas` para `apps/web`.
> Todos os itens abaixo foram identificados como faltantes no backend em relação
> à interface já existente no frontend.
>
> **Status: todos os itens foram implementados.** Mantido como histórico/changelog —
> cada seção referencia onde a implementação vive hoje.

---

## 1. ✅ `patient_nome` em Agendamentos

**Endpoint:** `GET /scheduling/appointments?date=YYYY-MM-DD`

Implementado via join transiente em `backend/app/modules/scheduling/service.py`
(`_attach_patient_nome` / `_attach_patient_nomes`) e exposto em
`backend/app/modules/scheduling/schemas.py:32` (`patient_nome: str | None`).

---

## 2. ✅ `patient_nome` em Cobranças

**Endpoint:** `GET /billing/charges`

Implementado em `backend/app/modules/billing/service.py`
(`_attach_patient_nome`) e `backend/app/modules/billing/schemas.py:26`.

---

## 3. ✅ Campo `tipo` nos Agendamentos

**Endpoints:** `POST /scheduling/appointments` e `GET /scheduling/appointments`

Coluna `tipo` na tabela `appointments` (migration Alembic), enum de valores
(`avaliacao`, `limpeza`, `restauracao`, `canal`, `clareamento`, `cirurgia`) em
`backend/app/modules/scheduling/schemas.py` e mapeamento em
`backend/app/modules/scheduling/models.py:76`.

---

## 4. ✅ Agendamentos em range de datas (visão semanal)

**Endpoint:** `GET /scheduling/appointments?from=YYYY-MM-DD&to=YYYY-MM-DD`

Query params opcionais `from`/`to` adicionados em
`backend/app/modules/scheduling/router.py` (retro-compatível com `date` único),
reaproveitando o `list_in_range` do service.

---

## 5. ✅ Contador de conversas não lidas

**Endpoint:** `GET /conversations`

Campo `unread: bool` na resposta, calculado em
`backend/app/modules/conversations/service.py:83` (última mensagem do paciente
sem resposta da clínica) e exposto em
`backend/app/modules/conversations/schemas.py:29`.

---

## 6. ✅ Busca/filtro de conversas

**Endpoint:** `GET /conversations?q=Ana`

Query param `q` (nome do paciente ou telefone) em
`backend/app/modules/conversations/router.py:35`.

---

## 7. ✅ Atualizar conversa (toggle IA)

**Endpoint:** `PATCH /conversations/{id}` — em `conversations/router.py:66`.

Aceita `{ "ai_enabled": bool }` e devolve `ConversationOut` com o item
atualizado. O hook `useToggleAI` no frontend está conectado corretamente.

---

## 8. ✅ Página de Configurações

**Endpoints:** `GET /clinics/me` · `PATCH /clinics/me`

A tela `/config` (Dados da clínica, Horários, Preferências) é atendida pelo
JSONB `clinics.config`, estruturado em
`backend/app/modules/clinics/schemas.py` (`ClinicConfig` com `clinic_data`,
`working_hours`, `preferences`, `timezone`) e roteado em
`backend/app/modules/clinics/router.py`. Merge raso por seção feito no
service — cada bloco da tela grava só a sua própria chave.

Cadastro de números de WhatsApp por clínica: `GET`/`POST /ai/whatsapp/numbers`
(módulo `ai_agent`).

---

## Resumo

| # | Endpoint / Campo | Status |
|---|---|---|
| 1 | `patient_nome` em appointments | ✅ |
| 2 | `patient_nome` em charges | ✅ |
| 3 | Campo `tipo` em appointments | ✅ |
| 4 | Range de agendamentos | ✅ |
| 5 | Contador de não lidas | ✅ |
| 6 | Busca de conversas | ✅ |
| 7 | `PATCH /conversations/{id}` | ✅ |
| 8 | Config (dados, horários, preferências, WhatsApp) | ✅ |

Nenhum item pendente neste documento. Para o próximo trabalho, ver a seção
"Próximas fases" do `README.md` (provedores reais restantes, portal do
paciente, deploy, CI).
