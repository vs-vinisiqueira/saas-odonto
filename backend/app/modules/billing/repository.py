import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import Payment


async def list_all(session: AsyncSession, clinic_id: uuid.UUID | str) -> list[Payment]:
    result = await session.execute(
        select(Payment)
        .where(Payment.clinic_id == clinic_id)
        .order_by(Payment.created_at.desc())
    )
    return list(result.scalars().all())


async def get_by_id(
    session: AsyncSession, clinic_id: uuid.UUID | str, payment_id: uuid.UUID | str
) -> Payment | None:
    result = await session.execute(
        select(Payment).where(
            Payment.id == payment_id, Payment.clinic_id == clinic_id
        )
    )
    return result.scalar_one_or_none()


async def get_by_charge_id(
    session: AsyncSession, charge_id: str
) -> Payment | None:
    """Busca por charge_id (já dentro de um tenant scope). Sem filtro de clinic
    porque o webhook abre a sessão no tenant correto antes de chamar."""
    result = await session.execute(
        select(Payment).where(Payment.charge_id == charge_id)
    )
    return result.scalar_one_or_none()


async def add(session: AsyncSession, payment: Payment) -> Payment:
    session.add(payment)
    await session.flush()
    return payment
