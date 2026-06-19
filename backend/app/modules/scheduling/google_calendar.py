"""Adapter real para o Google Calendar (serviço de conta = Service Account).

Usa a Google Calendar API v3 via httpx + JWT de serviço próprio (sem depender do
SDK gigante `google-api-python-client`). Fluxo:
  1. Gera um JWT assinado com a chave privada da Service Account.
  2. Troca por um Access Token no endpoint OAuth2 da Google.
  3. Usa o token para criar/atualizar/remover eventos no calendário configurado.

A Service Account precisa:
  - Ter o papel "Editor" no calendário alvo (ou acesso via Google Workspace
    domain-wide delegation, se preferir).
  - Compartilhar o calendário com o e-mail da Service Account.

Variáveis necessárias em .env:
  CALENDAR_PROVIDER=google
  GOOGLE_CALENDAR_ID=primary          # ou <id>@group.calendar.google.com
  GOOGLE_SA_CREDENTIALS_JSON=<json>   # conteúdo inteiro do arquivo credentials.json
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import time
import uuid

import httpx

from app.modules.scheduling.calendar_sync import CalendarSync
from app.modules.scheduling.models import Appointment, STATUS_CONFIRMED, STATUS_COMPLETED

logger = logging.getLogger("scheduling.google_calendar")

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SCOPE = "https://www.googleapis.com/auth/calendar"
_API_BASE = "https://www.googleapis.com/calendar/v3"


def _make_jwt(sa_email: str, private_key_pem: str) -> str:
    """Monta e assina o JWT para troca por Access Token."""
    import base64
    import hashlib
    import hmac
    import struct

    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": sa_email,
        "scope": _SCOPE,
        "aud": _TOKEN_URL,
        "exp": now + 3600,
        "iat": now,
    }

    def b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    h = b64(json.dumps(header).encode())
    p = b64(json.dumps(payload).encode())
    message = f"{h}.{p}".encode()

    # Assina com RSA-SHA256 usando cryptography (já no ambiente como dep transitiva).
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    sig = key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    return f"{h}.{p}.{b64(sig)}"


class GoogleCalendarSync(CalendarSync):
    """Sincroniza agendamentos com um calendário Google via Service Account."""

    def __init__(
        self,
        sa_email: str,
        private_key_pem: str,
        calendar_id: str = "primary",
    ) -> None:
        self._sa_email = sa_email
        self._private_key = private_key_pem
        self._calendar_id = calendar_id
        self._access_token: str | None = None
        self._token_expiry: float = 0.0

    async def _get_token(self) -> str:
        if self._access_token and time.time() < self._token_expiry - 60:
            return self._access_token
        jwt = _make_jwt(self._sa_email, self._private_key)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                _TOKEN_URL,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": jwt,
                },
            )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600)
        return self._access_token  # type: ignore[return-value]

    def _headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _event_body(self, appt: Appointment) -> dict:
        starts_at = appt.starts_at
        ends_at = appt.ends_at
        status_label = {
            STATUS_CONFIRMED: "confirmado",
            STATUS_COMPLETED: "concluído",
        }.get(appt.status, "agendado")
        return {
            "summary": f"Consulta [{status_label}]",
            "description": appt.notes or "",
            "start": {"dateTime": starts_at.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": ends_at.isoformat(), "timeZone": "UTC"},
            "extendedProperties": {
                "private": {"saas_odonto_id": str(appt.id)}
            },
        }

    def _event_url(self, event_id: str | None = None) -> str:
        base = f"{_API_BASE}/calendars/{self._calendar_id}/events"
        return f"{base}/{event_id}" if event_id else base

    async def _find_event_id(self, appt: Appointment, token: str) -> str | None:
        """Busca o evento pelo extendedProperty saas_odonto_id."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                self._event_url(),
                headers=self._headers(token),
                params={"privateExtendedProperty": f"saas_odonto_id={appt.id}"},
            )
        if resp.status_code != 200:
            return None
        items = resp.json().get("items", [])
        return items[0]["id"] if items else None

    async def upsert_event(self, appt: Appointment) -> None:
        try:
            token = await self._get_token()
            event_id = await self._find_event_id(appt, token)
            body = self._event_body(appt)
            async with httpx.AsyncClient(timeout=15) as client:
                if event_id:
                    resp = await client.put(
                        self._event_url(event_id),
                        json=body,
                        headers=self._headers(token),
                    )
                else:
                    resp = await client.post(
                        self._event_url(),
                        json=body,
                        headers=self._headers(token),
                    )
            resp.raise_for_status()
        except Exception:
            logger.exception("Falha ao sincronizar evento %s com Google Calendar", appt.id)

    async def delete_event(self, appt: Appointment) -> None:
        try:
            token = await self._get_token()
            event_id = await self._find_event_id(appt, token)
            if not event_id:
                return
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.delete(
                    self._event_url(event_id), headers=self._headers(token)
                )
            if resp.status_code not in (200, 204, 404):
                resp.raise_for_status()
        except Exception:
            logger.exception("Falha ao remover evento %s do Google Calendar", appt.id)
