"""Testes do MercadoPagoGateway sem rede: monta a cobrança Pix, parseia a
resposta e mapeia o status (httpx mockado).
"""

from decimal import Decimal

import pytest

from app.modules.billing.mercadopago_gateway import MercadoPagoGateway, map_status


class _Resp:
    def __init__(self, data: dict, status_code: int = 200):
        self._data = data
        self.status_code = status_code

    def json(self) -> dict:
        return self._data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AssertionError("HTTP error")


def _patch_client(monkeypatch, *, post=None, get=None):
    captured: dict = {}

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json, headers):
            captured.update(method="POST", url=url, json=json, headers=headers)
            return post

        async def get(self, url, headers):
            captured.update(method="GET", url=url, headers=headers)
            return get

    monkeypatch.setattr(
        "app.modules.billing.mercadopago_gateway.httpx.AsyncClient", _FakeClient
    )
    return captured


@pytest.mark.asyncio
async def test_map_status():
    assert map_status("approved") == "paid"
    assert map_status("pending") == "pending"
    assert map_status("in_process") == "pending"
    assert map_status("rejected") == "canceled"
    assert map_status("cancelled") == "canceled"
    assert map_status(None) == "pending"


@pytest.mark.asyncio
async def test_create_pix_charge(monkeypatch):
    mp_response = {
        "id": 123456789,
        "status": "pending",
        "point_of_interaction": {
            "transaction_data": {
                "qr_code": "000201...BR.GOV.BCB.PIX",
                "qr_code_base64": "iVBORw0KGgo=",
                "ticket_url": "https://mp/ticket",
            }
        },
    }
    captured = _patch_client(monkeypatch, post=_Resp(mp_response))

    gw = MercadoPagoGateway(access_token="TEST-123", payer_email="comprador@test.com")
    charge = await gw.create_pix_charge(Decimal("150.00"), "Limpeza", "ref-abc")

    # requisição montada corretamente
    assert captured["url"].endswith("/v1/payments")
    assert captured["json"]["transaction_amount"] == 150.0
    assert captured["json"]["payment_method_id"] == "pix"
    assert captured["json"]["external_reference"] == "ref-abc"
    assert captured["json"]["payer"]["email"] == "comprador@test.com"
    assert captured["headers"]["Authorization"] == "Bearer TEST-123"
    assert captured["headers"]["X-Idempotency-Key"] == "ref-abc"

    # resposta parseada
    assert charge.charge_id == "123456789"
    assert charge.qr_code == "000201...BR.GOV.BCB.PIX"
    assert charge.qr_code_base64 == "iVBORw0KGgo="
    assert charge.status == "pending"


@pytest.mark.asyncio
async def test_get_status(monkeypatch):
    captured = _patch_client(monkeypatch, get=_Resp({"status": "approved"}))
    gw = MercadoPagoGateway(access_token="TEST-123")
    status = await gw.get_status("123456789")
    assert captured["url"].endswith("/v1/payments/123456789")
    assert status == "paid"
