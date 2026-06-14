"""Contrato de gateway de pagamento (adapter).

O provedor concreto (Mercado Pago / Asaas / Stripe) será decidido depois. O
BillingService dependerá SEMPRE desta interface, nunca de um provedor concreto
— mesmo padrão de adapter do canal de WhatsApp.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PixCharge:
    charge_id: str
    qr_code: str
    qr_code_base64: str
    status: str  # pending | paid | expired | canceled


class PaymentGateway(ABC):
    @abstractmethod
    async def create_pix_charge(
        self, amount: Decimal, description: str, reference_id: str
    ) -> PixCharge: ...

    @abstractmethod
    async def get_status(self, charge_id: str) -> str: ...
