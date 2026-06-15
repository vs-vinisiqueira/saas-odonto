import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models import TimestampMixin, UUIDPKMixin


class WhatsAppNumber(UUIDPKMixin, TimestampMixin, Base):
    """Liga um número do WhatsApp Business (phone_number_id da Meta) a uma clínica.

    O webhook da Meta traz só o `phone_number_id`; é por aqui que descobrimos a
    qual tenant ele pertence. Escopado por clinic_id (RLS); o webhook (sem tenant)
    resolve via a função SECURITY DEFINER `whatsapp_clinic_for_number`.
    """

    __tablename__ = "whatsapp_numbers"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # ID do número na Meta (único globalmente).
    phone_number_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
