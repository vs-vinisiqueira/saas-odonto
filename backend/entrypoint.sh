#!/usr/bin/env sh
set -e

echo ">> Aplicando migrations (Alembic, conexão admin)..."
uv run alembic upgrade head

echo ">> Subindo a API (uvicorn) na porta ${PORT:-8000}..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
