"""Casos de uso da agenda.

`buscar_horarios` e `agendar` são as operações que o agente de IA expõe como
tools. Toda escrita também é empurrada para o calendário externo via o port
`calendar_sync` (no-op por enquanto).
"""

import datetime as dt
import logging
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.clinics import repository as clinics_repo
from app.modules.patients import repository as patients_repo
from app.modules.scheduling import repository
from app.modules.scheduling.calendar_sync import CalendarSync
from app.modules.scheduling.calendar_factory import get_calendar_sync

default_calendar_sync = get_calendar_sync()
from app.modules.scheduling.models import (
    APPOINTMENT_STATUSES,
    APPOINTMENT_TIPOS,
    STATUS_CANCELLED,
    Appointment,
)
from app.modules.scheduling.schemas import AppointmentCreate, AppointmentUpdate
from app.shared.exceptions import Conflict, NotFound

# Janela de atendimento padrão e granularidade dos slots. Os horários de
# funcionamento ("09:00" etc.) são interpretados no FUSO da clínica (config
# `timezone`), não em UTC — ver `_clinic_tz`/`buscar_horarios`.
WORK_START_HOUR = 9
WORK_END_HOUR = 18
DEFAULT_SLOT_MIN = 30

UTC = dt.timezone.utc
# Produto BR: sem `timezone` na config, assume-se o horário de Brasília.
DEFAULT_TZ = "America/Sao_Paulo"

# Chave de dia da semana usada em `clinics.config["working_hours"]`, alinhada
# com `date.weekday()` (0=segunda).
WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

logger = logging.getLogger("scheduling.service")


def _clinic_tz(config: dict | None) -> dt.tzinfo:
    """Fuso da clínica a partir do config (default America/Sao_Paulo).

    Um valor inválido cai no default; se nem o default resolver (base de fusos
    ausente), cai em UTC — nunca estoura, a agenda sempre tem um fuso.
    """
    name = (config or {}).get("timezone") or DEFAULT_TZ
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        pass
    try:
        return ZoneInfo(DEFAULT_TZ)
    except (ZoneInfoNotFoundError, ValueError):
        logger.warning("Base de fusos indisponível; usando UTC para a agenda.")
        return UTC


async def clinic_timezone(
    session: AsyncSession, clinic_id: uuid.UUID | str
) -> dt.tzinfo:
    """Fuso da clínica (para formatar/interpretar horários fora do service)."""
    clinic = await clinics_repo.get_by_id(session, clinic_id)
    return _clinic_tz(clinic.config if clinic else None)


async def _calendar_for_clinic(
    session: AsyncSession, clinic_id: uuid.UUID | str
) -> CalendarSync:
    """Calendário com as credenciais DA CLÍNICA quando configuradas; senão o
    padrão global (NullCalendarSync no-op)."""
    try:
        from app.modules.integrations import service as integrations_service

        creds = await integrations_service.load_credentials(
            session, clinic_id, "google_calendar"
        )
        if creds:
            return get_calendar_sync(creds)
    except Exception:
        logger.exception("Falha ao carregar calendário da clínica; usando padrão")
    return default_calendar_sync


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


async def _attach_patient_nome(
    session: AsyncSession, clinic_id: uuid.UUID | str, appt: Appointment
) -> Appointment:
    """Anexa `patient_nome` (atributo transiente, não mapeado) para a resposta."""
    patient = await patients_repo.get_by_id(session, clinic_id, appt.patient_id)
    appt.patient_nome = patient.nome if patient else None
    return appt


async def _attach_patient_nomes(
    session: AsyncSession, clinic_id: uuid.UUID | str, appts: list[Appointment]
) -> list[Appointment]:
    if not appts:
        return appts
    patients = {p.id: p.nome for p in await patients_repo.list_all(session, clinic_id)}
    for a in appts:
        a.patient_nome = patients.get(a.patient_id)
    return appts


def _validate_tipo(tipo: str) -> None:
    if tipo not in APPOINTMENT_TIPOS:
        raise NotFound(f"Tipo de consulta inválido: {tipo}")


async def _validate_dentist(session, dentist_id: uuid.UUID | None) -> None:
    if dentist_id is None:
        return
    # RLS já escopa users ao tenant atual.
    result = await session.execute(select(User).where(User.id == dentist_id))
    if result.scalar_one_or_none() is None:
        raise NotFound("Dentista não encontrado")


def _parse_hhmm(value: str | None, default: dt.time) -> dt.time:
    if not value:
        return default
    try:
        h, m = value.split(":")
        return dt.time(int(h), int(m))
    except (ValueError, TypeError):
        return default


def _working_hours_for_day(config: dict | None, day: dt.date) -> dict | None:
    """Janela de atendimento da clínica no dia, lendo `config.working_hours`.

    Sem configuração (clínica ainda não usou a tela de Horários): cai no
    fallback fixo 09-18h (compatibilidade com clínicas já em uso). Retorna
    `None` quando o dia está marcado como fechado (sem slots). Os horários são
    `dt.time` "ingênuos" — o fuso é aplicado por quem monta os datetimes.
    """
    default_start = dt.time(WORK_START_HOUR)
    default_end = dt.time(WORK_END_HOUR)

    working_hours = (config or {}).get("working_hours")
    if not working_hours:
        return {"start": default_start, "end": default_end, "lunch_start": None, "lunch_end": None}

    day_cfg = working_hours.get(WEEKDAY_KEYS[day.weekday()])
    if not day_cfg:
        return {"start": default_start, "end": default_end, "lunch_start": None, "lunch_end": None}
    if day_cfg.get("closed"):
        return None

    return {
        "start": _parse_hhmm(day_cfg.get("start"), default_start),
        "end": _parse_hhmm(day_cfg.get("end"), default_end),
        "lunch_start": _parse_hhmm(day_cfg.get("lunch_start"), None) if day_cfg.get("lunch_start") else None,
        "lunch_end": _parse_hhmm(day_cfg.get("lunch_end"), None) if day_cfg.get("lunch_end") else None,
    }


async def buscar_horarios(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    day: dt.date,
    dentist_id: uuid.UUID | None = None,
    slot_min: int = DEFAULT_SLOT_MIN,
    now: dt.datetime | None = None,
) -> list[dict]:
    """Lista os horários livres de um dia (slots de `slot_min` minutos).

    Os horários de funcionamento são interpretados no fuso da clínica e
    convertidos para UTC — os slots retornados são instantes UTC tz-aware.
    """
    clinic = await clinics_repo.get_by_id(session, clinic_id)
    config = clinic.config if clinic else None
    tz = _clinic_tz(config)

    hours = _working_hours_for_day(config, day)
    if hours is None:
        return []  # clínica fechada nesse dia da semana

    def _at(t: dt.time | None) -> dt.datetime | None:
        # Combina data+hora no fuso da clínica e converte para UTC.
        return dt.datetime.combine(day, t, tzinfo=tz).astimezone(UTC) if t else None

    day_start = _at(hours["start"])
    day_end = _at(hours["end"])
    lunch_start = _at(hours["lunch_start"])
    lunch_end = _at(hours["lunch_end"])
    now = now or dt.datetime.now(UTC)

    busy = await repository.list_in_range(
        session, clinic_id, day_start, day_end, dentist_id, active_only=True
    )

    slots: list[dict] = []
    step = dt.timedelta(minutes=slot_min)
    cursor = day_start
    while cursor + step <= day_end:
        slot_end = cursor + step
        in_lunch = lunch_start and lunch_end and cursor < lunch_end and slot_end > lunch_start
        if (
            cursor >= now
            and not in_lunch
            and not any(a.starts_at < slot_end and a.ends_at > cursor for a in busy)
        ):
            slots.append({"starts_at": cursor, "ends_at": slot_end})
        cursor = slot_end
    return slots


async def agendar(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    data: AppointmentCreate,
    calendar: CalendarSync | None = None,
) -> Appointment:
    """Cria um agendamento, validando paciente, dentista e conflito de horário."""
    calendar = calendar or await _calendar_for_clinic(session, clinic_id)
    starts_at = _ensure_utc(data.starts_at)
    ends_at = starts_at + dt.timedelta(minutes=data.duration_min)

    # Nunca agendar no passado (vale para todos os caminhos: painel e agente).
    if starts_at < dt.datetime.now(UTC):
        raise ConflictError("Não é possível agendar em um horário no passado")

    await _validate_patient(session, clinic_id, data.patient_id)
    await _validate_dentist(session, data.dentist_id)
    _validate_tipo(data.tipo)

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
        tipo=data.tipo,
        notes=data.notes,
    )
    # find_conflict acima é o caminho rápido; a constraint EXCLUDE (migration 0012)
    # é o backstop contra a race de dois agendamentos simultâneos. O savepoint
    # mantém a transação externa utilizável se a constraint disparar.
    try:
        async with session.begin_nested():
            await repository.add(session, appointment)
    except IntegrityError:
        raise ConflictError()
    await calendar.upsert_event(appointment)
    return await _attach_patient_nome(session, clinic_id, appointment)


async def list_appointments(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    day: dt.date | None = None,
    dentist_id: uuid.UUID | None = None,
    from_date: dt.date | None = None,
    to_date: dt.date | None = None,
) -> list[Appointment]:
    if from_date is not None:
        # Range explícito (ex.: visão semanal) — `to_date` é inclusivo.
        start = dt.datetime.combine(from_date, dt.time.min, tzinfo=UTC)
        end_day = to_date or from_date
        end = dt.datetime.combine(end_day, dt.time.min, tzinfo=UTC) + dt.timedelta(days=1)
    elif day is not None:
        start = dt.datetime.combine(day, dt.time.min, tzinfo=UTC)
        end = start + dt.timedelta(days=1)
    else:
        # Janela ampla padrão: do início de hoje aos próximos 90 dias.
        start = dt.datetime.combine(dt.datetime.now(UTC).date(), dt.time.min, tzinfo=UTC)
        end = start + dt.timedelta(days=90)
    appts = await repository.list_in_range(session, clinic_id, start, end, dentist_id)
    return await _attach_patient_nomes(session, clinic_id, appts)


async def stats(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    start_date: dt.date,
    end_date: dt.date,
) -> dict:
    """Contagem de agendamentos por status num intervalo [start_date, end_date]."""
    start = dt.datetime.combine(start_date, dt.time.min, tzinfo=UTC)
    end = dt.datetime.combine(end_date, dt.time.min, tzinfo=UTC) + dt.timedelta(days=1)
    appts = await repository.list_in_range(session, clinic_id, start, end)
    by_status: dict[str, int] = {}
    per_day: dict[str, int] = {}
    for a in appts:
        by_status[a.status] = by_status.get(a.status, 0) + 1
        day = a.starts_at.astimezone(UTC).date().isoformat()
        per_day[day] = per_day.get(day, 0) + 1
    return {"total": len(appts), "by_status": by_status, "per_day": per_day}


async def get_appointment(
    session: AsyncSession, clinic_id: uuid.UUID | str, appointment_id: uuid.UUID | str
) -> Appointment:
    appt = await repository.get_by_id(session, clinic_id, appointment_id)
    if appt is None:
        raise NotFound("Agendamento não encontrado")
    return await _attach_patient_nome(session, clinic_id, appt)


async def update_appointment(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    appointment_id: uuid.UUID | str,
    data: AppointmentUpdate,
    calendar: CalendarSync | None = None,
) -> Appointment:
    calendar = calendar or await _calendar_for_clinic(session, clinic_id)
    appt = await get_appointment(session, clinic_id, appointment_id)

    if data.status is not None:
        if data.status not in APPOINTMENT_STATUSES:
            raise NotFound(f"Status inválido: {data.status}")
        appt.status = data.status
    if data.dentist_id is not None:
        await _validate_dentist(session, data.dentist_id)
        appt.dentist_id = data.dentist_id
    if data.tipo is not None:
        _validate_tipo(data.tipo)
        appt.tipo = data.tipo
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

    try:
        async with session.begin_nested():
            await session.flush()
    except IntegrityError:
        raise ConflictError()
    if appt.status == STATUS_CANCELLED:
        await calendar.delete_event(appt)
    else:
        await calendar.upsert_event(appt)
    return appt


async def cancel_appointment(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    appointment_id: uuid.UUID | str,
    calendar: CalendarSync | None = None,
) -> Appointment:
    calendar = calendar or await _calendar_for_clinic(session, clinic_id)
    appt = await get_appointment(session, clinic_id, appointment_id)
    appt.status = STATUS_CANCELLED
    await session.flush()
    await calendar.delete_event(appt)
    return appt


async def delete_appointment(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    appointment_id: uuid.UUID | str,
    calendar: CalendarSync | None = None,
) -> None:
    calendar = calendar or await _calendar_for_clinic(session, clinic_id)
    appt = await get_appointment(session, clinic_id, appointment_id)
    await calendar.delete_event(appt)
    await session.delete(appt)
    await session.flush()
