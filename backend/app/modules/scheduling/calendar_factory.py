"""Seleção do adapter de calendário.

Prioridade: credenciais DA CLÍNICA (`creds`) > credenciais globais (env, compat)
> NullCalendarSync (no-op). O null garante que CI/dev não precisem do Google.

As credenciais da clínica trazem `sa_credentials_json` (o conteúdo do
credentials.json da Service Account) e, opcionalmente, `calendar_id`.
"""

import json
import logging

from app.core.config import settings
from app.modules.scheduling.calendar_sync import CalendarSync, NullCalendarSync

logger = logging.getLogger("scheduling.calendar_factory")

_null = NullCalendarSync()


def _build_google(sa_json: str, calendar_id: str) -> CalendarSync:
    creds = json.loads(sa_json)
    from app.modules.scheduling.google_calendar import GoogleCalendarSync

    return GoogleCalendarSync(
        sa_email=creds["client_email"],
        private_key_pem=creds["private_key"],
        calendar_id=calendar_id,
    )


def get_calendar_sync(creds: dict | None = None) -> CalendarSync:
    # 1) Credenciais da clínica (modelo multi-tenant).
    if creds and creds.get("sa_credentials_json"):
        try:
            return _build_google(
                creds["sa_credentials_json"],
                creds.get("calendar_id") or settings.google_calendar_id,
            )
        except Exception:
            logger.exception("Credenciais Google da clínica inválidas; usando NullCalendarSync")
            return _null

    # 2) Credenciais globais (compatibilidade com o deploy atual via env).
    if settings.calendar_provider == "google" and settings.google_sa_credentials_json:
        try:
            return _build_google(
                settings.google_sa_credentials_json, settings.google_calendar_id
            )
        except Exception:
            logger.exception("Falha ao inicializar GoogleCalendarSync; usando NullCalendarSync")

    return _null
