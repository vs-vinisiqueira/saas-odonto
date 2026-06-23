"""Seleção do provedor de LLM.

Prioridade: credenciais DA CLÍNICA (`creds`) > credenciais globais (env, compat)
> mock. O mock (sem chave, offline) garante que CI/dev nunca quebrem.
"""

from app.core.config import settings
from app.modules.ai_agent.llm.base import LLMProvider
from app.modules.ai_agent.llm.mock import MockLLMProvider


def get_llm_provider(creds: dict | None = None) -> LLMProvider:
    # 1) Credenciais da clínica (modelo multi-tenant).
    if creds and creds.get("api_key"):
        from app.modules.ai_agent.llm.gemini import GeminiLLMProvider

        return GeminiLLMProvider(
            api_key=creds["api_key"], model=creds.get("model") or settings.gemini_model
        )

    # 2) Credenciais globais (compatibilidade com o deploy atual via env).
    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        from app.modules.ai_agent.llm.gemini import GeminiLLMProvider

        return GeminiLLMProvider(
            api_key=settings.gemini_api_key, model=settings.gemini_model
        )

    return MockLLMProvider()
