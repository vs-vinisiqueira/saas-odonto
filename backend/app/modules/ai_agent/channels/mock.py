"""Implementação MOCK do canal de WhatsApp (esta fase).

"Envia" gravando num log em memória — permite desenvolver e testar o agente
inteiro sem uma conta Business aprovada na Meta. Substituída por `meta.py`
(Graph API) numa fase futura, mantendo o mesmo contrato.
"""

import logging

from app.modules.ai_agent.channels.base import InboundMessage, WhatsAppChannel

logger = logging.getLogger("ai_agent.channel.mock")


class MockWhatsAppChannel(WhatsAppChannel):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_text(self, to_number: str, text: str) -> None:
        self.sent.append((to_number, text))
        logger.info("MOCK -> %s: %s", to_number, text)

    def parse_webhook(self, payload: dict) -> InboundMessage:
        return InboundMessage(
            tenant_id=payload["tenant_id"],
            from_number=payload["from"],
            text=payload["text"],
            message_id=payload["message_id"],
        )
