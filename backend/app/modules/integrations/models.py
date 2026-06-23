import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models import TimestampMixin, UUIDPKMixin


class ClinicIntegration(UUIDPKMixin, TimestampMixin, Base):
    """Configuração de uma integração externa para uma clínica (tenant).

    Os segredos (tokens de API) ficam em `secrets_encrypted` CIFRADOS — ver
    core/crypto.py. Campos não-secretos vão em `public_config`. Uma linha por
    (clinic_id, provider). Escopado por clinic_id (RLS).
    """

    __tablename__ = "clinic_integrations"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Token Fernet de um JSON com os campos secretos. Nullable: pode existir a
    # linha (com public_config) antes de o dono inserir os segredos.
    secrets_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_config: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
