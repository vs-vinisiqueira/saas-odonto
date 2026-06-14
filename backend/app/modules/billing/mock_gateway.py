"""Gateway de pagamento MOCK (esta fase).

Simula a emissão de cobrança Pix sem provedor real. Guarda o status em memória
para o `get_status`; o caminho realista de confirmação é o webhook
(POST /billing/webhook), que o provedor chamaria. Trocável por Mercado
Pago/Asaas/Stripe sem tocar no BillingService (mesmo contrato `PaymentGateway`).
"""

import uuid
from decimal import Decimal

from app.modules.billing.gateway import PaymentGateway, PixCharge


class MockPaymentGateway(PaymentGateway):
    def __init__(self) -> None:
        self._status: dict[str, str] = {}

    async def create_pix_charge(
        self, amount: Decimal, description: str, reference_id: str
    ) -> PixCharge:
        charge_id = f"mock_{uuid.uuid4().hex[:16]}"
        self._status[charge_id] = "pending"
        # QR fake só para o fluxo (um EMV/payload real viria do provedor).
        payload = f"PIX|{reference_id}|{amount}|{description}"
        return PixCharge(
            charge_id=charge_id,
            qr_code=payload,
            qr_code_base64="data:image/png;base64,bW9jaw==",
            status="pending",
        )

    async def get_status(self, charge_id: str) -> str:
        return self._status.get(charge_id, "pending")

    def _simulate(self, charge_id: str, status: str) -> None:
        """Helper de teste/dev: força um status (como se o provedor mudasse)."""
        self._status[charge_id] = status


default_gateway = MockPaymentGateway()
