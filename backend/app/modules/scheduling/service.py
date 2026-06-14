"""Casos de uso da agenda.

`buscar_horarios` e `agendar` são as operações que o agente de IA expõe como
tools. Toda escrita também é empurrada para o calendário externo via o port
`calendar_sync` (no-op por enquanto).
"""

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.patients import repository as patients_repo
from app.modules.scheduling import repository
from app.modules.scheduling.calendar_sync import CalendarSync, default_calendar_sync
from app.modules.scheduling.models import (
    APPOINTMENT_STATUSES,
    STATUS_CANCELLED,
    Appointment,
)
from app.modules.scheduling.schemas import AppointmentCreate, AppointmentUpdate
from app.shared.exceptions import Conflict, NotFound

# Janela de atendimento (UTC) e granularidade padrão dos slots. Simplificação:
# o fuso local da clínica e os dias de funcionamento entram numa fase futura.
WORK_START_HOUR = 9
WORK_END_HOUR = 18
DEFAULT_SLOT_MIN = 30

UTC = dt.timezone.utc


def _ensure_utc(value: dt.datetime) -> dt.datetime:
    """Garante datetime tz-aware em UTC (entrada do cliente pode vir naïve)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class ConflictError(Conflict):
    """Horário indisponível (colide com outro agendamento)."""

    def __init__(self, detail: str = "Horário indisponível (conflito de agenda)"):
        super().__init__(detail=detail)


async def _validate_patient(session, clinic_id, patient_id: uuid.UUID) -> None:
    patient = await patients_repo.get_by_id(session, clinic_id, patient_id)
    if patient is None:
        raise NotFound("Paciente não encontrado")


async def _validate_dentist(session, dentist_id: uuid.UUID | None) -> None:
    if dentist_id is None:
        return
    # RLS já escopa users ao tenant atual.
    result = await session.execute(select(User).where(User.id == dentist_id))
    if result.scalar_one_or_none() is None:
        raise NotFound("Dentista não encontrado")


async def buscar_horarios(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    day: dt.date,
    dentist_id: uuid.UUID | None = None,
    slot_min: int = DEFAULT_SLOT_MIN,
    now: dt.datetime | None = None,
) -> list[dict]:
    """Lista os horários livres de um dia (slots de `slot_min` minutos)."""
    day_start = dt.datetime.combine(day, dt.time(WORK_START_HOUR), tzinfo=UTC)
    day_end = dt.datetime.combine(day, dt.time(WORK_END_HOUR), tzinfo=UTC)
    now = now or dt.datetime.now(UTC)

    busy = await repository.list_in_range(
        session, clinic_id, day_start, day_end, dentist_id, active_only=True
    )

    slots: list[dict] = []
    step = dt.timedelta(minutes=slot_min)
    cursor = day_start
    while cursor + step <= day_end:
        slot_end = cursor + step
        if cursor >= now and not any(
            a.starts_at < slot_end and a.ends_at > cursor for a in busy
        ):
            slots.append({"starts_at": cursor, "ends_at": slot_end})
        cursor = slot_end
    return slots


async def agendar(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    data: AppointmentCreate,
    calendar: CalendarSync = default_calendar_sync,
) -> Appointment:
    """Cria um agendamento, validando paciente, dentista e conflito de horário."""
    starts_at = _ensure_utc(data.starts_at)
    ends_at = starts_at + dt.timedelta(minutes=data.duration_min)

    await _validate_patient(session, clinic_id, data.patient_id)
    await _validate_dentist(session, data.dentist_id)

    conflict = await repository.find_conflict(
        session, clinic_id, starts_at, ends_at, data.dentist_id
    )
    if conflict is not None:
        raise ConflictError()

    appointment = Appointment(
        clinic_id=clinic_id,
        patient_id=data.patient_id,
        dentist_id=data.dentist_id,
        starts_at=starts_at,
        ends_at=ends_at,
        notes=data.notes,
    )
    await repository.add(session, appointment)
    await calendar.upsert_event(appointment)
    return appointment


async def list_appointments(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    day: dt.date | None = None,
    dentist_id: uuid.UUID | None = None,
) -> list[Appointment]:
    if day is not None:
        start = dt.datetime.combine(day, dt.time.min, tzinfo=UTC)
        end = start + dt.timedelta(days=1)
    else:
        # Janela ampla padrão: do início de hoje aos próximos 90 dias.
        start = dt.datetime.combine(dt.datetime.now(UTC).date(), dt.time.min, tzinfo=UTC)
        end = start + dt.timedelta(days=90)
    return await repository.list_in_range(session, clinic_id, start, end, dentist_id)


async def get_appointment(
    session: AsyncSession, clinic_id: uuid.UUID | str, appointment_id: uuid.UUID | str
) -> Appointment:
    appt = await repository.get_by_id(session, clinic_id, appointment_id)
    if appt is None:
        raise NotFound("Agendamento não encontrado")
    return appt


async def update_appointment(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    appointment_id: uuid.UUID | str,
    data: AppointmentUpdate,
    calendar: CalendarSync = default_calendar_sync,
) -> Appointment:
    appt = await get_appointment(session, clinic_id, appointment_id)

    if data.status is not None:
        if data.status not in APPOINTMENT_STATUSES:
            raise NotFound(f"Status inválido: {data.status}")
        appt.status = data.status
    if data.dentist_id is not None:
        await _validate_dentist(session, data.dentist_id)
        appt.dentist_id = data.dentist_id
    if data.notes is not None:
        appt.notes = data.notes

    # Reagendamento: recalcula janela e revalida conflito.
    if data.starts_at is not None or data.duration_min is not None:
        new_start = _ensure_utc(data.starts_at) if data.starts_at else appt.starts_at
        duration = (
            data.duration_min
            if data.duration_min is not None
            else int((appt.ends_at - appt.starts_at).total_seconds() // 60)
        )
        new_end = new_start + dt.timedelta(minutes=duration)
        conflict = await repository.find_conflict(
            session, clinic_id, new_start, new_end, appt.dentist_id, exclude_id=appt.id
        )
        if conflict is not None:
            raise ConflictError()
        appt.starts_at = new_start
        appt.ends_at = new_end

    await session.flush()
    if appt.status == STATUS_CANCELLED:
        await calendar.delete_event(appt)
    else:
        await calendar.upsert_event(appt)
    return appt


async def cancel_appointment(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    appointment_id: uuid.UUID | str,
    calendar: CalendarSync = default_calendar_sync,
) -> Appointment:
    appt = await get_appointment(session, clinic_id, appointment_id)
    appt.status = STATUS_CANCELLED
    await session.flush()
    await calendar.delete_event(appt)
    return appt
