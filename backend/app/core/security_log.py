"""Logging de eventos de segurança (Mixeng: OWASP A09 — Security Logging).

Regras:
- Logar: login falho, rate limit atingido, 401/403, ações destrutivas.
- NUNCA logar: senha, token, CPF, e-mail completo, PII.
"""

import logging

_log = logging.getLogger("security")


def login_failed(ip: str) -> None:
    _log.warning("auth.login_failed ip=%s", ip)


def login_rate_limited(ip: str) -> None:
    _log.warning("auth.rate_limited ip=%s", ip)


def login_ok(clinic_id: str) -> None:
    _log.info("auth.login_ok clinic=%s", clinic_id)


def access_denied(path: str, reason: str) -> None:
    _log.warning("authz.denied path=%s reason=%s", path, reason)
