"""Prova de que o RLS — e não apenas o código — garante o isolamento entre
tenants. Conecta como `app_user` (sujeito a RLS) e verifica que, mesmo num
SELECT sem `WHERE clinic_id`, só enxerga o tenant do contexto atual.
"""

import os

import pytest
from sqlalchemy import text

from app.tests.conftest import make_engine

APP_URL = os.getenv("DATABASE_URL")


async def _set_tenant(conn, clinic_id) -> None:
    await conn.execute(
        text("SELECT set_config('app.current_clinic', :cid, false)"),
        {"cid": str(clinic_id)},
    )


@pytest.mark.asyncio
async def test_rls_isolates_tenants(make_clinic_with_owner):
    a = await make_clinic_with_owner()
    b = await make_clinic_with_owner()

    app_engine = make_engine(APP_URL)
    async with app_engine.connect() as conn:
        await _set_tenant(conn, a["clinic_id"])

        # Mesmo sem WHERE, só vê linhas da clínica A.
        user_clinics = (await conn.execute(text("SELECT clinic_id FROM users"))).scalars().all()
        assert user_clinics, "deveria enxergar o usuário da própria clínica"
        assert all(str(c) == str(a["clinic_id"]) for c in user_clinics)
        assert all(str(c) != str(b["clinic_id"]) for c in user_clinics)

        # A tabela clinics também é escopada: só a própria clínica aparece.
        clinic_ids = (await conn.execute(text("SELECT id FROM clinics"))).scalars().all()
        assert all(str(c) == str(a["clinic_id"]) for c in clinic_ids)
    await app_engine.dispose()


@pytest.mark.asyncio
async def test_rls_denies_without_context(make_clinic_with_owner):
    await make_clinic_with_owner()  # existe dado, mas...

    app_engine = make_engine(APP_URL)
    async with app_engine.connect() as conn:
        # ...sem app.current_clinic definido, a política nega tudo.
        count = (await conn.execute(text("SELECT count(*) FROM users"))).scalar_one()
        assert count == 0
    await app_engine.dispose()
