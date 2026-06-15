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
    """Contrato mínimo que o AgentService usa: apenas ENVIAR.

    O PARSE do webhook é específico de cada provedor (formato do payload, e — no
    caso da Meta — resolução assíncrona do tenant pelo phone_number_id), então
    fica fora do contrato: cada adapter expõe seus próprios helpers de entrada.
    """

    @abstractmethod
    async def send_text(self, to_number: str, text: str) -> None: ...
