"""Teste unitário (sem rede/DB) da verificação de assinatura do webhook do
Mercado Pago — o header `x-signature` (HMAC-SHA256 do manifesto `id;request-id;ts`).
"""

import hashlib
import hmac

from starlette.requests import Request

from app.modules.billing import router as billing_router


def _make_request(headers: dict[str, str]) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/billing/mercadopago/webhook",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
    }
    return Request(scope)


def _valid_signature(secret: str, data_id: str, request_id: str, ts: str) -> str:
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{ts};"
    return hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()


def test_sem_secret_libera(monkeypatch):
    # Compat: sem segredo configurado, a verificação é pulada (aceita).
    monkeypatch.setattr(billing_router.settings, "mercadopago_webhook_secret", None)
    req = _make_request({})
    assert billing_router._verify_mercadopago_signature(req, "PAY123") is True


def test_assinatura_valida(monkeypatch):
    secret = "mp-webhook-secret"
    monkeypatch.setattr(billing_router.settings, "mercadopago_webhook_secret", secret)
    data_id, request_id, ts = "PAY123", "req-abc", "1700000000"
    v1 = _valid_signature(secret, data_id, request_id, ts)
    req = _make_request({"x-signature": f"ts={ts},v1={v1}", "x-request-id": request_id})
    assert billing_router._verify_mercadopago_signature(req, data_id) is True


def test_assinatura_invalida_ou_ausente(monkeypatch):
    secret = "mp-webhook-secret"
    monkeypatch.setattr(billing_router.settings, "mercadopago_webhook_secret", secret)
    data_id, request_id, ts = "PAY123", "req-abc", "1700000000"
    v1 = _valid_signature(secret, data_id, request_id, ts)

    # v1 correto, mas para OUTRO data_id => rejeita.
    req = _make_request({"x-signature": f"ts={ts},v1={v1}", "x-request-id": request_id})
    assert billing_router._verify_mercadopago_signature(req, "PAY999") is False

    # Header x-signature ausente => rejeita.
    assert billing_router._verify_mercadopago_signature(_make_request({}), data_id) is False

    # Falta o campo v1 => rejeita.
    req = _make_request({"x-signature": f"ts={ts}", "x-request-id": request_id})
    assert billing_router._verify_mercadopago_signature(req, data_id) is False
