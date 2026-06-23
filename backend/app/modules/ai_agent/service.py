"""Orquestrador do agente de IA.

Recebe uma mensagem (InboundMessage) de um canal, resolve o paciente pelo
telefone, deixa o LLM decidir as ações (tools), executa-as contra os casos de
uso reais (com RLS) e responde pelo mesmo canal. Toda a lógica depende apenas
das interfaces `LLMProvider` e `WhatsAppChannel` — os concretos (mock hoje,
Claude/Meta amanhã) entram por injeção.
"""

import logging

from app.core.tenant import open_tenant_session
from app.modules.ai_agent import tools
from app.modules.ai_agent.channels.base import InboundMessage, WhatsAppChannel
from app.modules.ai_agent.channels.factory import get_whatsapp_channel
from app.modules.ai_agent.llm.base import LLMProvider
from app.modules.ai_agent.llm.factory import get_llm_provider
from app.modules.conversations import service as conversations_service
from app.modules.patients import repository as patients_repo
from app.modules.patients.models import Patient

logger = logging.getLogger("ai_agent.service")

SYSTEM_PROMPT = (
    "Você é a recepcionista virtual de uma clínica odontológica. Seja cordial e "
    "objetiva. Use as ferramentas para consultar horários e marcar consultas. "
    "Nunca invente horários: sempre confira com a ferramenta."
)

MAX_TOOL_ROUNDS = 2


class AgentService:
    def __init__(self, llm: LLMProvider, channel: WhatsAppChannel) -> None:
        self._llm = llm
        self._channel = channel

    async def _ensure_patient(
        self, session, clinic_id: str, telefone: str
    ) -> Patient:
        patient = await patients_repo.get_by_telefone(session, clinic_id, telefone)
        if patient is None:
            patient = Patient(
                clinic_id=clinic_id, nome=f"Contato {telefone}", telefone=telefone
            )
            await patients_repo.add(session, patient)
        return patient

    async def _resolve_providers(
        self, session, clinic_id: str
    ) -> tuple[LLMProvider, WhatsAppChannel]:
        """Usa as credenciais DA CLÍNICA (IA + WhatsApp) quando configuradas;
        senão cai nos provedores injetados (mock nos testes, global em produção)."""
        llm, channel = self._llm, self._channel
        try:
            from app.modules.integrations import service as integrations_service

            ai_creds = await integrations_service.load_credentials(session, clinic_id, "ai")
            if ai_creds:
                llm = get_llm_provider(ai_creds)
            wa_creds = await integrations_service.load_credentials(
                session, clinic_id, "whatsapp"
            )
            if wa_creds:
                channel = get_whatsapp_channel(wa_creds)
        except Exception:
            logger.exception("Falha ao carregar credenciais da clínica; usando padrão")
        return llm, channel

    async def handle(self, inbound: InboundMessage) -> str:
        """Processa uma mensagem e devolve (e envia) a resposta em texto."""
        async with open_tenant_session(inbound.tenant_id) as session:
            llm, channel = await self._resolve_providers(session, inbound.tenant_id)
            patient = await self._ensure_patient(
                session, inbound.tenant_id, inbound.from_number
            )

            messages: list[dict] = [{"role": "user", "content": inbound.text}]
            reply = "Desculpe, não entendi. Pode reformular?"

            for _ in range(MAX_TOOL_ROUNDS):
                resp = await llm.complete(
                    SYSTEM_PROMPT, messages, tools.TOOL_SPECS
                )
                if not resp.tool_calls:
                    reply = resp.text or reply
                    break

                # Preserva as tool calls no histórico (formato agnóstico de provedor):
                # o mock ignora os campos extras; o Gemini precisa deles para o
                # function-calling multi-turn (functionCall <-> functionResponse).
                messages.append(
                    {
                        "role": "assistant",
                        "content": resp.text or "",
                        "tool_calls": resp.tool_calls,
                    }
                )
                for call in resp.tool_calls:
                    result = await tools.execute(
                        session, inbound.tenant_id, patient, call
                    )
                    messages.append(
                        {"role": "tool", "name": call.name, "content": result}
                    )
                    reply = result  # fallback caso o LLM não gere texto final

            # Persiste a troca (mensagem do paciente + resposta da IA) para o
            # painel poder mostrar o que o agente está falando com cada paciente.
            channel_name = getattr(channel, "channel_name", "whatsapp")
            await conversations_service.record_exchange(
                session,
                inbound.tenant_id,
                inbound.from_number,
                channel_name,
                inbound.text,
                reply,
                patient_id=patient.id,
            )

        await channel.send_text(inbound.from_number, reply)
        return reply
