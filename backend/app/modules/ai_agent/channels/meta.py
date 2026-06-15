"""Canal real de WhatsApp: Meta Cloud API (Graph API).

`send_text` envia pela Graph API; `parse_messages` extrai as mensagens de texto
do payload do webhook (ignora eventos de status). A resolução do tenant
(phone_number_id -> clinic_id) NÃO acontece aqui — é assíncrona (banco) e fica no
router, via `whatsapp.repository.resolve_clinic_for_number`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.modules.ai_agent.channels.base import WhatsAppChannel

logger = logging.getLogger("ai_agent.channel.meta")


@dataclass
class ParsedMessage:
    from_number: str
    text: str
    message_id: str
    phone_number_id: str


class MetaWhatsAppChannel(WhatsAppChannel):
    def __init__(
        self, token: str, phone_number_id: str, api_version: str = "v21.0"
    ) -> None:
        self._token = token
        self._phone_number_id = phone_number_id
        self._base = f"https://graph.facebook.com/{api_version}"

    async def send_text(self, to_number: str, text: str) -> None:
        url = f"{self._base}/{self._phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": text},
        }
        headers = {"Authorization": f"Bearer {self._token}"}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            logger.error("Falha ao enviar WhatsApp (%s): %s", resp.status_code, resp.text)

    @staticmethod
    def parse_messages(payload: dict) -> list[ParsedMessage]:
        """Extrai as mensagens de TEXTO recebidas. Ignora status e não-texto."""
        out: list[ParsedMessage] = []
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                phone_number_id = value.get("metadata", {}).get("phone_number_id", "")
                for msg in value.get("messages", []):
                    if msg.get("type") != "text":
                        continue
                    out.append(
                        ParsedMessage(
                            from_number=msg.get("from", ""),
                            text=msg.get("text", {}).get("body", ""),
                            message_id=msg.get("id", ""),
                            phone_number_id=phone_number_id,
                        )
                    )
        return out

    @staticmethod
    def verify_challenge(
        mode: str | None, token: str | None, challenge: str | None, expected: str | None
    ) -> str | None:
        """Retorna o challenge (a ecoar) se a verificação do webhook bater."""
        if mode == "subscribe" and expected and token == expected:
            return challenge
        return None
