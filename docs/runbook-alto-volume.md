# Runbook — preparação para alto volume de usuários

Stack: **Neon** (Postgres serverless, endpoint `-pooler`) + **Railway** (backend Docker) + **Vercel** (SPA).
Cenário-alvo: clínica grande (20+ dentistas), picos de agendamento concorrente.

> ⚠️ **Downtime:** o backend roda hoje em **instância única** no Railway. Qualquer
> deploy/redeploy reinicia o processo → blip de indisponibilidade. Regra deste runbook
> (prioridade sobre tudo): **não interromper usuários ativos.** Portanto:
> 1. Faça deploys em **janela de baixo tráfego**, OU
> 2. Suba para **≥ 2 réplicas** ANTES (Railway faz rolling deploy e o healthcheck `/health`
>    segura o corte), aí os deploys seguintes ficam sem downtime.

Legenda: **[código]** = já no PR desta branch · **[painel]** = ação sua no dashboard (não tenho acesso).

---

## Prioridade 0 — antes do pico

### P0.1 · Pool de conexões explícito — **[código] ✅ (PR #2, já na main)**
Já mergeado. `DB_POOL_SIZE=10, DB_MAX_OVERFLOW=10, DB_POOL_TIMEOUT=30, DB_POOL_RECYCLE=1800`.
- **Verificar (após deploy):**
  ```bash
  # rode de dentro de backend/ (é lá que vive o pacote app e o ambiente uv):
  cd backend && DATABASE_URL=postgresql+asyncpg://u:p@localhost/db \
    uv run python -c "from app.core.database import engine as e; \
    print(e.pool.size(), e.pool._max_overflow, e.pool._timeout, e.pool._recycle)"
  ```
- **Sucesso:** imprime `10 10 30 1800`.

### P0.2 · Índice composto da agenda — **[código] ✅ (PR #2, migration 0014, já na main)**
Aplica sozinha no boot (`entrypoint.sh`).
- **Verificar (no Postgres do ambiente):**
  ```sql
  \d appointments   -- deve listar ix_appointments_clinic_dentist_start
  EXPLAIN ANALYZE   -- deve usar o índice (Index Scan), não Seq Scan
  SELECT * FROM appointments
   WHERE clinic_id = '<uuid>' AND dentist_id = '<uuid>'
     AND starts_at < now() + interval '1 day' AND ends_at > now();
  ```
- **Sucesso:** `Index Scan using ix_appointments_clinic_dentist_start`.

### P0.3 · Rate limiter distribuído (Redis) — **[painel] — obrigatório se > 1 processo/réplica**
Sem `REDIS_URL`, o limite de login é **por processo** e se multiplica com workers/réplicas.
O código já suporta Redis com fallback in-memory ([ratelimit.py](../backend/app/core/ratelimit.py)) — só falta a env.
- **Fazer:** Railway → adicionar um **Redis** (plugin) → copiar a URL privada → setar `REDIS_URL=rediss://...` no serviço da API.
- **Verificar:**
  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" -X POST $BASE/auth/login \
       -H 'content-type: application/json' -d '{"email":"x@x","password":"x"}'
  # repita 6x rápido de duas conexões/instâncias diferentes
  ```
- **Sucesso:** a 6ª tentativa dentro de 60s retorna **429** de forma consistente entre réplicas.

### P0.4 · Neon: desligar scale-to-zero + teto de autoscaling — **[painel]**
Cold start após ociosidade adiciona segundos ao 1º request — ruim na recepção.
- **Fazer:** Neon → branch de produção → **Compute** → **min compute size > 0** (desliga o suspend no horário comercial) e definir **max autoscaling (CU)** adequado. Confirmar retenção de **PITR** (LGPD).
- **Verificar:**
  ```bash
  # após ~10min ocioso, o 1º request não deve pagar cold start:
  curl -s -o /dev/null -w "%{time_total}s\n" $BASE/health
  ```
- **Sucesso:** `/health` responde em ~sub-segundo mesmo após ociosidade; `status:ok`.

### P0.5 · Secrets de produção — **[painel]**
Definir no Railway (pendentes por checklist do projeto): `CREDENTIALS_SECRET` (fixa, ≥32 chars),
`WHATSAPP_APP_SECRET`, `MERCADOPAGO_WEBHOOK_SECRET`, e `ALLOWED_ORIGINS` só com domínios reais.
- **Verificar:** logs do boot **sem** o warning "CREDENTIALS_SECRET não definida em produção";
  webhooks rejeitam payload sem assinatura válida (401/403).

### P0.6 · Teste de carga do slot único → 409 — **[código] (script novo neste PR)**
- **Fazer (contra STAGING, com paciente/dentista de teste):**
  ```bash
  # o httpx vive no ambiente uv do backend/, então rode de dentro de backend/:
  cd backend && uv run python ../scripts/loadtest/booking_race.py \
    --base-url $STAGING --email <e> --password <s> \
    --patient-id <uuid> --dentist-id <uuid> --count 50
  ```
- **Sucesso:** `PASS ✅  Exatamente 1 agendamento venceu; os demais receberam 409.` + p95/p99 aceitáveis.

---

## Prioridade 1 — logo após subir

### P1.1 · Workers / réplicas — **[código: env-driven neste PR] + [painel]**
`entrypoint.sh` agora aceita `WEB_CONCURRENCY` (default 1 = inalterado). App é I/O-bound (async);
comece com **1 processo** e escale por **réplicas** (melhor isolamento + rolling deploy).
- ⚠️ Se **> 1 worker ou réplica**: P0.3 (Redis) vira **obrigatório** e ative P1.2 (migrations).
- **Dimensionar:** `(DB_POOL_SIZE + DB_MAX_OVERFLOW) * (WEB_CONCURRENCY × réplicas)` **abaixo** do
  limite do endpoint Neon. O `max_overflow` conta porque cada worker pode dar burst até
  `pool_size + max_overflow` sob pico (com os defaults 10+10, cada worker chega a **20** conexões,
  não 10). Para uma conta exata, zere `DB_MAX_OVERFLOW`.
- **Verificar:** `GET /health` OK em todas as réplicas; sem erro de esgotamento de pool sob carga.

### P1.2 · Migrations fora do boot das réplicas — **[código: guard neste PR] + [painel]**
`entrypoint.sh` aceita `RUN_MIGRATIONS=0`. Com múltiplas réplicas, rode `alembic upgrade head`
**uma vez** como etapa de release e ponha `RUN_MIGRATIONS=0` nas réplicas (evita corrida de DDL).
- **Sucesso:** só um processo aplica migrations; réplicas logam "pulando migrations".

### P1.3 · Observabilidade — **[painel/código futuro]**
Rastreamento de erros (Sentry) reusando o `X-Request-ID` de [main.py](../backend/app/main.py);
métricas de pool (checkout/esgotamento) e contagem de `IntegrityError` (frequência de corrida).

### P1.4 · Locking otimista no update — **[código futuro]**
Coluna `version` + `version_id_col` no `Appointment` para evitar *lost update* na edição concorrente
(o overlap já é coberto pelo EXCLUDE). Item 2.5 da revisão.

---

## Prioridade 2 — evolução
- Sync de calendário em background (fila + retry) — tirar do caminho do request (item 2.6).
- Endpoints de faixa semanal + `patient_nome` via JOIN (item 2.8, reduz N+1).

---

## Verificação de saúde geral (qualquer momento, sem downtime)
```bash
curl -s $BASE/health | jq          # {"status":"ok","db":true}
curl -s -o /dev/null -w "%{http_code}\n" $BASE/scheduling/appointments   # 401 sem token = rota viva
```
CI do repo (pytest como `app_user` validando RLS + build do frontend) deve permanecer verde em todo PR.
