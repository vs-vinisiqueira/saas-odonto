#!/usr/bin/env sh
set -e

# ── Migrations ────────────────────────────────────────────────────────────────
# Por padrão (RUN_MIGRATIONS=1, ou não definido) aplicamos as migrations no boot,
# como sempre. Em cenário MULTI-RÉPLICA, rode `alembic upgrade head` UMA vez como
# etapa de release (pre-deploy) e defina RUN_MIGRATIONS=0 nas réplicas — assim
# duas instâncias não disputam DDL ao subir ao mesmo tempo.
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo ">> Aplicando migrations (Alembic, conexão admin)..."
  uv run alembic upgrade head
else
  echo ">> RUN_MIGRATIONS=0 — pulando migrations neste processo (etapa de release cuida disso)."
fi

# ── API ───────────────────────────────────────────────────────────────────────
# Nº de workers via WEB_CONCURRENCY. Default 1 = comportamento atual (byte a byte:
# sem a flag --workers). Aumente com CAUTELA: cada worker abre seu PRÓPRIO pool,
# então o total de conexões é DB_POOL_SIZE * WEB_CONCURRENCY — mantenha abaixo do
# limite do endpoint Neon. App é I/O-bound (async), então poucos workers já saturam.
PORT="${PORT:-8000}"
WORKERS="${WEB_CONCURRENCY:-1}"
if [ "${WORKERS}" -gt 1 ] 2>/dev/null; then
  echo ">> Subindo a API (uvicorn, ${WORKERS} workers) na porta ${PORT}..."
  exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}"
else
  echo ">> Subindo a API (uvicorn) na porta ${PORT}..."
  exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
fi
