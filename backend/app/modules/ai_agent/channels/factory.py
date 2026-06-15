"""Seleção do canal de mensagens conforme a config.

Default = mock. "meta" só é usado se houver token + phone_number_id; caso
contrário cai no mock — assim CI/dev nunca quebram por falta de credencial.
"""

from app.core.config import settings
from app.modules.ai_agent.channels.base import WhatsAppChannel
from app.modules.ai_agent.channels.mock import MockWhatsAppChannel


def get_whatsapp_channel() -> WhatsAppChannel:
    if (
        settings.channel_provider == "meta"
        and settings.whatsapp_token
        and settings.whatsapp_phone_number_id
    ):
        from app.modules.ai_agent.channels.meta import MetaWhatsAppChannel

        return MetaWhatsAppChannel(
            token=settings.whatsapp_token,
            phone_number_id=settings.whatsapp_phone_number_id,
            api_version=settings.whatsapp_api_version,
        )
    return MockWhatsAppChannel()
