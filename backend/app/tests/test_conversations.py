"""Testes do inbox de conversas.

Cobrem: (1) o webhook do agente persiste a conversa + as 2 mensagens (paciente
e IA); (2) resposta manual cria uma mensagem `human`; (3) isolamento por tenant
(uma clínica não enxerga a conversa da outra). LLM forçado em mock (determinístico).
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.main import app
from app.modules.ai_agent import router as ai_router
from app.modules.ai_agent.llm.mock import MockLLMProvider
from app.modules.ai_agent.router import channel

PHONE = "+5511971112233"


@pytest.fixture(autouse=True)
def _force_mock_llm():
    original = ai_router.agent._llm
    ai_router.agent._llm = MockLLMProvider()
    yield
    ai_router.agent._llm = original


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client, owner: dict, password: str) -> dict:
    res = await client.post(
        "/auth/login", json={"email": owner["email"], "password": password}
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


async def _say(client, clinic_id: str, text: str) -> None:
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


@pytest.mark.asyncio
async def test_webhook_persists_conversation_and_messages(client, make_clinic_with_owner):
    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))
    clinic_id = owner["clinic_id"]
    channel.sent.clear()

    await _say(client, clinic_id, "bom dia!")

    headers = await _login(client, owner, password)
    convs = (await client.get("/conversations", headers=headers)).json()
    assert len(convs) == 1
    conv = convs[0]
    assert conv["external_number"] == PHONE
    assert conv["channel"] == "mock"
    assert conv["last_message_preview"]

    messages = (
        await client.get(f"/conversations/{conv['id']}/messages", headers=headers)
    ).json()
    assert len(messages) == 2
    assert messages[0]["sender"] == "patient"
    assert messages[0]["direction"] == "inbound"
    assert messages[1]["sender"] == "ai"
    assert messages[1]["direction"] == "outbound"


@pytest.mark.asyncio
async def test_manual_reply_creates_human_message(client, make_clinic_with_owner):
    password = "segredo123"
    owner = await make_clinic_with_owner(password_hash=hash_password(password))
    channel.sent.clear()
    await _say(client, owner["clinic_id"], "oi")

    headers = await _login(client, owner, password)
    conv = (await client.get("/conversations", headers=headers)).json()[0]

    r = await client.post(
        f"/conversations/{conv['id']}/messages",
        json={"text": "Olá! Já te respondo."},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["sender"] == "human"

    messages = (
        await client.get(f"/conversations/{conv['id']}/messages", headers=headers)
    ).json()
    assert messages[-1]["sender"] == "human"
    assert messages[-1]["text"] == "Olá! Já te respondo."


@pytest.mark.asyncio
async def test_conversation_isolated_by_tenant(client, make_clinic_with_owner):
    pw_a = "segredoA"
    pw_b = "segredoB"
    owner_a = await make_clinic_with_owner(password_hash=hash_password(pw_a))
    owner_b = await make_clinic_with_owner(password_hash=hash_password(pw_b))
    channel.sent.clear()

    await _say(client, owner_a["clinic_id"], "oi da clínica A")

    headers_b = await _login(client, owner_b, pw_b)
    convs_b = (await client.get("/conversations", headers=headers_b)).json()
    assert convs_b == []
