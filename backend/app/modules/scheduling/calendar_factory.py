"""Seleção do adapter de calendário conforme a config.

Default = NullCalendarSync (no-op). "google" só é usado se houver
GOOGLE_SA_CREDENTIALS_JSON; caso contrário cai no null — assim CI/dev não
precisam de credenciais do Google.
"""

import json
import logging

from app.core.config import settings
from app.modules.scheduling.calendar_sync import CalendarSync, NullCalendarSync

logger = logging.getLogger("scheduling.calendar_factory")

_null = NullCalendarSync()


def get_calendar_sync() -> CalendarSync:
    if settings.calendar_provider == "google" and settings.google_sa_credentials_json:
        try:
            creds = json.loads(settings.google_sa_credentials_json)
            from app.modules.scheduling.google_calendar import GoogleCalendarSync

            return GoogleCalendarSync(
                sa_email=creds["client_email"],
                private_key_pem=creds["private_key"],
                calendar_id=settings.google_calendar_id,
            )
        except Exception:
            logger.exception("Falha ao inicializar GoogleCalendarSync; usando NullCalendarSync")
    return _null
