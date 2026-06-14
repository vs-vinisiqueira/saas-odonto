"""Contrato de canal de mensagens (o pulo do gato do mock-first).

O AgentService dependerá de WhatsAppChannel, nunca da Meta diretamente. Hoje
rodamos com `mock`; amanhã trocamos por `meta` (Graph API) sem tocar na lógica
de negócio — apenas a injeção de dependência muda.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class InboundMessage:
    tenant_id: str
    from_number: str
    text: str
    message_id: str


class WhatsAppChannel(ABC):
    @abstractmethod
    async def send_text(self, to_number: str, text: str) -> None: ...

    @abstractmethod
    def parse_webhook(self, payload: dict) -> InboundMessage: ...
