"""Testes do GeminiLLMProvider sem rede: mapeamento de tools/mensagens, parsing
de respostas e o fluxo de complete() com o cliente fakeado.
"""

from types import SimpleNamespace

import pytest

from app.modules.ai_agent.llm.base import LLMResponse, ToolCall
from app.modules.ai_agent.llm.gemini import (
    GeminiLLMProvider,
    _parse,
    _to_contents,
    _to_tools,
)
from app.modules.ai_agent.tools import TOOL_SPECS


@pytest.mark.asyncio
async def test_to_tools_mapeia_specs_e_remove_default():
    tools = _to_tools(TOOL_SPECS)
    assert tools is not None
    decls = tools[0].function_declarations
    nomes = {d.name for d in decls}
    assert nomes == {"buscar_horarios", "agendar"}
    agendar = next(d for d in decls if d.name == "agendar")
    # `default` foi removido do schema
    assert agendar.parameters.properties["duration_min"].default is None
    assert agendar.parameters.required == ["starts_at"]


@pytest.mark.asyncio
async def test_to_contents_traduz_user_assistant_tool():
    messages = [
        {"role": "user", "content": "quero horários"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [ToolCall("buscar_horarios", {"date": "2099-01-05"})],
        },
        {"role": "tool", "name": "buscar_horarios", "content": "09:00, 09:30"},
    ]
    contents = _to_contents(messages)
    assert [c.role for c in contents] == ["user", "model", "user"]
    # turno do modelo carrega o functionCall
    assert contents[1].parts[0].function_call.name == "buscar_horarios"
    # resposta da tool vira functionResponse
    fr = contents[2].parts[0].function_response
    assert fr.name == "buscar_horarios"
    assert fr.response == {"result": "09:00, 09:30"}


@pytest.mark.asyncio
async def test_parse_texto_simples():
    resp = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[SimpleNamespace(function_call=None, text="Olá!")]
                )
            )
        ]
    )
    out = _parse(resp)
    assert isinstance(out, LLMResponse)
    assert out.text == "Olá!"
    assert out.tool_calls == []


@pytest.mark.asyncio
async def test_parse_function_call():
    resp = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(
                            function_call=SimpleNamespace(
                                name="agendar", args={"starts_at": "2099-01-05T09:00"}
                            ),
                            text=None,
                        )
                    ]
                )
            )
        ]
    )
    out = _parse(resp)
    assert out.text is None
    assert len(out.tool_calls) == 1
    assert out.tool_calls[0].name == "agendar"
    assert out.tool_calls[0].arguments == {"starts_at": "2099-01-05T09:00"}


@pytest.mark.asyncio
async def test_complete_usa_o_cliente(monkeypatch):
    fake_resp = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[SimpleNamespace(function_call=None, text="Tudo certo!")]
                )
            )
        ]
    )

    class _Models:
        def __init__(self):
            self.called = None

        async def generate_content(self, **kwargs):
            self.called = kwargs
            return fake_resp

    models = _Models()
    provider = GeminiLLMProvider(api_key="dummy", model="gemini-2.0-flash")
    provider._client = SimpleNamespace(aio=SimpleNamespace(models=models))

    out = await provider.complete("sys", [{"role": "user", "content": "oi"}], TOOL_SPECS)
    assert out.text == "Tudo certo!"
    assert models.called["model"] == "gemini-2.0-flash"
    assert models.called["config"].system_instruction == "sys"
