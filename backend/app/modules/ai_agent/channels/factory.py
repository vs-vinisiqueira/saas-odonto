"""Seleção do canal de mensagens.

Prioridade: credenciais DA CLÍNICA (passadas em `creds`) > credenciais globais
(env, compat) > mock. O mock garante que CI/dev nunca quebrem por falta de
credencial.
"""

from app.core.config import settings
from app.modules.ai_agent.channels.base import WhatsAppChannel
from app.modules.ai_agent.channels.mock import MockWhatsAppChannel


def get_whatsapp_channel(creds: dict | None = None) -> WhatsAppChannel:
    # 1) Credenciais da clínica (modelo multi-tenant).
    if creds and creds.get("access_token") and creds.get("phone_number_id"):
        from app.modules.ai_agent.channels.meta import MetaWhatsAppChannel

        return MetaWhatsAppChannel(
            token=creds["access_token"],
            phone_number_id=creds["phone_number_id"],
            api_version=creds.get("api_version") or settings.whatsapp_api_version,
        )

    # 2) Credenciais globais (compatibilidade com o deploy atual via env).
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
