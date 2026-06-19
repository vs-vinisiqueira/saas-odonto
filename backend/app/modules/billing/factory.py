"""Seleção do gateway de pagamento conforme a config.

Default = mock. "mercadopago" só é usado se houver MERCADOPAGO_ACCESS_TOKEN;
caso contrário cai no mock — assim CI/dev nunca quebram por falta de credencial.
"""

from app.core.config import settings
from app.modules.billing.gateway import PaymentGateway
from app.modules.billing.mock_gateway import default_gateway


def get_payment_gateway() -> PaymentGateway:
    if settings.billing_provider == "mercadopago" and settings.mercadopago_access_token:
        from app.modules.billing.mercadopago_gateway import MercadoPagoGateway

        return MercadoPagoGateway(
            access_token=settings.mercadopago_access_token,
            payer_email=settings.mercadopago_payer_email,
        )
    return default_gateway
