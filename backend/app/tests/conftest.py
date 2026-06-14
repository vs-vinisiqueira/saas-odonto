"""Fixtures de teste.

Os testes são de INTEGRAÇÃO: precisam do Postgres no ar com as migrations
aplicadas. Forma recomendada de rodar (host `db` resolve dentro da rede):

    docker compose run --rm api uv run pytest

Para rodar no host, exporte DATABASE_URL/ADMIN_DATABASE_URL apontando para
localhost antes de chamar `uv run pytest`.
"""

import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.db_url import prepare_asyncpg

ADMIN_URL = os.getenv("ADMIN_DATABASE_URL") or os.getenv("DATABASE_URL")
APP_URL = os.getenv("DATABASE_URL")


def make_engine(url: str):
    """Engine async normalizado para o asyncpg (SSL/pooler do Neon)."""
    u, connect_args = prepare_asyncpg(url)
    return create_async_engine(u, connect_args=connect_args)


@pytest.fixture(autouse=True)
async def _dispose_app_engine():
    """Cada teste async roda em um event loop próprio. O engine global da app
    (app.core.database.engine) mantém um pool asyncpg preso ao primeiro loop;
    descartá-lo no teardown garante conexões novas no loop do próximo teste."""
    yield
    from app.core.database import engine

    await engine.dispose()


@pytest.fixture
async def make_clinic_with_owner():
    """Factory: cria (clínica + owner) via conexão admin e limpa tudo no fim."""
    admin = make_engine(ADMIN_URL)
    created: list[uuid.UUID] = []

    async def _make(password_hash: str = "x", role: str = "owner") -> dict:
        suffix = uuid.uuid4().hex[:8]
        clinic_id = uuid.uuid4()
        email = f"user-{suffix}@example.com"
        async with admin.begin() as conn:
            await conn.execute(
                text("INSERT INTO clinics (id, nome, config) VALUES (:id, :n, '{}'::jsonb)"),
                {"id": clinic_id, "n": f"Clinica {suffix}"},
            )
            await conn.execute(
                text(
                    "INSERT INTO users (id, clinic_id, email, password_hash, role) "
                    "VALUES (:id, :c, :e, :p, :r)"
                ),
                {"id": uuid.uuid4(), "c": clinic_id, "e": email, "p": password_hash, "r": role},
            )
        created.append(clinic_id)
        return {"clinic_id": clinic_id, "email": email}

    yield _make

    async with admin.begin() as conn:
        for clinic_id in created:
            await conn.execute(text("DELETE FROM users WHERE clinic_id = :c"), {"c": clinic_id})
            await conn.execute(text("DELETE FROM clinics WHERE id = :c"), {"c": clinic_id})
    await admin.dispose()
