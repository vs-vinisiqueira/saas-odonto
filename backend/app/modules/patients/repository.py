import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.models import Patient

# Nota: o RLS já garante o isolamento por tenant. Ainda assim filtramos por
# clinic_id explicitamente (defesa em profundidade e clareza de intenção).


async def list_all(session: AsyncSession, clinic_id: uuid.UUID | str) -> list[Patient]:
    result = await session.execute(
        select(Patient).where(Patient.clinic_id == clinic_id).order_by(Patient.nome)
    )
    return list(result.scalars().all())


async def get_by_id(
    session: AsyncSession, clinic_id: uuid.UUID | str, patient_id: uuid.UUID | str
) -> Patient | None:
    result = await session.execute(
        select(Patient).where(
            Patient.id == patient_id, Patient.clinic_id == clinic_id
        )
    )
    return result.scalar_one_or_none()


async def get_by_telefone(
    session: AsyncSession, clinic_id: uuid.UUID | str, telefone: str
) -> Patient | None:
    result = await session.execute(
        select(Patient).where(
            Patient.clinic_id == clinic_id, Patient.telefone == telefone
        )
    )
    return result.scalars().first()


async def add(session: AsyncSession, patient: Patient) -> Patient:
    session.add(patient)
    await session.flush()
    return patient


async def delete(session: AsyncSession, patient: Patient) -> None:
    await session.delete(patient)
    await session.flush()
