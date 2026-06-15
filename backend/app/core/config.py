from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Agente de IA (LLM). "mock" (default) usa intenção por regex, sem chave.
    # "gemini" usa o Google Gemini (precisa de GEMINI_API_KEY).
    llm_provider: str = "mock"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
