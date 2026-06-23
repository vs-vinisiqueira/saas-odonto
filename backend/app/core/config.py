from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_WEAK_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    """Configurações da aplicação, carregadas de variáveis de ambiente / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SaaS Odonto"
    environment: str = "development"

    # Conexão da aplicação (role app_user, sujeito a RLS).
    database_url: str
    # Conexão admin (superusuário) usada por migrations e seed. Opcional em runtime.
    admin_database_url: str | None = None

    # JWT
    jwt_secret: str = _WEAK_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Chave para cifrar segredos de integrações por clínica (tokens de API) no
    # banco. Recomendado: aleatória, ≥ 32 chars, FIXA (se mudar, os segredos já
    # gravados ficam ilegíveis e precisam ser reconfigurados). Se ausente, cai no
    # JWT_SECRET — funciona, mas o ideal é uma secret dedicada. Ver core/crypto.py.
    credentials_secret: str | None = None

    # CORS: lista separada por vírgula. Em produção, inclua só os domínios reais.
    allowed_origins: str = "http://localhost:5173"

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_strong(cls, v: str, info) -> str:
        # Bloqueia a secret fraca em produção. Em dev, apenas avisa.
        env = info.data.get("environment", "development")
        if v == _WEAK_SECRET and env == "production":
            raise ValueError(
                "JWT_SECRET não pode ser o valor padrão em produção. "
                "Defina uma string aleatória ≥ 32 caracteres."
            )
        return v

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    # Agente de IA (LLM). "mock" (default) usa intenção por regex, sem chave.
    # "gemini" usa o Google Gemini (precisa de GEMINI_API_KEY).
    llm_provider: str = "mock"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    # Canal de mensagens. "mock" (default) ou "meta" (WhatsApp Cloud API).
    channel_provider: str = "mock"
    whatsapp_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_verify_token: str | None = None
    whatsapp_api_version: str = "v21.0"

    # Gateway de pagamento. "mock" (default) ou "mercadopago".
    billing_provider: str = "mock"
    mercadopago_access_token: str | None = None
    # E-mail do pagador exigido pelo Pix (use um de teste no sandbox).
    mercadopago_payer_email: str = "test_user@testuser.com"

    # Calendário externo. "null" (default, no-op) ou "google" (Service Account).
    calendar_provider: str = "null"
    google_calendar_id: str = "primary"
    # Conteúdo JSON do arquivo credentials.json da Service Account (string única).
    google_sa_credentials_json: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
