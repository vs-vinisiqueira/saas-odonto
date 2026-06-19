"""Acesso a dados de conversas/mensagens. RLS já isola por tenant; ainda assim
filtramos por clinic_id explicitamente (defesa em profundidade)."""

import datetime as dt
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.conversations.models import Conversation, Message


async def get_by_number(
    session: AsyncSession, clinic_id: uuid.UUID | str, external_number: str
) -> Conversation | None:
    result = await session.execute(
        select(Conversation).where(
            Conversation.clinic_id == clinic_id,
            Conversation.external_number == external_number,
        )
    )
    return result.scalar_one_or_none()


async def get_or_create(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    external_number: str,
    channel: str,
    patient_id: uuid.UUID | str | None = None,
) -> Conversation:
    conv = await get_by_number(session, clinic_id, external_number)
    if conv is None:
        conv = Conversation(
            clinic_id=clinic_id,
            external_number=external_number,
            channel=channel,
            patient_id=patient_id,
        )
        session.add(conv)
        await session.flush()
    elif patient_id is not None and conv.patient_id is None:
        conv.patient_id = patient_id
    return conv


async def get_by_id(
    session: AsyncSession, clinic_id: uuid.UUID | str, conversation_id: uuid.UUID | str
) -> Conversation | None:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.clinic_id == clinic_id,
        )
    )
    return result.scalar_one_or_none()


async def list_all(
    session: AsyncSession, clinic_id: uuid.UUID | str
) -> list[Conversation]:
    """Conversas do tenant, mais recentes primeiro (sem last_message_at por último)."""
    result = await session.execute(
        select(Conversation)
        .where(Conversation.clinic_id == clinic_id)
        .order_by(
            Conversation.last_message_at.desc().nullslast(),
            Conversation.created_at.desc(),
        )
    )
    return list(result.scalars().all())


async def add_message(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    conversation: Conversation,
    direction: str,
    sender: str,
    text: str,
    when: dt.datetime | None = None,
) -> Message:
    msg = Message(
        clinic_id=clinic_id,
        conversation_id=conversation.id,
        direction=direction,
        sender=sender,
        text=text,
    )
    session.add(msg)
    conversation.last_message_at = when or dt.datetime.now(dt.timezone.utc)
    await session.flush()
    return msg


async def list_messages(
    session: AsyncSession, clinic_id: uuid.UUID | str, conversation_id: uuid.UUID | str
) -> list[Message]:
    result = await session.execute(
        select(Message)
        .where(
            Message.clinic_id == clinic_id,
            Message.conversation_id == conversation_id,
        )
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())


async def latest_messages(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    conversation_ids: list[uuid.UUID],
) -> dict[uuid.UUID, Message]:
    """Última mensagem de cada conversa (para a prévia na lista do inbox)."""
    if not conversation_ids:
        return {}
    latest_at = (
        select(
            Message.conversation_id.label("cid"),
            func.max(Message.created_at).label("max_at"),
        )
        .where(
            Message.clinic_id == clinic_id,
            Message.conversation_id.in_(conversation_ids),
        )
        .group_by(Message.conversation_id)
        .subquery()
    )
    stmt = select(Message).join(
        latest_at,
        (Message.conversation_id == latest_at.c.cid)
        & (Message.created_at == latest_at.c.max_at),
    )
    result = await session.execute(stmt)
    out: dict[uuid.UUID, Message] = {}
    for msg in result.scalars().all():
        out[msg.conversation_id] = msg
    return out
