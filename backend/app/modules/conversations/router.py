"""Inbox de conversas do agente de IA (painel da clínica).

- GET   /conversations                      -> lista (inbox) com prévia.
- GET   /conversations/{id}/messages         -> thread em ordem cronológica.
- POST  /conversations/{id}/messages         -> resposta manual (humano no loop).
- PATCH /conversations/{id}                  -> pausa/ativa a IA na conversa.

Tudo escopado por tenant via `get_tenant_session` (RLS), igual aos demais módulos.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_tenant_session
from app.modules.ai_agent.channels.factory import get_whatsapp_channel
from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.conversations import service
from app.modules.conversations.schemas import (
    ConversationOut,
    ConversationUpdate,
    ManualMessageIn,
    MessageOut,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])

# Canal para envio das respostas manuais (meta quando há credenciais; senão mock).
_channel = get_whatsapp_channel()


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.list_conversations(session, user.clinic_id)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.get_messages(session, user.clinic_id, conversation_id)


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: uuid.UUID,
    body: ManualMessageIn,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.send_manual(
        session, user.clinic_id, conversation_id, body.text, _channel
    )


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def update_conversation(
    conversation_id: uuid.UUID,
    body: ConversationUpdate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    await service.update_conversation(
        session, user.clinic_id, conversation_id, body.ai_enabled
    )
    # Reusa a montagem da listagem para devolver o item já com prévia/paciente.
    convs = await service.list_conversations(session, user.clinic_id)
    return next(c for c in convs if c.id == conversation_id)
