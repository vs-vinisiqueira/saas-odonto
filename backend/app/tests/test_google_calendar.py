"""Testes do GoogleCalendarSync sem rede: troca de token + upsert/delete de evento."""

import datetime as dt
import types
import uuid

import pytest

from app.modules.scheduling.google_calendar import GoogleCalendarSync
from app.modules.scheduling.models import STATUS_SCHEDULED, STATUS_CONFIRMED


UTC = dt.timezone.utc


def _make_appt(**kwargs) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        id=kwargs.get("id", uuid.uuid4()),
        clinic_id=kwargs.get("clinic_id", uuid.uuid4()),
        patient_id=kwargs.get("patient_id", uuid.uuid4()),
        dentist_id=kwargs.get("dentist_id", None),
        starts_at=kwargs.get("starts_at", dt.datetime(2025, 1, 10, 9, 0, tzinfo=UTC)),
        ends_at=kwargs.get("ends_at", dt.datetime(2025, 1, 10, 9, 30, tzinfo=UTC)),
        status=kwargs.get("status", STATUS_SCHEDULED),
        notes=kwargs.get("notes", None),
    )


class _Resp:
    def __init__(self, data: dict, status_code: int = 200):
        self._data = data
        self.status_code = status_code

    def json(self) -> dict:
        return self._data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AssertionError(f"HTTP {self.status_code}")


class _FakeClient:
    """httpx.AsyncClient fake que grava chamadas e retorna respostas configuradas."""

    def __init__(self, responses: list[_Resp]):
        self._responses = iter(responses)
        self.calls: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    def _record(self, method: str, url: str, **kwargs) -> _Resp:
        self.calls.append({"method": method, "url": url, **kwargs})
        return next(self._responses)

    async def post(self, url, *, data=None, json=None, headers=None):
        return self._record("POST", url, data=data, json=json, headers=headers)

    async def get(self, url, *, headers=None, params=None):
        return self._record("GET", url, headers=headers, params=params)

    async def put(self, url, *, json=None, headers=None):
        return self._record("PUT", url, json=json, headers=headers)

    async def delete(self, url, *, headers=None):
        return self._record("DELETE", url, headers=headers)


def _patch_httpx(monkeypatch, responses: list[_Resp]) -> _FakeClient:
    client = _FakeClient(responses)
    monkeypatch.setattr(
        "app.modules.scheduling.google_calendar.httpx.AsyncClient",
        lambda **_: client,
    )
    return client


# JWT é gerado com RSA real; substituímos por stub para não precisar de chave.
def _patch_jwt(monkeypatch):
    monkeypatch.setattr(
        "app.modules.scheduling.google_calendar._make_jwt",
        lambda *_: "fake.jwt.token",
    )


_TOKEN_RESP = _Resp({"access_token": "tok-abc", "expires_in": 3600})
_EMPTY_LIST = _Resp({"items": []})
_EVENT_CREATED = _Resp({"id": "gcal-event-1"})
_EVENT_LIST_FOUND = _Resp({"items": [{"id": "gcal-event-1"}]})
_NO_CONTENT = _Resp({}, status_code=204)


@pytest.mark.asyncio
async def test_upsert_creates_event(monkeypatch):
    """Quando não existe evento anterior, faz POST."""
    _patch_jwt(monkeypatch)
    client = _patch_httpx(monkeypatch, [_TOKEN_RESP, _EMPTY_LIST, _EVENT_CREATED])

    gw = GoogleCalendarSync(
        sa_email="sa@proj.iam.gserviceaccount.com",
        private_key_pem="FAKE",
        calendar_id="primary",
    )
    appt = _make_appt()
    await gw.upsert_event(appt)

    methods = [c["method"] for c in client.calls]
    assert methods == ["POST", "GET", "POST"]
    # Último POST é para criar o evento
    body = client.calls[-1]["json"]
    assert "Consulta" in body["summary"]
    assert body["start"]["timeZone"] == "UTC"
    assert body["extendedProperties"]["private"]["saas_odonto_id"] == str(appt.id)


@pytest.mark.asyncio
async def test_upsert_updates_existing_event(monkeypatch):
    """Quando evento já existe (encontrado via extendedProperty), faz PUT."""
    _patch_jwt(monkeypatch)
    client = _patch_httpx(monkeypatch, [_TOKEN_RESP, _EVENT_LIST_FOUND, _EVENT_CREATED])

    gw = GoogleCalendarSync(
        sa_email="sa@proj.iam.gserviceaccount.com",
        private_key_pem="FAKE",
        calendar_id="primary",
    )
    appt = _make_appt(status=STATUS_CONFIRMED)
    await gw.upsert_event(appt)

    methods = [c["method"] for c in client.calls]
    assert methods == ["POST", "GET", "PUT"]
    assert "confirmado" in client.calls[-1]["json"]["summary"]


@pytest.mark.asyncio
async def test_delete_event(monkeypatch):
    """Localiza e deleta o evento no calendário."""
    _patch_jwt(monkeypatch)
    client = _patch_httpx(monkeypatch, [_TOKEN_RESP, _EVENT_LIST_FOUND, _NO_CONTENT])

    gw = GoogleCalendarSync(
        sa_email="sa@proj.iam.gserviceaccount.com",
        private_key_pem="FAKE",
        calendar_id="cal-id@group.calendar.google.com",
    )
    appt = _make_appt()
    await gw.delete_event(appt)

    methods = [c["method"] for c in client.calls]
    assert methods == ["POST", "GET", "DELETE"]
    assert "gcal-event-1" in client.calls[-1]["url"]


@pytest.mark.asyncio
async def test_delete_noop_when_event_not_found(monkeypatch):
    """Se o evento não existe no calendário, não tenta DELETE."""
    _patch_jwt(monkeypatch)
    client = _patch_httpx(monkeypatch, [_TOKEN_RESP, _EMPTY_LIST])

    gw = GoogleCalendarSync(
        sa_email="sa@proj.iam.gserviceaccount.com",
        private_key_pem="FAKE",
    )
    appt = _make_appt()
    await gw.delete_event(appt)

    methods = [c["method"] for c in client.calls]
    assert "DELETE" not in methods
