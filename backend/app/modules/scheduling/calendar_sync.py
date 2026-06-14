"""Port de sincronização one-way com o Google Calendar.

A agenda interna (tabela `appointments`) é a fonte da verdade; este port empurra
as mudanças para um calendário externo. Mantemos só a interface + uma
implementação no-op (mock-first), no mesmo espírito do `billing/gateway.py`:
o provedor concreto (Google Calendar API) entra numa fase posterior.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.modules.scheduling.models import Appointment


@runtime_checkable
class CalendarSync(Protocol):
    async def upsert_event(self, appointment: Appointment) -> None:
        """Cria/atualiza o evento correspondente ao agendamento."""
        ...

    async def delete_event(self, appointment: Appointment) -> None:
        """Remove o evento (ex.: cancelamento)."""
        ...


class NullCalendarSync:
    """No-op: não há provedor configurado ainda. Não falha o fluxo da agenda."""

    async def upsert_event(self, appointment: Appointment) -> None:
        return None

    async def delete_event(self, appointment: Appointment) -> None:
        return None


# Instância padrão usada pelo service. Trocar por um adapter real (ex.:
# GoogleCalendarSync) quando a integração for implementada.
default_calendar_sync: CalendarSync = NullCalendarSync()
