"""Módulo de agendamento: agenda interna (fonte da verdade) + disponibilidade.

As operações `buscar_horarios` (GET /scheduling/availability) e `agendar`
(POST /scheduling/appointments) são os casos de uso que o agente de IA expõe
como tools. Tudo escopado por tenant via RLS (get_tenant_session).
"""

import datetime as dt
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_tenant_session
from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.scheduling import service
from app.modules.scheduling.schemas import (
    AppointmentCreate,
    AppointmentOut,
    AppointmentUpdate,
    SlotOut,
)

router = APIRouter(prefix="/scheduling", tags=["scheduling"])


@router.get("/availability", response_model=list[SlotOut])
async def availability(
    date: dt.date = Query(..., description="Dia a consultar (YYYY-MM-DD)"),
    dentist_id: uuid.UUID | None = Query(default=None),
    slot_min: int = Query(default=service.DEFAULT_SLOT_MIN, ge=5, le=480),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.buscar_horarios(
        session, user.clinic_id, date, dentist_id, slot_min
    )


@router.get("/appointments", response_model=list[AppointmentOut])
async def list_appointments(
    date: dt.date | None = Query(default=None),
    dentist_id: uuid.UUID | None = Query(default=None),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.list_appointments(session, user.clinic_id, date, dentist_id)


@router.post(
    "/appointments", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED
)
async def create_appointment(
    body: AppointmentCreate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.agendar(session, user.clinic_id, body)


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
async def get_appointment(
    appointment_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.get_appointment(session, user.clinic_id, appointment_id)


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentUpdate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.update_appointment(
        session, user.clinic_id, appointment_id, body
    )


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.cancel_appointment(session, user.clinic_id, appointment_id)
