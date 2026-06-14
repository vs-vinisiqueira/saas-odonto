"""Contrato do provedor de LLM (adapter plugável).

Decisão do usuário: abstrair o LLM atrás desta interface. Começamos sem
implementação concreta; depois plugamos Claude / OpenAI / etc. sem mexer no
AgentService. As `tools` são funções tipadas expostas ao modelo (function
calling); o LLM apenas PEDE ações via tool_call — quem executa são os casos de
uso (ex.: SchedulingService), com validação e RLS.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str | None
    tool_calls: list[ToolCall]


class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse: ...
