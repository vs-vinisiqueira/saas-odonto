"""Testes de rotação e revogação de refresh token (A4).

Login persiste o jti; refresh rotaciona (invalida o anterior) e detecta reuso;
logout revoga de verdade no servidor.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client, owner, password) -> dict:
    r = await client.post(
        "/auth/login", json={"email": owner["email"], "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_refresh_rotates_and_rejects_reuse(client, make_clinic_with_owner):
    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))
    old_refresh = (await _login(client, owner, password))["refresh_token"]

    # Refresh emite um par novo (refresh token diferente do anterior).
    r = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200, r.text
    assert r.json()["refresh_token"] != old_refresh

    # Reusar o refresh antigo (já rotacionado) é recusado.
    r = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 401, r.text


@pytest.mark.asyncio
async def test_logout_revokes_refresh(client, make_clinic_with_owner):
    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))
    refresh = (await _login(client, owner, password))["refresh_token"]

    r = await client.post("/auth/logout", json={"refresh_token": refresh})
    assert r.status_code == 204, r.text

    # Depois do logout, o refresh não vale mais.
    r = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 401, r.text
