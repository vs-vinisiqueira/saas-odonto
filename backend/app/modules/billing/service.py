"""Casos de uso do financeiro.

A criação de cobrança fala com o `PaymentGateway` (mock por enquanto). O webhook
do provedor chega SEM JWT/tenant: resolvemos a clínica do `charge_id` por uma
função SECURITY DEFINER (que ignora o RLS, como o login faz) e então abrimos uma
sessão escopada nesse tenant para atualizar o pagamento sob RLS.
"""

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.tenant import open_tenant_session
from app.modules.billing import repository
from app.modules.billing.gateway import PaymentGateway
from app.modules.billing.mock_gateway import default_gateway
from app.modules.billing.models import PAYMENT_STATUSES, Payment
from app.modules.billing.schemas import ChargeCreate
from app.shared.exceptions import NotFound


async def create_charge(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    data: ChargeCreate,
    gateway: PaymentGateway = default_gateway,
) -> Payment:
    payment_id = uuid.uuid4()
    charge = await gateway.create_pix_charge(
        amount=data.valor,
        description=data.descricao or "Cobrança",
        reference_id=str(payment_id),
    )
    payment = Payment(
        id=payment_id,
        clinic_id=clinic_id,
        patient_id=data.patient_id,
        appointment_id=data.appointment_id,
        valor=data.valor,
        descricao=data.descricao,
        status=charge.status,
        charge_id=charge.charge_id,
        qr_code=charge.qr_code,
        qr_code_base64=charge.qr_code_base64,
    )
    return await repository.add(session, payment)


async def list_payments(
    session: AsyncSession, clinic_id: uuid.UUID | str
) -> list[Payment]:
    return await repository.list_all(session, clinic_id)


async def get_payment(
    session: AsyncSession, clinic_id: uuid.UUID | str, payment_id: uuid.UUID | str
) -> Payment:
    payment = await repository.get_by_id(session, clinic_id, payment_id)
    if payment is None:
        raise NotFound("Pagamento não encontrado")
    return payment


async def refresh_status(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    payment_id: uuid.UUID | str,
    gateway: PaymentGateway = default_gateway,
) -> Payment:
    payment = await get_payment(session, clinic_id, payment_id)
    payment.status = await gateway.get_status(payment.charge_id)
    await session.flush()
    return payment


async def handle_webhook(charge_id: str, status: str) -> bool:
    """Atualiza o status de um pagamento a partir do webhook do provedor.

    Sem tenant no request: resolve a clínica pelo charge_id (SECURITY DEFINER) e
    atualiza dentro do tenant. Retorna False se o charge_id é desconhecido.
    """
    if status not in PAYMENT_STATUSES:
        return False

    # 1) descobre o tenant ignorando o RLS (função roda como dono das tabelas).
    async with async_session_maker() as s:
        result = await s.execute(
            text("SELECT billing_clinic_for_charge(:c)"), {"c": charge_id}
        )
        clinic_id = result.scalar()
    if clinic_id is None:
        return False

    # 2) atualiza sob o tenant correto (RLS ativo).
    async with open_tenant_session(clinic_id) as session:
        payment = await repository.get_by_charge_id(session, charge_id)
        if payment is None:
            return False
        payment.status = status
        await session.flush()
    return True
