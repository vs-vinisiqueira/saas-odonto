# 🦷 SaaS Odonto — IA + WhatsApp + Gestão

SaaS B2B **multi-tenant** para clínicas odontológicas (2–5 dentistas). Diferencial:
atendimento por **IA no WhatsApp** com agendamento autônomo, gestão de pacientes,
agenda e cobrança Pix — tudo isolado por clínica via **Row-Level Security** do
PostgreSQL.

> O backend e o painel já rodam ponta a ponta. Os provedores externos (LLM real,
> WhatsApp da Meta, gateway Pix, Google Calendar) estão atrás de interfaces e hoje
> usam implementações **mock-first** — trocáveis sem mexer na regra de negócio.

---

## Estado atual

| Área | Status | Descrição |
|------|--------|-----------|
| **Auth** | ✅ | Login JWT (claims `clinic_id` + `role`), refresh, RBAC |
| **Clínicas** | ✅ | Leitura/edição da própria clínica (tenant) |
| **Pacientes** | ✅ | CRUD escopado por tenant |
| **Agenda** | ✅ | Disponibilidade, agendar (com checagem de conflito), cancelar |
| **Cobranças** | ✅ | Pix via gateway mock **ou Mercado Pago (real)** + webhook de confirmação |
| **Agente de IA** | ✅ | Conversa → consulta horários → agenda. LLM mock ou **Gemini**; canal mock ou **WhatsApp (Meta)** |
| **Painel web** | ✅ | Login, Pacientes, Agenda (calendário), Cobranças |
| **Multi-tenancy** | ✅ | Shared DB + `clinic_id` + RLS (isolamento garantido pelo banco) |

**Testes:** 13 de integração no backend (pytest) + 3 no frontend (Vitest).

---

## Stack

- **Backend:** FastAPI · SQLAlchemy 2.0 (async) · Alembic · **PostgreSQL** (Neon ou Docker) · JWT próprio
- **Frontend:** Vite · React · TypeScript · Tailwind + componentes shadcn-style · React Router · TanStack Query · Zustand · react-hook-form + zod
- **Multi-tenancy:** Shared DB + `clinic_id` + **Row-Level Security**
- **Adapters plugáveis (mock-first):** canal WhatsApp · provedor de LLM · gateway de pagamento · sync de calendário
- **Tooling:** `uv` (Python) · `npm` (web) · Docker Compose (opcional)

---

## Estrutura do monorepo

```
saas-odonto/
├── docker-compose.yml          # postgres + api (alternativa 100% local)
├── db/
│   ├── init/                   # role app_user p/ o Postgres do Docker
│   └── neon/01-app-role.sql    # role app_user p/ o Neon (rodar 1x)
├── backend/
│   ├── alembic/versions/       # migrations 0001..0005
│   └── app/
│       ├── core/               # config, database, security, tenant, db_url
│       ├── shared/             # models base, exceptions
│       ├── modules/
│       │   ├── auth/  clinics/  patients/  scheduling/  billing/
│       │   └── ai_agent/       # channels (WhatsApp), llm, tools, service
│       └── tests/              # pytest (integração, RLS ponta a ponta)
└── apps/web/                   # painel React (Vite)
    └── src/{lib,components,features,routes.tsx}
```

Cada módulo segue o mesmo molde: `models → schemas → repository → service → router`.

---

## Pré-requisitos

- Python 3.11+ e [`uv`](https://docs.astral.sh/uv/)
- Node 18+ e `npm`
- Um PostgreSQL — **Neon** (recomendado) ou via **Docker Compose**

---

## Configuração (`.env`)

Copie o exemplo e ajuste (o `.env` fica na raiz e **não** é versionado):

```bash
cp .env.example .env        # PowerShell: Copy-Item .env.example .env
```

Chaves principais:

| Variável | Uso |
|----------|-----|
| `DATABASE_URL` | Conexão da **aplicação** (role `app_user`, sujeito a RLS). No Neon, use o host **com** `-pooler`. |
| `ADMIN_DATABASE_URL` | Conexão **admin** (dono do banco) usada por migrations e seed. No Neon, host **direto** (sem `-pooler`). |
| `JWT_SECRET` | Segredo do JWT (troque em produção). |

Driver sempre `postgresql+asyncpg://`. O helper `app/core/db_url.py` normaliza
SSL/pooler do Neon (remove `sslmode`/`channel_binding`, desliga prepared
statements no pooler) automaticamente.

---

## Subindo o backend

### Opção A — Neon (recomendado)

```bash
# 1. Crie o role da aplicação no Neon (uma vez), no SQL Editor do projeto:
#    rode o conteúdo de db/neon/01-app-role.sql (troque a senha) — a MESMA
#    senha vai no usuário do DATABASE_URL.

# 2. A partir de backend/, injetando o .env da raiz no ambiente:
cd backend
uv run --env-file ../.env alembic upgrade head     # aplica as migrations
uv run --env-file ../.env python -m scripts.seed    # 2 clínicas + 1 owner cada
uv run --env-file ../.env uvicorn app.main:app --reload
```

> Rodando local (fora do Docker), `alembic` e o `seed` leem as variáveis via
> `os.getenv`, por isso o `--env-file ../.env` é necessário.

### Opção B — Docker Compose (Postgres local)

```bash
docker compose up --build                              # sobe postgres + api (migrations no boot)
docker compose exec api uv run python -m scripts.seed  # popula os dados
```

- API: http://localhost:8000 · **Docs (Swagger):** http://localhost:8000/docs · Health: http://localhost:8000/health

### Login de teste (após o seed)

| Clínica           | E-mail              | Senha    |
|-------------------|---------------------|----------|
| Clínica Sorriso   | owner@sorriso.com   | senha123 |
| Clínica Bem Estar | owner@bemestar.com  | senha123 |

---

## Subindo o painel (frontend)

```bash
cd apps/web
npm install
npm run dev        # http://localhost:5173  (proxy /api -> http://localhost:8000)
```

Abra http://localhost:5173 e entre com o login de teste. Telas: **Agenda**
(calendário com horários livres → agendar/cancelar), **Pacientes** (CRUD) e
**Cobranças** (Pix + status).

---

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/auth/login` · `/auth/refresh` | Autenticação (JWT + refresh) |
| `GET` `PATCH` | `/clinics/me` | Dados da própria clínica |
| `GET` `POST` | `/patients` | Listar / criar pacientes |
| `GET` `PATCH` `DELETE` | `/patients/{id}` | Detalhe / editar / excluir |
| `GET` | `/scheduling/availability?date=YYYY-MM-DD` | Horários livres do dia |
| `GET` `POST` | `/scheduling/appointments` | Listar / agendar |
| `PATCH` | `/scheduling/appointments/{id}` | Reagendar / mudar status |
| `POST` | `/scheduling/appointments/{id}/cancel` | Cancelar |
| `GET` `POST` | `/billing/charges` | Listar / criar cobrança Pix |
| `POST` | `/billing/charges/{id}/refresh` | Atualizar status no gateway |
| `POST` | `/billing/webhook` | Confirmação genérica/mock (sem JWT) |
| `POST` | `/billing/mercadopago/webhook` | Notificação do Mercado Pago (sem JWT) |
| `POST` | `/ai/webhook` | Mensagem recebida pelo canal mock (teste do agente) |
| `GET` `POST` | `/ai/whatsapp/webhook` | Verificação / recebimento do WhatsApp (Meta) |
| `GET` `POST` | `/ai/whatsapp/numbers` | Listar / registrar o número da clínica |
| `GET` | `/health` | Healthcheck |

### Demo do agente de IA (sem WhatsApp real)

```bash
curl -X POST http://localhost:8000/ai/webhook -H "Content-Type: application/json" \
  -d '{"tenant_id":"<CLINIC_ID>","from":"+5511999990000","text":"quais horários tem dia 2099-01-05?","message_id":"1"}'

curl -X POST http://localhost:8000/ai/webhook -H "Content-Type: application/json" \
  -d '{"tenant_id":"<CLINIC_ID>","from":"+5511999990000","text":"quero agendar 2099-01-05 09:00","message_id":"2"}'
```

O agente resolve o paciente pelo telefone (cria se não existir), consulta a agenda
real e marca a consulta — tudo escopado pelo tenant.

### Usando o Gemini (LLM real, opcional)

Por padrão o agente usa um LLM **mock** (intenção por regex, offline). Para usar o
**Google Gemini** de verdade, pegue uma chave grátis em
https://aistudio.google.com e configure no `.env`:

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=<sua-chave>
GEMINI_MODEL=gemini-2.5-flash
```

Sem chave (ou com `LLM_PROVIDER=mock`), o agente segue no mock — útil para
desenvolvimento e testes offline. A execução das tools (`buscar_horarios`/
`agendar`) continua escopada por tenant (RLS) nos dois casos.

### Conectar o WhatsApp real (Meta Cloud API, grátis)

> 📖 **Passo a passo detalhado:** [`docs/whatsapp-setup.md`](docs/whatsapp-setup.md)

Use o **número de teste** gratuito da Meta (envia para até 5 números verificados).

1. **Meta:** developers.facebook.com → criar app **Business** → adicionar o produto
   **WhatsApp** → pegar o **número de teste**, o **token** e o **Phone number ID**;
   adicionar seu celular como destinatário de teste.
2. **Túnel:** exponha a API local com `ngrok http 8000` (a Meta exige HTTPS público).
3. **Webhook (painel da Meta):** Callback URL
   `https://SEU-NGROK/ai/whatsapp/webhook`, Verify token = o mesmo do `.env`,
   e assine o campo **messages**.
4. **`.env`:**
   ```
   CHANNEL_PROVIDER=meta
   WHATSAPP_TOKEN=<token>
   WHATSAPP_PHONE_NUMBER_ID=<phone number id>
   WHATSAPP_VERIFY_TOKEN=<string à sua escolha>
   ```
5. **Ligar o número à clínica** (uma vez, autenticado):
   ```bash
   curl -X POST http://localhost:8000/ai/whatsapp/numbers \
     -H "Authorization: Bearer <ACCESS_TOKEN>" -H "Content-Type: application/json" \
     -d '{"phone_number_id":"<phone number id>"}'
   ```
6. Mande uma mensagem do seu WhatsApp para o número de teste — o agente responde.

O webhook resolve a clínica pelo `phone_number_id` (tabela `whatsapp_numbers` +
função `SECURITY DEFINER`) e processa em background. Sem credenciais
(`CHANNEL_PROVIDER=mock`), tudo segue no canal mock.

### Ativar o Pix real (Mercado Pago, sandbox)

> 📖 **Passo a passo detalhado:** [`docs/mercadopago-setup.md`](docs/mercadopago-setup.md)

Pegue o **Access Token de teste** (`TEST-...`) no painel de devs do Mercado Pago e
configure no `.env`:
```
BILLING_PROVIDER=mercadopago
MERCADOPAGO_ACCESS_TOKEN=TEST-xxxx
MERCADOPAGO_PAYER_EMAIL=test_user_123@testuser.com
```
`POST /billing/charges` passa a emitir um **Pix real** (QR copia-e-cola +
imagem). Dá para testar **sem ngrok**: `POST /billing/charges/{id}/refresh`
consulta o status na API do MP. Sem token (`BILLING_PROVIDER=mock`), segue no
gateway mock.

---

## Testes

```bash
# Backend (integração; precisa do banco com as migrations aplicadas)
cd backend
uv run --env-file ../.env pytest          # Neon
# ou: docker compose run --rm api uv run pytest

# Frontend
cd apps/web
npm test
```

Os testes de backend provam o **isolamento por RLS**: conectado como `app_user`,
um `SELECT` sem `WHERE` só retorna o tenant do contexto; sem contexto, nada.

---

## Arquitetura de segurança (resumo)

- O **`clinic_id` vem de dentro do JWT** — nunca de parâmetro do cliente.
- A cada request com tenant, `core/tenant.py` faz `set_config('app.current_clinic', ...)`
  numa transação; o **RLS do PostgreSQL** filtra as linhas no próprio banco.
- A aplicação conecta como **`app_user`** (não-dono) → sujeita ao RLS. Migrations e
  seed rodam como **dono do banco** → ignoram o RLS de propósito (sem `FORCE`, o que
  funciona no Neon, que não tem superusuário).
- Operações **sem contexto de tenant** usam funções **`SECURITY DEFINER`**: o login
  (`auth_find_user_by_email`) e o webhook de pagamento (`billing_clinic_for_charge`).

---

## Adapters plugáveis (mock-first)

Hoje rodam mocks; a troca por provedores reais não toca a regra de negócio:

| Interface | Mock atual | Provedor futuro |
|-----------|------------|-----------------|
| `ai_agent/llm/base.LLMProvider` | `MockLLMProvider` (regex) **ou Gemini (real)** | Claude / OpenAI |
| `ai_agent/channels/base.WhatsAppChannel` | `MockWhatsAppChannel` **ou Meta (real)** | (Twilio/360dialog) |
| `billing/gateway.PaymentGateway` | `MockPaymentGateway` **ou Mercado Pago (real)** | Asaas / Stripe |
| `scheduling/calendar_sync.CalendarSync` | `NullCalendarSync` | Google Calendar |

---

## Próximas fases

Provedores reais (LLM, WhatsApp, Pix, Calendar) · fuso horário e horário de
funcionamento por clínica · portal do paciente · deploy (Vercel/Docker) · CI.
