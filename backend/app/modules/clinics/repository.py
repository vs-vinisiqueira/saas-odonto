import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clinics.models import Clinic


async def get_by_id(session: AsyncSession, clinic_id: uuid.UUID | str) -> Clinic | None:
    result = await session.execute(select(Clinic).where(Clinic.id == clinic_id))
    return result.scalar_one_or_none()
