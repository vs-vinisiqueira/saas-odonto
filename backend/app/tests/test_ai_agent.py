"""Teste end-to-end do agente de IA via webhook do canal mock.

Conversa: pergunta horários -> agenda -> tenta de novo (conflito). Tudo
escopado por tenant (RLS) e usando os casos de uso reais da agenda.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.main import app
from app.modules.ai_agent.router import channel

DAY = "2099-01-05"
PHONE = "+5511970001234"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _say(client, clinic_id: str, text: str) -> str:
    r = await client.post(
        "/ai/webhook",
        json={
            "tenant_id": str(clinic_id),
            "from": PHONE,
            "text": text,
            "message_id": "m-" + text[:6],
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["reply"]


@pytest.mark.asyncio
async def test_agent_books_appointment_end_to_end(client, make_clinic_with_owner):
    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))
    clinic_id = owner["clinic_id"]
    channel.sent.clear()

    # 1) pergunta por horários
    reply = await _say(client, clinic_id, f"oi, quais horários tem dia {DAY}?")
    assert "Horários livres" in reply
    assert "09:00" in reply

    # 2) agenda às 09:00
    reply = await _say(client, clinic_id, f"quero agendar {DAY} 09:00")
    assert "marcada" in reply.lower()
    assert "05/01/2099" in reply

    # 3) tenta o mesmo horário de novo -> conflito tratado com cordialidade
    reply = await _say(client, clinic_id, f"pode marcar {DAY} 09:00 de novo")
    assert "indispon" in reply.lower()

    # o canal mock registrou as 3 respostas enviadas
    assert len(channel.sent) == 3
    assert all(to == PHONE for to, _ in channel.sent)

    # o paciente foi criado automaticamente a partir do telefone
    login = await client.post(
        "/auth/login", json={"email": owner["email"], "password": password}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    patients = (await client.get("/patients", headers=headers)).json()
    assert any(p["telefone"] == PHONE for p in patients)


@pytest.mark.asyncio
async def test_agent_help_message_when_unclear(client, make_clinic_with_owner):
    owner = await make_clinic_with_owner(password_hash=hash_password("x"))
    reply = await _say(client, owner["clinic_id"], "bom dia!")
    assert "ajudar" in reply.lower()
