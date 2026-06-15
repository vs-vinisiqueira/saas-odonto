"""Provedor de LLM real: Google Gemini (function calling manual).

Implementa a mesma interface `LLMProvider` do mock. O Gemini decide quando chamar
as tools (`buscar_horarios`/`agendar`); a EXECUÇÃO continua no `tools.execute`,
dentro da sessão escopada ao tenant (RLS) — por isso desligamos o automatic
function calling do SDK.

As funções de mapeamento (`_to_tools`, `_to_contents`, `_parse`) são puras e
testáveis sem rede.
"""

from __future__ import annotations

import logging
from typing import Any

from google import genai
from google.genai import types

from app.modules.ai_agent.llm.base import LLMProvider, LLMResponse, ToolCall

logger = logging.getLogger("ai_agent.llm.gemini")

_FALLBACK = "Desculpe, tive um problema técnico agora. Pode tentar de novo em instantes?"


def _sanitize_params(params: dict | None) -> dict | None:
    """Mantém só o que o Gemini aceita no schema (remove `default` etc.)."""
    if not params:
        return None
    props = {
        name: {k: v for k, v in prop.items() if k != "default"}
        for name, prop in (params.get("properties") or {}).items()
    }
    out: dict[str, Any] = {"type": params.get("type", "object"), "properties": props}
    if params.get("required"):
        out["required"] = params["required"]
    return out


def _to_tools(specs: list[dict] | None) -> list[types.Tool] | None:
    if not specs:
        return None
    decls = [
        types.FunctionDeclaration(
            name=s["name"],
            description=s.get("description"),
            parameters=_sanitize_params(s.get("parameters")),
        )
        for s in specs
    ]
    return [types.Tool(function_declarations=decls)]


def _to_contents(messages: list[dict]) -> list[types.Content]:
    """Converte o histórico interno (user/assistant/tool) para o formato Gemini."""
    contents: list[types.Content] = []
    for m in messages:
        role = m.get("role")
        if role == "user":
            contents.append(
                types.Content(
                    role="user", parts=[types.Part.from_text(text=m.get("content") or "")]
                )
            )
        elif role == "assistant":
            tool_calls = m.get("tool_calls")
            if tool_calls:
                parts = [
                    types.Part.from_function_call(name=tc.name, args=tc.arguments or {})
                    for tc in tool_calls
                ]
            else:
                parts = [types.Part.from_text(text=m.get("content") or "")]
            contents.append(types.Content(role="model", parts=parts))
        elif role == "tool":
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=m.get("name") or "tool",
                            response={"result": m.get("content")},
                        )
                    ],
                )
            )
    return contents


def _parse(response: Any) -> LLMResponse:
    """Extrai texto e/ou tool calls de uma resposta do Gemini."""
    texts: list[str] = []
    tool_calls: list[ToolCall] = []
    candidates = getattr(response, "candidates", None) or []
    if candidates:
        content = getattr(candidates[0], "content", None)
        for part in getattr(content, "parts", None) or []:
            fc = getattr(part, "function_call", None)
            if fc is not None:
                tool_calls.append(ToolCall(name=fc.name, arguments=dict(fc.args or {})))
            elif getattr(part, "text", None):
                texts.append(part.text)
    return LLMResponse(text="\n".join(texts) if texts else None, tool_calls=tool_calls)


class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=_to_contents(messages),
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=_to_tools(tools),
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                    temperature=0,
                ),
            )
        except Exception:
            logger.exception("Falha ao chamar o Gemini")
            return LLMResponse(text=_FALLBACK, tool_calls=[])
        return _parse(response)
