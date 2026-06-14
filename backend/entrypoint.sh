#!/usr/bin/env sh
set -e

echo ">> Aplicando migrations (Alembic, conexão admin)..."
uv run alembic upgrade head

echo ">> Subindo a API (uvicorn)..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
