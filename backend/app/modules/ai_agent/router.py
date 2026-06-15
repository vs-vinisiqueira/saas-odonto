"""Webhook do canal de mensagens (mock) -> agente de IA.

Hoje o canal é o `MockWhatsAppChannel` e o `tenant_id` (clinic_id) vem direto no
payload. Numa fase futura, o adapter `meta.py` (Graph API) valida a assinatura
e mapeia o phone-number-id da Meta para a clínica — sem mudar o AgentService.
"""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.modules.ai_agent.channels.mock import MockWhatsAppChannel
from app.modules.ai_agent.llm.factory import get_llm_provider
from app.modules.ai_agent.service import AgentService

router = APIRouter(prefix="/ai", tags=["ai_agent"])

# Canal mock-first; o LLM é escolhido por config (mock por padrão, Gemini se
# houver GEMINI_API_KEY). Ambos trocáveis por adapters reais sem mexer no agente.
channel = MockWhatsAppChannel()
agent = AgentService(llm=get_llm_provider(), channel=channel)


class MockWebhookPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(description="clinic_id da clínica (tenant)")
    from_: str = Field(alias="from", description="Número de quem enviou")
    text: str
    message_id: str


class WebhookReply(BaseModel):
    reply: str


@router.post("/webhook", response_model=WebhookReply)
async def webhook(payload: MockWebhookPayload):
    inbound = channel.parse_webhook(payload.model_dump(by_alias=True))
    reply = await agent.handle(inbound)
    return WebhookReply(reply=reply)
