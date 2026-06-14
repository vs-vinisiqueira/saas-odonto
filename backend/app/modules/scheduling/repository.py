import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.models import ACTIVE_STATUSES, Appointment

# RLS já isola por tenant; ainda assim filtramos por clinic_id explicitamente.


async def list_in_range(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    start: dt.datetime,
    end: dt.datetime,
    dentist_id: uuid.UUID | str | None = None,
    active_only: bool = False,
) -> list[Appointment]:
    stmt = (
        select(Appointment)
        .where(
            Appointment.clinic_id == clinic_id,
            Appointment.starts_at < end,
            Appointment.ends_at > start,
        )
        .order_by(Appointment.starts_at)
    )
    if dentist_id is not None:
        stmt = stmt.where(Appointment.dentist_id == dentist_id)
    if active_only:
        stmt = stmt.where(Appointment.status.in_(ACTIVE_STATUSES))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_by_id(
    session: AsyncSession, clinic_id: uuid.UUID | str, appointment_id: uuid.UUID | str
) -> Appointment | None:
    result = await session.execute(
        select(Appointment).where(
            Appointment.id == appointment_id, Appointment.clinic_id == clinic_id
        )
    )
    return result.scalar_one_or_none()


async def find_conflict(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    start: dt.datetime,
    end: dt.datetime,
    dentist_id: uuid.UUID | str | None,
    exclude_id: uuid.UUID | str | None = None,
) -> Appointment | None:
    """Retorna um agendamento ATIVO que colide com [start, end), se houver.

    O conflito é por dentista quando `dentist_id` é dado; sem dentista, qualquer
    agendamento da clínica que se sobreponha conta como conflito.
    """
    stmt = select(Appointment).where(
        Appointment.clinic_id == clinic_id,
        Appointment.status.in_(ACTIVE_STATUSES),
        Appointment.starts_at < end,
        Appointment.ends_at > start,
    )
    if dentist_id is not None:
        stmt = stmt.where(Appointment.dentist_id == dentist_id)
    if exclude_id is not None:
        stmt = stmt.where(Appointment.id != exclude_id)
    result = await session.execute(stmt.limit(1))
    return result.scalar_one_or_none()


async def add(session: AsyncSession, appointment: Appointment) -> Appointment:
    session.add(appointment)
    await session.flush()
    return appointment
