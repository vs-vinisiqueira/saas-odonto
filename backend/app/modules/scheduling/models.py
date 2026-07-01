import datetime as dt
import uuid

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models import TimestampMixin, UUIDPKMixin

# Status do agendamento
STATUS_SCHEDULED = "scheduled"
STATUS_CONFIRMED = "confirmed"
STATUS_CANCELLED = "cancelled"
STATUS_COMPLETED = "completed"
STATUS_NO_SHOW = "no_show"
APPOINTMENT_STATUSES = {
    STATUS_SCHEDULED,
    STATUS_CONFIRMED,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_NO_SHOW,
}
# Status que "ocupam" um horário (entram na checagem de conflito/disponibilidade).
ACTIVE_STATUSES = (STATUS_SCHEDULED, STATUS_CONFIRMED)

# Tipo da consulta (colore a grade da agenda no frontend). Campo livre (não
# enum de banco) para facilitar evolução; validado na camada de schema.
TIPO_AVALIACAO = "avaliacao"
TIPO_LIMPEZA = "limpeza"
TIPO_RESTAURACAO = "restauracao"
TIPO_CANAL = "canal"
TIPO_CLAREAMENTO = "clareamento"
TIPO_CIRURGIA = "cirurgia"
APPOINTMENT_TIPOS = {
    TIPO_AVALIACAO,
    TIPO_LIMPEZA,
    TIPO_RESTAURACAO,
    TIPO_CANAL,
    TIPO_CLAREAMENTO,
    TIPO_CIRURGIA,
}


class Appointment(UUIDPKMixin, TimestampMixin, Base):
    """Agendamento. Fonte da verdade interna da agenda (escopado por clinic_id)."""

    __tablename__ = "appointments"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Dentista responsável (opcional). users.role == 'dentist'.
    dentist_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    starts_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    ends_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=STATUS_SCHEDULED, server_default=STATUS_SCHEDULED
    )
    tipo: Mapped[str] = mapped_column(
        String(30), nullable=False, default=TIPO_AVALIACAO, server_default=TIPO_AVALIACAO
    )
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
