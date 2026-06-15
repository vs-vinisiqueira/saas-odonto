"""Testes do registro de números do WhatsApp por clínica:
registro + resolução do tenant (SECURITY DEFINER) + isolamento por RLS.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.main import app
from app.modules.whatsapp.repository import resolve_clinic_for_number


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client, email: str, password: str) -> dict:
    r = await client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_registra_resolve_e_isola(client, make_clinic_with_owner):
    password = "segredo123"
    pn = f"PN_{uuid.uuid4().hex[:10]}"
    a = await make_clinic_with_owner(password_hash=hash_password(password))
    b = await make_clinic_with_owner(password_hash=hash_password(password))
    ha = await _login(client, a["email"], password)
    hb = await _login(client, b["email"], password)

    # A registra seu número
    r = await client.post(
        "/ai/whatsapp/numbers", headers=ha, json={"phone_number_id": pn, "label": "Teste"}
    )
    assert r.status_code == 201, r.text

    # aparece na listagem de A
    r = await client.get("/ai/whatsapp/numbers", headers=ha)
    assert any(n["phone_number_id"] == pn for n in r.json())

    # a função SECURITY DEFINER resolve o tenant pelo phone_number_id (sem JWT)
    resolved = await resolve_clinic_for_number(pn)
    assert resolved == str(a["clinic_id"])

    # B não vê o número de A...
    r = await client.get("/ai/whatsapp/numbers", headers=hb)
    assert all(n["phone_number_id"] != pn for n in r.json())

    # ...e não consegue registrar o MESMO phone_number_id (único global) -> 409
    r = await client.post(
        "/ai/whatsapp/numbers", headers=hb, json={"phone_number_id": pn}
    )
    assert r.status_code == 409, r.text


@pytest.mark.asyncio
async def test_resolve_desconhecido_retorna_none():
    assert await resolve_clinic_for_number("PN_inexistente_xyz") is None
