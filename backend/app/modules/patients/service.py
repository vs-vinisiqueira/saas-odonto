import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients import repository
from app.modules.patients.models import Patient
from app.modules.patients.schemas import PatientCreate, PatientUpdate
from app.shared.exceptions import NotFound


async def list_patients(
    session: AsyncSession, clinic_id: uuid.UUID | str
) -> list[Patient]:
    return await repository.list_all(session, clinic_id)


async def get_patient(
    session: AsyncSession, clinic_id: uuid.UUID | str, patient_id: uuid.UUID | str
) -> Patient:
    patient = await repository.get_by_id(session, clinic_id, patient_id)
    if patient is None:
        raise NotFound("Paciente não encontrado")
    return patient


async def create_patient(
    session: AsyncSession, clinic_id: uuid.UUID | str, data: PatientCreate
) -> Patient:
    patient = Patient(
        clinic_id=clinic_id,
        nome=data.nome,
        telefone=data.telefone,
        email=data.email,
        observacoes=data.observacoes,
    )
    return await repository.add(session, patient)


async def update_patient(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    patient_id: uuid.UUID | str,
    data: PatientUpdate,
) -> Patient:
    patient = await get_patient(session, clinic_id, patient_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    await session.flush()
    return patient


async def delete_patient(
    session: AsyncSession, clinic_id: uuid.UUID | str, patient_id: uuid.UUID | str
) -> None:
    patient = await get_patient(session, clinic_id, patient_id)
    await repository.delete(session, patient)
