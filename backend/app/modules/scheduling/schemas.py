import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.modules.scheduling.models import TIPO_AVALIACAO


class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    starts_at: dt.datetime
    duration_min: int = Field(default=30, ge=5, le=480)
    dentist_id: uuid.UUID | None = None
    tipo: str = TIPO_AVALIACAO
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    starts_at: dt.datetime | None = None
    duration_min: int | None = Field(default=None, ge=5, le=480)
    dentist_id: uuid.UUID | None = None
    status: str | None = None
    tipo: str | None = None
    notes: str | None = None


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    patient_nome: str | None = None
    dentist_id: uuid.UUID | None
    starts_at: dt.datetime
    ends_at: dt.datetime
    status: str
    tipo: str
    notes: str | None


class SlotOut(BaseModel):
    starts_at: dt.datetime
    ends_at: dt.datetime


class StatsOut(BaseModel):
    """Resumo da agenda num intervalo, para o dashboard."""

    total: int
    by_status: dict[str, int]
    # Contagem por dia (YYYY-MM-DD em UTC) — alimenta o gráfico semanal.
    per_day: dict[str, int]
