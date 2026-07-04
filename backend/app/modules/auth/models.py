import datetime as dt
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models import TimestampMixin, UUIDPKMixin

# Papéis do RBAC
ROLE_OWNER = "owner"
ROLE_DENTIST = "dentist"
ROLE_SECRETARY = "secretary"
ROLES = {ROLE_OWNER, ROLE_DENTIST, ROLE_SECRETARY}


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"
    # E-mail único globalmente: permite o login localizar o usuário (e seu tenant)
    # antes de existir um token / contexto de clínica.
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    # Perfil (preenchido pela tela de Configurações > Usuários).
    nome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(32), nullable=True)


class RefreshToken(Base):
    """Registro de um refresh token emitido (identificado pelo claim `jti`).

    Sem RLS: o refresh é pré-tenant (ver migration 0013). Permite rotação,
    revogação (logout/reset de senha) e detecção de reuso.
    """

    __tablename__ = "refresh_tokens"

    jti: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
