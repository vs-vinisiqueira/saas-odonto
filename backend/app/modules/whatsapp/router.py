"""Webhook do WhatsApp (Meta Cloud API) + registro de números por clínica.

- GET  /ai/whatsapp/webhook  -> verificação do webhook (eco do challenge).
- POST /ai/whatsapp/webhook  -> recebe mensagens; resolve o tenant pelo
  phone_number_id e processa em BACKGROUND (responde 200 na hora, como a Meta
  exige). O AgentService responde pelo próprio canal (Graph API).
- POST/GET /ai/whatsapp/numbers -> a clínica registra/lista seu phone_number_id.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.tenant import get_tenant_session
from app.modules.ai_agent.channels.base import InboundMessage
from app.modules.ai_agent.channels.factory import get_whatsapp_channel
from app.modules.ai_agent.channels.meta import MetaWhatsAppChannel
from app.modules.ai_agent.llm.factory import get_llm_provider
from app.modules.ai_agent.service import AgentService
from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.whatsapp import repository
from app.modules.whatsapp.schemas import WhatsAppNumberCreate, WhatsAppNumberOut
from app.shared.exceptions import Conflict

logger = logging.getLogger("whatsapp.router")

router = APIRouter(prefix="/ai/whatsapp", tags=["whatsapp"])

# Agente com o canal configurado (meta quando há credenciais; senão mock).
_agent = AgentService(llm=get_llm_provider(), channel=get_whatsapp_channel())


@router.get("/webhook")
async def verify_webhook(
    mode: str | None = Query(default=None, alias="hub.mode"),
    token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    """Verificação do webhook pela Meta: ecoa o challenge se o token bater."""
    result = MetaWhatsAppChannel.verify_challenge(
        mode, token, challenge, settings.whatsapp_verify_token
    )
    if result is None:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return PlainTextResponse(result)


@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """Recebe eventos da Meta. Responde 200 imediatamente; processa em background."""
    payload = await request.json()
    for msg in MetaWhatsAppChannel.parse_messages(payload):
        clinic_id = await repository.resolve_clinic_for_number(msg.phone_number_id)
        if clinic_id is None:
            logger.warning("phone_number_id sem clínica: %s", msg.phone_number_id)
            continue
        inbound = InboundMessage(
            tenant_id=clinic_id,
            from_number=msg.from_number,
            text=msg.text,
            message_id=msg.message_id,
        )
        background_tasks.add_task(_agent.handle, inbound)
    return {"status": "received"}


@router.post(
    "/numbers", response_model=WhatsAppNumberOut, status_code=status.HTTP_201_CREATED
)
async def register_number(
    body: WhatsAppNumberCreate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    try:
        return await repository.get_or_create(
            session, user.clinic_id, body.phone_number_id, body.label
        )
    except IntegrityError:
        raise Conflict("Esse phone_number_id já está registrado em outra clínica.")


@router.get("/numbers", response_model=list[WhatsAppNumberOut])
async def list_numbers(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await repository.list_for_clinic(session, user.clinic_id)
