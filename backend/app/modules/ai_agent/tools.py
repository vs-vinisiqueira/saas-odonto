"""Tools expostas ao LLM + executor.

O LLM apenas PEDE ações (tool_call). Quem executa é este módulo, chamando os
casos de uso reais (`scheduling.service`) dentro de uma sessão já escopada ao
tenant (RLS). Cada tool devolve uma string pronta para o paciente.
"""

import datetime as dt

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_agent.llm.base import ToolCall
from app.modules.patients.models import Patient
from app.modules.scheduling import service as scheduling
from app.modules.scheduling.schemas import AppointmentCreate
from app.shared.exceptions import Conflict, NotFound

UTC = dt.timezone.utc

# Specs no formato de function-calling (entregues ao LLMProvider.complete).
TOOL_SPECS: list[dict] = [
    {
        "name": "buscar_horarios",
        "description": "Lista os horários livres da clínica em um dia.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Dia no formato YYYY-MM-DD. Se omitido, usa amanhã.",
                }
            },
        },
    },
    {
        "name": "agendar",
        "description": "Marca uma consulta para o paciente em um horário.",
        "parameters": {
            "type": "object",
            "properties": {
                "starts_at": {
                    "type": "string",
                    "description": "Início no formato YYYY-MM-DDTHH:MM.",
                },
                "duration_min": {"type": "integer", "default": 30},
            },
            "required": ["starts_at"],
        },
    },
]


def _fmt_hm(value: dt.datetime) -> str:
    return value.astimezone(UTC).strftime("%H:%M")


async def _buscar_horarios(session, clinic_id, patient, args) -> str:
    raw = args.get("date")
    if raw:
        day = dt.date.fromisoformat(raw)
    else:
        day = (dt.datetime.now(UTC) + dt.timedelta(days=1)).date()

    slots = await scheduling.buscar_horarios(session, clinic_id, day)
    if not slots:
        return f"Não encontrei horários livres em {day.isoformat()}. Quer tentar outro dia?"

    horas = [_fmt_hm(s["starts_at"]) for s in slots]
    mostrados = ", ".join(horas[:8])
    extra = f" (e mais {len(horas) - 8})" if len(horas) > 8 else ""
    return (
        f"Horários livres em {day.isoformat()}: {mostrados}{extra}. "
        "Qual prefere? É só dizer, por ex.: \"agendar "
        f"{day.isoformat()} {horas[0]}\"."
    )


async def _agendar(session, clinic_id, patient: Patient, args) -> str:
    starts_at = dt.datetime.fromisoformat(args["starts_at"])
    if starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=UTC)
    data = AppointmentCreate(
        patient_id=patient.id,
        starts_at=starts_at,
        duration_min=int(args.get("duration_min", 30)),
    )
    try:
        appt = await scheduling.agendar(session, clinic_id, data)
    except Conflict:
        return (
            "Esse horário acabou de ficar indisponível. "
            "Posso te mostrar outras opções no mesmo dia?"
        )
    except NotFound as e:
        return f"Não consegui concluir: {e.detail}"

    quando = appt.starts_at.astimezone(UTC)
    return (
        f"Pronto, {patient.nome}! Sua consulta está marcada para "
        f"{quando.strftime('%d/%m/%Y às %H:%M')}. Até lá! 🦷"
    )


_DISPATCH = {
    "buscar_horarios": _buscar_horarios,
    "agendar": _agendar,
}


async def execute(
    session: AsyncSession,
    clinic_id: str,
    patient: Patient,
    call: ToolCall,
) -> str:
    handler = _DISPATCH.get(call.name)
    if handler is None:
        return "Desculpe, não consegui processar esse pedido."
    return await handler(session, clinic_id, patient, call.arguments)
