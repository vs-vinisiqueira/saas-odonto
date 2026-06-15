"""Testes do MetaWhatsAppChannel sem rede: parsing do payload, verificação do
challenge e montagem da requisição de envio (httpx mockado).
"""

import pytest

from app.modules.ai_agent.channels.meta import MetaWhatsAppChannel

TEXT_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "WABA",
            "changes": [
                {
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {"phone_number_id": "PN123"},
                        "messages": [
                            {
                                "from": "5511999990000",
                                "id": "wamid.ABC",
                                "type": "text",
                                "text": {"body": "quero marcar uma limpeza"},
                            }
                        ],
                    },
                }
            ],
        }
    ],
}

STATUS_PAYLOAD = {
    "entry": [
        {
            "changes": [
                {
                    "value": {
                        "metadata": {"phone_number_id": "PN123"},
                        "statuses": [{"id": "wamid.X", "status": "delivered"}],
                    }
                }
            ]
        }
    ]
}


@pytest.mark.asyncio
async def test_parse_messages_texto():
    msgs = MetaWhatsAppChannel.parse_messages(TEXT_PAYLOAD)
    assert len(msgs) == 1
    m = msgs[0]
    assert m.from_number == "5511999990000"
    assert m.text == "quero marcar uma limpeza"
    assert m.message_id == "wamid.ABC"
    assert m.phone_number_id == "PN123"


@pytest.mark.asyncio
async def test_parse_messages_ignora_status():
    assert MetaWhatsAppChannel.parse_messages(STATUS_PAYLOAD) == []


@pytest.mark.asyncio
async def test_verify_challenge():
    assert (
        MetaWhatsAppChannel.verify_challenge("subscribe", "segredo", "123", "segredo")
        == "123"
    )
    assert (
        MetaWhatsAppChannel.verify_challenge("subscribe", "errado", "123", "segredo")
        is None
    )
    assert MetaWhatsAppChannel.verify_challenge("subscribe", "x", "123", None) is None


@pytest.mark.asyncio
async def test_send_text_monta_requisicao(monkeypatch):
    captured: dict = {}

    class _Resp:
        status_code = 200
        text = "ok"

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json, headers):
            captured.update(url=url, json=json, headers=headers)
            return _Resp()

    monkeypatch.setattr(
        "app.modules.ai_agent.channels.meta.httpx.AsyncClient", _FakeClient
    )

    channel = MetaWhatsAppChannel(token="TKN", phone_number_id="PN123", api_version="v21.0")
    await channel.send_text("5511999990000", "Olá!")

    assert captured["url"] == "https://graph.facebook.com/v21.0/PN123/messages"
    assert captured["json"]["to"] == "5511999990000"
    assert captured["json"]["text"]["body"] == "Olá!"
    assert captured["headers"]["Authorization"] == "Bearer TKN"
