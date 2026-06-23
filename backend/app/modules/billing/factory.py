"""Seleção do gateway de pagamento.

Prioridade: credenciais DA CLÍNICA (`creds`) > credenciais globais (env, compat)
> mock. O mock garante que CI/dev nunca quebrem por falta de credencial.
"""

from app.core.config import settings
from app.modules.billing.gateway import PaymentGateway
from app.modules.billing.mock_gateway import default_gateway


def get_payment_gateway(creds: dict | None = None) -> PaymentGateway:
    # 1) Credenciais da clínica (modelo multi-tenant).
    if creds and creds.get("access_token"):
        from app.modules.billing.mercadopago_gateway import MercadoPagoGateway

        return MercadoPagoGateway(
            access_token=creds["access_token"],
            payer_email=creds.get("payer_email") or settings.mercadopago_payer_email,
        )

    # 2) Credenciais globais (compatibilidade com o deploy atual via env).
    if settings.billing_provider == "mercadopago" and settings.mercadopago_access_token:
        from app.modules.billing.mercadopago_gateway import MercadoPagoGateway

        return MercadoPagoGateway(
            access_token=settings.mercadopago_access_token,
            payer_email=settings.mercadopago_payer_email,
        )

    return default_gateway
