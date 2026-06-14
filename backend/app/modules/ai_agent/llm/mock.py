"""LLM MOCK (esta fase): nenhum provedor concreto ainda.

Simula function-calling de forma determinística para destravar o agente
ponta a ponta sem chave de API. A lógica é proposital e simples: detecta
intenção por palavras-chave + regex de data/hora e devolve um `ToolCall`, ou um
texto de ajuda. Trocável por Claude/OpenAI sem tocar no AgentService — basta
implementar a mesma interface `LLMProvider`.
"""

import re

from app.modules.ai_agent.llm.base import LLMProvider, LLMResponse, ToolCall

_ISO_DATETIME = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_TIME = re.compile(r"\b(\d{2}:\d{2})\b")

_AGENDAR_KWS = ("agendar", "marcar", "confirmar", "quero o", "pode ser")
_HORARIOS_KWS = ("horário", "horario", "horarios", "horários", "disponí", "dispon", "vaga", "agenda", "livre")


class MockLLMProvider(LLMProvider):
    async def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        last = messages[-1] if messages else {"role": "user", "content": ""}

        # 2ª passada: já temos o resultado da tool -> respondemos com ele.
        if last.get("role") == "tool":
            return LLMResponse(text=last.get("content", ""), tool_calls=[])

        text = (last.get("content") or "").lower()

        # Intenção de AGENDAR: precisa de um instante (ISO, ou data + hora).
        if any(k in text for k in _AGENDAR_KWS):
            iso = _ISO_DATETIME.search(text)
            if iso:
                starts_at = iso.group(0).replace(" ", "T")
                return LLMResponse(
                    text=None, tool_calls=[ToolCall("agendar", {"starts_at": starts_at})]
                )
            d, t = _DATE.search(text), _TIME.search(text)
            if d and t:
                return LLMResponse(
                    text=None,
                    tool_calls=[
                        ToolCall("agendar", {"starts_at": f"{d.group(0)}T{t.group(1)}"})
                    ],
                )

        # Intenção de BUSCAR HORÁRIOS.
        if any(k in text for k in _HORARIOS_KWS):
            d = _DATE.search(text)
            args = {"date": d.group(0)} if d else {}
            return LLMResponse(text=None, tool_calls=[ToolCall("buscar_horarios", args)])

        return LLMResponse(
            text=(
                "Olá! Posso te ajudar a ver horários livres e marcar sua consulta. "
                "Ex.: \"quais horários tem dia 2099-01-05?\" ou "
                "\"quero agendar 2099-01-05 10:00\"."
            ),
            tool_calls=[],
        )
