FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# uv (gerenciador de dependências)
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv

WORKDIR /app

# Instala dependências primeiro para aproveitar o cache de camadas
COPY pyproject.toml ./
COPY uv.lock* ./
RUN uv sync --no-dev

# Código da aplicação
COPY . .

EXPOSE 8000
CMD ["sh", "./entrypoint.sh"]
