import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models import TimestampMixin, UUIDPKMixin

# Métodos e status do pagamento
METODO_PIX = "pix"

STATUS_PENDING = "pending"
STATUS_PAID = "paid"
STATUS_EXPIRED = "expired"
STATUS_CANCELED = "canceled"
PAYMENT_STATUSES = {STATUS_PENDING, STATUS_PAID, STATUS_EXPIRED, STATUS_CANCELED}


class Payment(UUIDPKMixin, TimestampMixin, Base):
    """Cobrança/pagamento. Escopado por clinic_id (RLS).

    O `charge_id` é o identificador do provedor externo (gateway) e é único
    globalmente — é por ele que o webhook (sem tenant) localiza o pagamento.
    """

    __tablename__ = "payments"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
    )
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metodo: Mapped[str] = mapped_column(
        String(16), nullable=False, default=METODO_PIX, server_default=METODO_PIX
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=STATUS_PENDING, server_default=STATUS_PENDING
    )
    # Identificador no gateway externo (único globalmente).
    charge_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    qr_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    qr_code_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
