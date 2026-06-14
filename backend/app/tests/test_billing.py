"""Testes do financeiro: cobrança Pix (gateway mock), webhook e isolamento."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.main import app


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
async def test_charge_and_webhook_flow(client, make_clinic_with_owner):
    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))
    h = await _login(client, owner["email"], password)

    # cria cobrança
    r = await client.post(
        "/billing/charges",
        headers=h,
        json={"valor": "150.00", "descricao": "Limpeza"},
    )
    assert r.status_code == 201, r.text
    charge = r.json()
    assert charge["status"] == "pending"
    assert charge["charge_id"].startswith("mock_")
    assert charge["qr_code"]
    assert float(charge["valor"]) == 150.0

    # aparece na listagem
    r = await client.get("/billing/charges", headers=h)
    assert any(p["id"] == charge["id"] for p in r.json())

    # provedor confirma o pagamento via webhook (sem JWT)
    r = await client.post(
        "/billing/webhook",
        json={"charge_id": charge["charge_id"], "status": "paid"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # status atualizado
    r = await client.get(f"/billing/charges/{charge['id']}", headers=h)
    assert r.json()["status"] == "paid"

    # webhook com charge_id desconhecido -> ok=false, mas 200
    r = await client.post(
        "/billing/webhook", json={"charge_id": "mock_inexistente", "status": "paid"}
    )
    assert r.status_code == 200
    assert r.json()["ok"] is False


@pytest.mark.asyncio
async def test_charges_isolated_between_tenants(client, make_clinic_with_owner):
    password = "segredo123"
    a = await make_clinic_with_owner(password_hash=hash_password(password))
    b = await make_clinic_with_owner(password_hash=hash_password(password))
    ha = await _login(client, a["email"], password)
    hb = await _login(client, b["email"], password)

    r = await client.post(
        "/billing/charges", headers=ha, json={"valor": "99.90"}
    )
    cid = r.json()["id"]

    # B não vê a cobrança de A
    r = await client.get("/billing/charges", headers=hb)
    assert all(p["id"] != cid for p in r.json())
    r = await client.get(f"/billing/charges/{cid}", headers=hb)
    assert r.status_code == 404
