"""Casos de uso de conversas: listagem para o inbox, leitura da thread,
resposta manual (humano no loop) e persistência das trocas do agente."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_agent.channels.base import WhatsAppChannel
from app.modules.conversations import repository
from app.modules.conversations.models import (
    DIRECTION_INBOUND,
    DIRECTION_OUTBOUND,
    SENDER_AI,
    SENDER_HUMAN,
    SENDER_PATIENT,
    Conversation,
    Message,
)
from app.modules.conversations.schemas import ConversationOut
from app.modules.patients import repository as patients_repo
from app.shared.exceptions import NotFound


async def record_exchange(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    external_number: str,
    channel: str,
    inbound_text: str,
    reply_text: str,
    patient_id: uuid.UUID | str | None = None,
) -> Conversation:
    """Grava a mensagem do paciente e a resposta da IA numa conversa.

    Chamado pelo `AgentService` após gerar a resposta. Idempotência de conversa
    via (clinic_id, external_number).
    """
    conv = await repository.get_or_create(
        session, clinic_id, external_number, channel, patient_id
    )
    await repository.add_message(
        session, clinic_id, conv, DIRECTION_INBOUND, SENDER_PATIENT, inbound_text
    )
    await repository.add_message(
        session, clinic_id, conv, DIRECTION_OUTBOUND, SENDER_AI, reply_text
    )
    return conv


async def list_conversations(
    session: AsyncSession, clinic_id: uuid.UUID | str, q: str | None = None
) -> list[ConversationOut]:
    convs = await repository.list_all(session, clinic_id)
    if not convs:
        return []

    latest = await repository.latest_messages(
        session, clinic_id, [c.id for c in convs]
    )
    patients = {p.id: p.nome for p in await patients_repo.list_all(session, clinic_id)}

    out: list[ConversationOut] = []
    for c in convs:
        msg = latest.get(c.id)
        patient_nome = patients.get(c.patient_id) if c.patient_id else None
        if q:
            needle = q.strip().lower()
            haystack = f"{patient_nome or ''} {c.external_number}".lower()
            if needle not in haystack:
                continue
        out.append(
            ConversationOut(
                id=c.id,
                patient_id=c.patient_id,
                patient_nome=patient_nome,
                external_number=c.external_number,
                channel=c.channel,
                ai_enabled=c.ai_enabled,
                last_message_at=c.last_message_at,
                last_message_preview=msg.text if msg else None,
                last_message_sender=msg.sender if msg else None,
                # Não lida: última mensagem é do paciente e a clínica ainda não respondeu.
                unread=msg is not None and msg.sender == SENDER_PATIENT,
            )
        )
    return out


async def _get_or_404(
    session: AsyncSession, clinic_id: uuid.UUID | str, conversation_id: uuid.UUID | str
) -> Conversation:
    conv = await repository.get_by_id(session, clinic_id, conversation_id)
    if conv is None:
        raise NotFound("Conversa não encontrada")
    return conv


async def get_messages(
    session: AsyncSession, clinic_id: uuid.UUID | str, conversation_id: uuid.UUID | str
) -> list[Message]:
    await _get_or_404(session, clinic_id, conversation_id)
    return await repository.list_messages(session, clinic_id, conversation_id)


async def send_manual(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    conversation_id: uuid.UUID | str,
    text: str,
    channel: WhatsAppChannel,
) -> Message:
    """Resposta manual de um atendente: grava como `human` e envia pelo canal.

    Em dev (canal mock) o envio só registra em memória — sem erro.
    """
    conv = await _get_or_404(session, clinic_id, conversation_id)
    msg = await repository.add_message(
        session, clinic_id, conv, DIRECTION_OUTBOUND, SENDER_HUMAN, text
    )
    await channel.send_text(conv.external_number, text)
    return msg


async def update_conversation(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    conversation_id: uuid.UUID | str,
    ai_enabled: bool | None,
) -> Conversation:
    conv = await _get_or_404(session, clinic_id, conversation_id)
    if ai_enabled is not None:
        conv.ai_enabled = ai_enabled
    await session.flush()
    return conv
