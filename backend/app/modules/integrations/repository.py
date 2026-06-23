import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.models import ClinicIntegration


async def get(
    session: AsyncSession, clinic_id: uuid.UUID | str, provider: str
) -> ClinicIntegration | None:
    result = await session.execute(
        select(ClinicIntegration).where(
            ClinicIntegration.clinic_id == clinic_id,
            ClinicIntegration.provider == provider,
        )
    )
    return result.scalar_one_or_none()


async def list_all(
    session: AsyncSession, clinic_id: uuid.UUID | str
) -> list[ClinicIntegration]:
    result = await session.execute(
        select(ClinicIntegration)
        .where(ClinicIntegration.clinic_id == clinic_id)
        .order_by(ClinicIntegration.provider)
    )
    return list(result.scalars().all())


async def add(
    session: AsyncSession, integration: ClinicIntegration
) -> ClinicIntegration:
    session.add(integration)
    await session.flush()
    return integration
