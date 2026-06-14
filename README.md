# SaaS Odonto — IA + WhatsApp + Gestão

SaaS B2B multi-tenant para clínicas odontológicas (2–5 dentistas). Esta fase
entrega o **scaffold + a fundação**: base rodável, multi-tenant segura e
arquitetura plugável. O agente de IA, agendamento e o painel completo vêm nas
próximas fases.

> Documentos de origem: arquitetura técnica e pesquisa de mercado.

## Stack

- **Backend:** FastAPI · SQLAlchemy 2.0 (async) · Alembic · PostgreSQL 16 · JWT próprio
- **Multi-tenancy:** Shared DB + `clinic_id` + **Row-Level Security** (isolamento garantido pelo banco)
- **Adapters plugáveis:** canal de WhatsApp (mock-first), provedor de LLM, gateway de pagamento
- **Frontend:** Vite + React (placeholder de login)
- **Tooling:** `uv` (Python) · Docker Compose

## Estrutura

```
saas-odonto/
├── docker-compose.yml      # postgres + api
├── db/init/                # cria o role app_user (não-superusuário, sujeito a RLS)
├── backend/                # FastAPI + Alembic + testes
│   └── app/{core,modules,shared,tests}
└── apps/web/               # painel React (Vite) — placeholder
```

## Como subir (Docker — recomendado)

```bash
# 1. variáveis de ambiente
cp .env.example .env        # (Windows PowerShell: Copy-Item .env.example .env)

# 2. sobe postgres + api (a api roda as migrations no boot)
docker compose up --build

# 3. popula 2 clínicas + 1 owner cada
docker compose exec api uv run python -m scripts.seed
```

- API: http://localhost:8000 · Docs: http://localhost:8000/docs · Health: http://localhost:8000/health

### Login de teste (após o seed)

| Clínica           | E-mail               | Senha    |
|-------------------|----------------------|----------|
| Clínica Sorriso   | owner@sorriso.com    | senha123 |
| Clínica Bem Estar | owner@bemestar.com   | senha123 |

```bash
# login -> tokens
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@sorriso.com","password":"senha123"}'

# usar o access_token para ler a própria clínica (escopada por RLS)
curl http://localhost:8000/clinics/me -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Testes

Rodam contra um Postgres real com as migrations aplicadas:

```bash
docker compose run --rm api uv run pytest
```

Os testes provam o **isolamento por RLS**: conectado como `app_user`, um
`SELECT` sem `WHERE` só retorna o tenant do contexto atual; sem contexto, nada.

## Painel React (dev)

```bash
cd apps/web
npm install
npm run dev        # http://localhost:5173 (proxy /api -> :8000)
```

## Arquitetura de segurança (resumo)

- O **`clinic_id` vem de dentro do JWT** — nunca de parâmetro do cliente.
- A cada request com tenant, `core/tenant.py` faz `set_config('app.current_clinic', ...)`;
  o **RLS do PostgreSQL** filtra as linhas no próprio banco.
- A app conecta como **`app_user`** (não-superusuário) → sujeita ao RLS.
  Migrations e seed rodam como **superusuário** → ignoram o RLS de propósito.
- O login usa uma função **`SECURITY DEFINER`** para achar o usuário por e-mail
  antes de existir contexto de tenant.

## Próximas fases

`ai_agent` (LLM + tools `buscar_horarios`/`agendar`) · `scheduling` + Google
Calendar · `billing` com gateway Pix/cartão · adapter `meta.py` (WhatsApp
oficial) · painel React completo.
