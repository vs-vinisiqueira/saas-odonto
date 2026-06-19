"""Módulo de pacientes: CRUD escopado por tenant (RLS via get_tenant_session).

Modelo PATIENT { id, clinic_id, nome, telefone, email?, observacoes? }, com RLS
por clinic_id igual aos demais. O `telefone` é a chave de correlação com o
WhatsApp usada pelo agente de IA.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_tenant_session
from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.patients import service
from app.modules.patients.schemas import PatientCreate, PatientOut, PatientRecordOut, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientOut])
async def list_patients(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.list_patients(session, user.clinic_id)


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient(
    body: PatientCreate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.create_patient(session, user.clinic_id, body)


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(
    patient_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.get_patient(session, user.clinic_id, patient_id)


@router.patch("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: uuid.UUID,
    body: PatientUpdate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.update_patient(session, user.clinic_id, patient_id, body)


@router.get("/{patient_id}/record", response_model=PatientRecordOut)
async def get_patient_record(
    patient_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.get_patient_record(session, user.clinic_id, patient_id)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    await service.delete_patient(session, user.clinic_id, patient_id)
