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

    # Fixa o fuso em UTC para casar com os timestamps "Z" deste teste (os horários
    # de funcionamento são interpretados no fuso da clínica).
    await client.patch("/clinics/me", headers=h, json={"config": {"timezone": "UTC"}})

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

    # Fuso UTC para que "09:00–12:00" caiam nas horas UTC que o teste assere.
    await client.patch("/clinics/me", headers=h, json={"config": {"timezone": "UTC"}})

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


@pytest.mark.asyncio
async def test_optimistic_lock_on_concurrent_update(client, make_clinic_with_owner):
    """Locking otimista: duas edições concorrentes da MESMA linha — a segunda
    deve falhar com StaleDataError (que o service traduz para 409), fechando o
    lost update. Simula a corrida com duas sessões de tenant e commit controlado."""
    from sqlalchemy import text
    from sqlalchemy.orm.exc import StaleDataError

    from app.core.database import async_session_maker
    from app.modules.scheduling import repository

    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))
    clinic_id = owner["clinic_id"]
    h = await _login(client, owner["email"], password)

    pr = await client.post(
        "/patients", headers=h, json={"nome": "Bia", "telefone": "+5511966665555"}
    )
    patient_id = pr.json()["id"]
    cr = await client.post(
        "/scheduling/appointments",
        headers=h,
        json={"patient_id": patient_id, "starts_at": f"{DAY}T15:00:00Z", "duration_min": 30},
    )
    assert cr.status_code == 201, cr.text
    appt_id = cr.json()["id"]

    async def _tenant_session():
        # Espelha app.core.tenant.open_tenant_session, mas sem auto-commit no
        # exit — precisamos controlar a ordem (A commita antes de B dar flush).
        s = async_session_maker()
        await s.execute(
            text("SELECT set_config('app.current_clinic', :c, true)"),
            {"c": str(clinic_id)},
        )
        return s

    s1 = await _tenant_session()
    s2 = await _tenant_session()
    try:
        a1 = await repository.get_by_id(s1, clinic_id, appt_id)
        a2 = await repository.get_by_id(s2, clinic_id, appt_id)
        assert a1 is not None and a2 is not None

        a1.notes = "editado por A"
        await s1.commit()  # A vence: version 1 -> 2

        a2.notes = "editado por B (stale)"
        with pytest.raises(StaleDataError):
            await s2.flush()  # UPDATE ... WHERE version=1 casa 0 linhas
        await s2.rollback()
    finally:
        await s1.close()
        await s2.close()
