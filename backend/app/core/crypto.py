"""Criptografia simétrica para segredos de integrações (tokens de API por clínica).

Usa Fernet (AES-128-CBC + HMAC) da lib `cryptography`. A chave é derivada de
`CREDENTIALS_SECRET` (recomendado: aleatória, ≥ 32 chars e FIXA). Se não houver,
cai no `JWT_SECRET` — assim o ambiente atual continua funcionando sem variável
nova, mas o ideal é uma secret dedicada (ver .env.example).

Os segredos das integrações (token do WhatsApp, chave do Gemini, etc.) NUNCA são
gravados em claro: o service cifra antes de persistir e só decifra na hora de
usar. A API jamais devolve o valor em claro — apenas dicas mascaradas.

Importante: se a secret usada para derivar a chave mudar, os dados já cifrados
ficam ilegíveis (decrypt falha e tratamos como "sem segredo"). Mantenha-a fixa.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger("core.crypto")

_fernet_cache: Fernet | None = None


def _fernet() -> Fernet:
    global _fernet_cache
    if _fernet_cache is None:
        secret = settings.credentials_secret or settings.jwt_secret
        # Deriva uma chave Fernet válida (32 bytes em urlsafe-base64) de qualquer
        # string, via SHA-256. Determinístico: a mesma secret gera a mesma chave.
        digest = hashlib.sha256(secret.encode()).digest()
        _fernet_cache = Fernet(base64.urlsafe_b64encode(digest))
    return _fernet_cache


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


def encrypt_dict(data: dict) -> str:
    """Cifra um dicionário de segredos como um único token."""
    return encrypt(json.dumps(data, separators=(",", ":"), ensure_ascii=False))


def decrypt_dict(token: str | None) -> dict:
    """Decifra o token de segredos. Devolve {} se vazio, ilegível ou corrompido."""
    if not token:
        return {}
    try:
        return json.loads(decrypt(token))
    except (InvalidToken, ValueError):
        logger.warning("Segredo de integração ilegível (chave trocada?); ignorando.")
        return {}
