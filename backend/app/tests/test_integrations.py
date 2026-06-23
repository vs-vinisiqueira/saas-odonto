"""Testes das integrações por clínica:

- segredo é cifrado e NUNCA volta em claro (só dica mascarada);
- update parcial preserva o segredo não reenviado;
- WhatsApp registra o número (roteamento do webhook) e barra duplicado (409);
- RBAC (só owner) e isolamento por RLS;
- load_credentials decifra para uso em runtime.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.core.tenant import open_tenant_session
from app.main import app
from app.modules.integrations import service as integrations_service
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
async def test_lista_inicial_sem_configuracao(client, make_clinic_with_owner):
    password = "segredo123"
    a = await make_clinic_with_owner(password_hash=hash_password(password))
    ha = await _login(client, a["email"], password)

    r = await client.get("/integrations", headers=ha)
    assert r.status_code == 200, r.text
    providers = {i["provider"]: i for i in r.json()}
    assert set(providers) == {"whatsapp", "mercadopago", "google_calendar", "ai"}
    assert all(not i["configured"] and not i["enabled"] for i in providers.values())
    assert all(i["secret_hints"] == {} for i in providers.values())


@pytest.mark.asyncio
async def test_whatsapp_cifra_mascara_e_registra_numero(client, make_clinic_with_owner):
    password = "segredo123"
    token = f"EAA_{uuid.uuid4().hex}"
    pn = f"PN_{uuid.uuid4().hex[:10]}"
    a = await make_clinic_with_owner(password_hash=hash_password(password))
    ha = await _login(client, a["email"], password)

    r = await client.put(
        "/integrations/whatsapp",
        headers=ha,
        json={
            "enabled": True,
            "public_config": {"phone_number_id": pn},
            "secrets": {"access_token": token},
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["enabled"] and body["configured"]
    # o token JAMAIS volta em claro — só dica mascarada terminando nos últimos 4
    assert token not in r.text
    assert body["secret_hints"]["access_token"].endswith(token[-4:])
    assert body["public_config"]["phone_number_id"] == pn

    # registrou o número para o roteamento do webhook (função SECURITY DEFINER)
    assert await resolve_clinic_for_number(pn) == str(a["clinic_id"])

    # runtime consegue decifrar as credenciais da clínica
    async with open_tenant_session(a["clinic_id"]) as session:
        creds = await integrations_service.load_credentials(
            session, a["clinic_id"], "whatsapp"
        )
    assert creds["access_token"] == token
    assert creds["phone_number_id"] == pn


@pytest.mark.asyncio
async def test_update_parcial_preserva_segredo(client, make_clinic_with_owner):
    password = "segredo123"
    token = f"EAA_{uuid.uuid4().hex}"
    pn1 = f"PN_{uuid.uuid4().hex[:10]}"
    pn2 = f"PN_{uuid.uuid4().hex[:10]}"
    a = await make_clinic_with_owner(password_hash=hash_password(password))
    ha = await _login(client, a["email"], password)

    await client.put(
        "/integrations/whatsapp",
        headers=ha,
        json={"enabled": True, "public_config": {"phone_number_id": pn1}, "secrets": {"access_token": token}},
    )
    # troca só o phone_number_id; NÃO reenvia o segredo (deve ser preservado)
    r = await client.put(
        "/integrations/whatsapp",
        headers=ha,
        json={"public_config": {"phone_number_id": pn2}, "secrets": {}},
    )
    assert r.status_code == 200, r.text
    assert r.json()["public_config"]["phone_number_id"] == pn2

    async with open_tenant_session(a["clinic_id"]) as session:
        creds = await integrations_service.load_credentials(
            session, a["clinic_id"], "whatsapp"
        )
    assert creds["access_token"] == token  # segredo intacto


@pytest.mark.asyncio
async def test_numero_duplicado_em_outra_clinica_da_409(client, make_clinic_with_owner):
    password = "segredo123"
    pn = f"PN_{uuid.uuid4().hex[:10]}"
    a = await make_clinic_with_owner(password_hash=hash_password(password))
    b = await make_clinic_with_owner(password_hash=hash_password(password))
    ha = await _login(client, a["email"], password)
    hb = await _login(client, b["email"], password)

    r = await client.put(
        "/integrations/whatsapp",
        headers=ha,
        json={"public_config": {"phone_number_id": pn}, "secrets": {"access_token": "t"}},
    )
    assert r.status_code == 200, r.text

    r = await client.put(
        "/integrations/whatsapp",
        headers=hb,
        json={"public_config": {"phone_number_id": pn}, "secrets": {"access_token": "t"}},
    )
    assert r.status_code == 409, r.text


@pytest.mark.asyncio
async def test_isolamento_por_rls(client, make_clinic_with_owner):
    password = "segredo123"
    a = await make_clinic_with_owner(password_hash=hash_password(password))
    b = await make_clinic_with_owner(password_hash=hash_password(password))
    ha = await _login(client, a["email"], password)
    hb = await _login(client, b["email"], password)

    await client.put(
        "/integrations/ai",
        headers=ha,
        json={"enabled": True, "secrets": {"api_key": "AIza_secreta"}},
    )
    # B não enxerga a configuração de A
    r = await client.get("/integrations", headers=hb)
    ai = next(i for i in r.json() if i["provider"] == "ai")
    assert not ai["configured"] and ai["secret_hints"] == {}


@pytest.mark.asyncio
async def test_disconnect_limpa_segredo(client, make_clinic_with_owner):
    password = "segredo123"
    a = await make_clinic_with_owner(password_hash=hash_password(password))
    ha = await _login(client, a["email"], password)

    await client.put(
        "/integrations/ai",
        headers=ha,
        json={"enabled": True, "secrets": {"api_key": "AIza_secreta"}},
    )
    r = await client.delete("/integrations/ai", headers=ha)
    assert r.status_code == 200, r.text
    assert not r.json()["enabled"] and r.json()["secret_hints"] == {}

    async with open_tenant_session(a["clinic_id"]) as session:
        creds = await integrations_service.load_credentials(session, a["clinic_id"], "ai")
    assert creds is None


@pytest.mark.asyncio
async def test_nao_owner_recebe_403(client, make_clinic_with_owner):
    password = "segredo123"
    s = await make_clinic_with_owner(password_hash=hash_password(password), role="secretary")
    hs = await _login(client, s["email"], password)

    r = await client.get("/integrations", headers=hs)
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_provider_invalido_da_404(client, make_clinic_with_owner):
    password = "segredo123"
    a = await make_clinic_with_owner(password_hash=hash_password(password))
    ha = await _login(client, a["email"], password)

    r = await client.put("/integrations/inexistente", headers=ha, json={"secrets": {}})
    assert r.status_code == 404, r.text
