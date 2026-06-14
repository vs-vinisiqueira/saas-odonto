"""Testes do módulo de pacientes: CRUD + isolamento por tenant via RLS."""

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
async def test_patient_crud(client, make_clinic_with_owner):
    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))
    headers = await _login(client, owner["email"], password)

    # cria
    r = await client.post(
        "/patients",
        headers=headers,
        json={"nome": "Maria Souza", "telefone": "+5511999990000"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # lista
    r = await client.get("/patients", headers=headers)
    assert r.status_code == 200
    assert any(p["id"] == pid for p in r.json())

    # detalhe
    r = await client.get(f"/patients/{pid}", headers=headers)
    assert r.status_code == 200
    assert r.json()["nome"] == "Maria Souza"

    # atualiza
    r = await client.patch(
        f"/patients/{pid}", headers=headers, json={"observacoes": "alergia a dipirona"}
    )
    assert r.status_code == 200
    assert r.json()["observacoes"] == "alergia a dipirona"

    # remove
    r = await client.delete(f"/patients/{pid}", headers=headers)
    assert r.status_code == 204
    r = await client.get(f"/patients/{pid}", headers=headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_patients_isolated_between_tenants(client, make_clinic_with_owner):
    password = "segredo123"
    a = await make_clinic_with_owner(password_hash=hash_password(password))
    b = await make_clinic_with_owner(password_hash=hash_password(password))
    ha = await _login(client, a["email"], password)
    hb = await _login(client, b["email"], password)

    # paciente criado na clínica A
    r = await client.post(
        "/patients", headers=ha, json={"nome": "Paciente A", "telefone": "111"}
    )
    pid = r.json()["id"]

    # clínica B não enxerga na listagem...
    r = await client.get("/patients", headers=hb)
    assert all(p["id"] != pid for p in r.json())

    # ...nem por acesso direto ao id (RLS -> 404)
    r = await client.get(f"/patients/{pid}", headers=hb)
    assert r.status_code == 404
