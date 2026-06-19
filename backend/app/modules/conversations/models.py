"""Persistência das conversas do agente de IA com os pacientes.

Hoje o `AgentService` respondia e descartava o histórico. Estes modelos guardam
cada troca (paciente -> IA -> humano) para que o painel mostre o que o Gemini
está falando com cada paciente. Tudo escopado por `clinic_id` (RLS), igual aos
demais módulos.
"""

import datetime as dt
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models import TimestampMixin, UUIDPKMixin

# Direção da mensagem (do ponto de vista da clínica).
DIRECTION_INBOUND = "inbound"  # paciente -> clínica
DIRECTION_OUTBOUND = "outbound"  # clínica -> paciente

# Quem produziu a mensagem.
SENDER_PATIENT = "patient"
SENDER_AI = "ai"  # resposta gerada pelo Gemini/agente
SENDER_HUMAN = "human"  # resposta manual de um atendente pelo painel


class Conversation(UUIDPKMixin, TimestampMixin, Base):
    """Uma thread de mensagens com um número de WhatsApp (um paciente).

    Identificada pelo par (clinic_id, external_number). `ai_enabled` permite, no
    futuro, pausar o agente numa conversa específica (atendimento humano).
    """

    __tablename__ = "conversations"
    __table_args__ = (
        Index("uq_conversations_clinic_number", "clinic_id", "external_number", unique=True),
    )

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
        index=True,
    )
    # Canal de origem: "whatsapp" (Meta) ou "mock" (dev).
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="whatsapp")
    # Número de quem está do outro lado (telefone do paciente).
    external_number: Mapped[str] = mapped_column(String(32), nullable=False)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_message_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(UUIDPKMixin, TimestampMixin, Base):
    """Uma mensagem dentro de uma conversa."""

    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    sender: Mapped[str] = mapped_column(String(16), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
