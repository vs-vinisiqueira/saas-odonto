"""Testes da agenda: disponibilidade, agendamento, conflito e isolamento."""

import datetime as dt

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.main import app

# Data futura fixa (evita o filtro de slots no passado).
DAY = "2099-01-05"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client, email: str, password: str) -> dict:
    r = await client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _hours(slots: list[dict]) -> set[tuple[int, int]]:
    out = set()
    for s in slots:
        d = dt.datetime.fromisoformat(s["starts_at"].replace("Z", "+00:00"))
        out.add((d.hour, d.minute))
    return out


@pytest.mark.asyncio
async def test_availability_and_booking_flow(client, make_clinic_with_owner):
    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))
    h = await _login(client, owner["email"], password)

    pr = await client.post(
        "/patients", headers=h, json={"nome": "João", "telefone": "+5511988887777"}
    )
    patient_id = pr.json()["id"]

    # 09:00–18:00, slots de 30min => 18 slots livres
    r = await client.get(f"/scheduling/availability?date={DAY}", headers=h)
    assert r.status_code == 200, r.text
    before = r.json()
    assert len(before) == 18
    assert (10, 0) in _hours(before)

    # agenda 10:00–10:30
    r = await client.post(
        "/scheduling/appointments",
        headers=h,
        json={"patient_id": patient_id, "starts_at": f"{DAY}T10:00:00Z", "duration_min": 30},
    )
    assert r.status_code == 201, r.text
    appt = r.json()
    assert appt["status"] == "scheduled"
    assert appt["tipo"] == "avaliacao"  # default
    assert appt["patient_nome"] == "João"

    # range from/to (visão semanal) inclui o agendamento criado
    r = await client.get(
        f"/scheduling/appointments?from={DAY}&to={DAY}", headers=h
    )
    assert r.status_code == 200, r.text
    range_ids = {a["id"] for a in r.json()}
    assert appt["id"] in range_ids

    # o slot das 10:00 some da disponibilidade
    r = await client.get(f"/scheduling/availability?date={DAY}", headers=h)
    after = r.json()
    assert len(after) == 17
    assert (10, 0) not in _hours(after)

    # tentar reagendar no mesmo horário => 409 conflito
    r = await client.post(
        "/scheduling/appointments",
        headers=h,
        json={"patient_id": patient_id, "starts_at": f"{DAY}T10:15:00Z", "duration_min": 30},
    )
    assert r.status_code == 409, r.text

    # cancelar libera o horário de novo
    r = await client.post(
        f"/scheduling/appointments/{appt['id']}/cancel", headers=h
    )
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
    r = await client.get(f"/scheduling/availability?date={DAY}", headers=h)
    assert (10, 0) in _hours(r.json())


@pytest.mark.asyncio
async def test_cannot_book_patient_from_other_tenant(client, make_clinic_with_owner):
    password = "segredo123"
    a = await make_clinic_with_owner(password_hash=hash_password(password))
    b = await make_clinic_with_owner(password_hash=hash_password(password))
    ha = await _login(client, a["email"], password)
    hb = await _login(client, b["email"], password)

    pr = await client.post(
        "/patients", headers=ha, json={"nome": "Paciente A", "telefone": "123"}
    )
    patient_a = pr.json()["id"]

    # clínica B não consegue agendar para o paciente da clínica A (RLS -> 404)
    r = await client.post(
        "/scheduling/appointments",
        headers=hb,
        json={"patient_id": patient_a, "starts_at": f"{DAY}T11:00:00Z"},
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_working_hours_from_clinic_config(client, make_clinic_with_owner):
    """`DAY` cai numa segunda-feira ("mon"); fechar esse dia via config zera a
    disponibilidade, e configurar 09-12h só libera slots dentro dessa janela."""
    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))
    h = await _login(client, owner["email"], password)

    r = await client.patch(
        "/clinics/me",
        headers=h,
        json={"config": {"working_hours": {"mon": {"closed": True}}}},
    )
    assert r.status_code == 200, r.text

    r = await client.get(f"/scheduling/availability?date={DAY}", headers=h)
    assert r.status_code == 200, r.text
    assert r.json() == []  # dia fechado -> sem slots

    r = await client.patch(
        "/clinics/me",
        headers=h,
        json={"config": {"working_hours": {"mon": {"closed": False, "start": "09:00", "end": "12:00"}}}},
    )
    assert r.status_code == 200, r.text

    r = await client.get(f"/scheduling/availability?date={DAY}", headers=h)
    slots = r.json()
    assert len(slots) == 6  # 09:00-12:00, 30min
    assert (12, 0) not in _hours(slots)


@pytest.mark.asyncio
async def test_invalid_tipo_rejected(client, make_clinic_with_owner):
    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))
    h = await _login(client, owner["email"], password)

    pr = await client.post(
        "/patients", headers=h, json={"nome": "Ana", "telefone": "+5511977776666"}
    )
    patient_id = pr.json()["id"]

    r = await client.post(
        "/scheduling/appointments",
        headers=h,
        json={
            "patient_id": patient_id,
            "starts_at": f"{DAY}T09:00:00Z",
            "tipo": "invalido",
        },
    )
    assert r.status_code == 404, r.text
