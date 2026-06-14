"""Testes end-to-end de autenticação + acesso escopado por tenant."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_login_and_get_my_clinic(client, make_clinic_with_owner):
    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))

    r = await client.post(
        "/auth/login", json={"email": owner["email"], "password": password}
    )
    assert r.status_code == 200, r.text
    tokens = r.json()
    assert tokens["token_type"] == "bearer"

    r2 = await client.get(
        "/clinics/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["id"] == str(owner["clinic_id"])


@pytest.mark.asyncio
async def test_login_wrong_password(client, make_clinic_with_owner):
    owner = await make_clinic_with_owner(password_hash=hash_password("certa"))
    r = await client.post(
        "/auth/login", json={"email": owner["email"], "password": "errada"}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_token(client):
    r = await client.get("/clinics/me")
    assert r.status_code in (401, 403)
