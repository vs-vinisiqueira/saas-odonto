import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.modules.whatsapp.models import WhatsAppNumber


async def list_for_clinic(
    session: AsyncSession, clinic_id: uuid.UUID | str
) -> list[WhatsAppNumber]:
    result = await session.execute(
        select(WhatsAppNumber)
        .where(WhatsAppNumber.clinic_id == clinic_id)
        .order_by(WhatsAppNumber.created_at)
    )
    return list(result.scalars().all())


async def get_or_create(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    phone_number_id: str,
    label: str | None = None,
) -> WhatsAppNumber:
    existing = await session.execute(
        select(WhatsAppNumber).where(
            WhatsAppNumber.clinic_id == clinic_id,
            WhatsAppNumber.phone_number_id == phone_number_id,
        )
    )
    number = existing.scalar_one_or_none()
    if number is not None:
        return number
    number = WhatsAppNumber(
        clinic_id=clinic_id, phone_number_id=phone_number_id, label=label
    )
    session.add(number)
    await session.flush()
    return number


async def resolve_clinic_for_number(phone_number_id: str) -> str | None:
    """Descobre o clinic_id de um phone_number_id SEM contexto de tenant.

    O webhook da Meta chega sem JWT. A função SECURITY DEFINER
    `whatsapp_clinic_for_number` (roda como dono das tabelas, ignora RLS) faz o
    lookup — mesmo padrão de `billing.service.handle_webhook`.
    """
    async with async_session_maker() as session:
        result = await session.execute(
            text("SELECT whatsapp_clinic_for_number(:pid)"),
            {"pid": phone_number_id},
        )
        clinic_id = result.scalar()
    return str(clinic_id) if clinic_id is not None else None
