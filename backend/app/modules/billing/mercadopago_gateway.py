"""Gateway de pagamento real: Mercado Pago (Pix).

Cria uma cobrança Pix (retorna o QR copia-e-cola + imagem) e consulta o status.
Implementa a mesma interface `PaymentGateway` do mock. No sandbox use o Access
Token de TESTE (TEST-...). O status do Mercado Pago é mapeado para o nosso
conjunto (`pending`/`paid`/`canceled`).
"""

from __future__ import annotations

import logging
from decimal import Decimal

import httpx

from app.modules.billing.gateway import PaymentGateway, PixCharge
from app.modules.billing.models import (
    STATUS_CANCELED,
    STATUS_PAID,
    STATUS_PENDING,
)

logger = logging.getLogger("billing.mercadopago")

# Mercado Pago -> nosso status interno.
_STATUS_MAP = {
    "approved": STATUS_PAID,
    "authorized": STATUS_PENDING,
    "in_process": STATUS_PENDING,
    "pending": STATUS_PENDING,
    "in_mediation": STATUS_PENDING,
    "rejected": STATUS_CANCELED,
    "cancelled": STATUS_CANCELED,
    "refunded": STATUS_CANCELED,
    "charged_back": STATUS_CANCELED,
}


def map_status(mp_status: str | None) -> str:
    return _STATUS_MAP.get(mp_status or "", STATUS_PENDING)


class MercadoPagoGateway(PaymentGateway):
    def __init__(
        self,
        access_token: str,
        payer_email: str = "test_user@testuser.com",
        base_url: str = "https://api.mercadopago.com",
    ) -> None:
        self._token = access_token
        self._payer_email = payer_email
        self._base = base_url

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        return headers

    async def create_pix_charge(
        self, amount: Decimal, description: str, reference_id: str
    ) -> PixCharge:
        body = {
            "transaction_amount": float(amount),
            "description": description,
            "payment_method_id": "pix",
            "external_reference": reference_id,
            "payer": {"email": self._payer_email},
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{self._base}/v1/payments",
                json=body,
                headers=self._headers(idempotency_key=reference_id),
            )
        resp.raise_for_status()
        data = resp.json()
        tx = (data.get("point_of_interaction") or {}).get("transaction_data") or {}
        return PixCharge(
            charge_id=str(data["id"]),
            qr_code=tx.get("qr_code"),
            qr_code_base64=tx.get("qr_code_base64"),
            status=map_status(data.get("status")),
        )

    async def get_status(self, charge_id: str) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                f"{self._base}/v1/payments/{charge_id}", headers=self._headers()
            )
        resp.raise_for_status()
        return map_status(resp.json().get("status"))
