"""Seleção do provedor de LLM conforme a config.

Default = mock (sem chave, offline). "gemini" só é usado se houver
`GEMINI_API_KEY`; caso contrário cai no mock — assim CI/dev nunca quebram por
falta de chave.
"""

from app.core.config import settings
from app.modules.ai_agent.llm.base import LLMProvider
from app.modules.ai_agent.llm.mock import MockLLMProvider


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        # Import tardio: só carrega o SDK do Gemini quando realmente usado.
        from app.modules.ai_agent.llm.gemini import GeminiLLMProvider

        return GeminiLLMProvider(
            api_key=settings.gemini_api_key, model=settings.gemini_model
        )
    return MockLLMProvider()
