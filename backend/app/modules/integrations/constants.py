"""Registro das integrações suportadas e seus campos.

Cada provedor declara:
- `secret`: campos sensíveis (cifrados, nunca devolvidos em claro pela API).
- `public`: campos não-secretos (modelo, calendar_id, etc.) guardados em claro.
- `required`: campos mínimos (secret + public) para considerar a integração
  "configurada" e utilizável em runtime.
- `label`: nome amigável exibido no painel.

Manter este registro como única fonte da verdade: o service usa estas listas
para validar entrada (ignora chaves desconhecidas), mascarar segredos e decidir
se a integração está pronta para uso.
"""

WHATSAPP = "whatsapp"
MERCADOPAGO = "mercadopago"
GOOGLE_CALENDAR = "google_calendar"
AI = "ai"

PROVIDERS = [WHATSAPP, MERCADOPAGO, GOOGLE_CALENDAR, AI]

PROVIDER_FIELDS: dict[str, dict] = {
    WHATSAPP: {
        "label": "WhatsApp (Meta)",
        "secret": ["access_token"],
        "public": ["phone_number_id", "api_version"],
        "required": ["access_token", "phone_number_id"],
    },
    MERCADOPAGO: {
        "label": "Mercado Pago",
        "secret": ["access_token"],
        "public": ["payer_email"],
        "required": ["access_token"],
    },
    GOOGLE_CALENDAR: {
        "label": "Google Calendar",
        "secret": ["sa_credentials_json"],
        "public": ["calendar_id"],
        "required": ["sa_credentials_json"],
    },
    AI: {
        "label": "Assistente de IA (Gemini)",
        "secret": ["api_key"],
        "public": ["model"],
        "required": ["api_key"],
    },
}


def is_valid_provider(provider: str) -> bool:
    return provider in PROVIDER_FIELDS


def secret_fields(provider: str) -> list[str]:
    return PROVIDER_FIELDS[provider]["secret"]


def public_fields(provider: str) -> list[str]:
    return PROVIDER_FIELDS[provider]["public"]


def required_fields(provider: str) -> list[str]:
    return PROVIDER_FIELDS[provider]["required"]


def label(provider: str) -> str:
    return PROVIDER_FIELDS[provider]["label"]
