from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models import TimestampMixin, UUIDPKMixin


class Clinic(UUIDPKMixin, TimestampMixin, Base):
    """O tenant. O próprio `id` é o clinic_id usado em todo o sistema."""

    __tablename__ = "clinics"

    nome: Mapped[str] = mapped_column(nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
