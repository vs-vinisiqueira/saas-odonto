import datetime as dt
import uuid

import bcrypt
import jwt

from app.core.config import settings

# bcrypt aceita no máximo 72 bytes; truncamos para evitar erro em senhas longas.
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode()[:_BCRYPT_MAX_BYTES], bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode()[:_BCRYPT_MAX_BYTES], password_hash.encode())


def _create_token(
    subject: str | uuid.UUID,
    clinic_id: str | uuid.UUID,
    role: str,
    expires_delta: dt.timedelta,
    token_type: str,
) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(subject),
        "clinic_id": str(clinic_id),
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject, clinic_id, role) -> str:
    return _create_token(
        subject, clinic_id, role,
        dt.timedelta(minutes=settings.access_token_expire_minutes), "access",
    )


def create_refresh_token(subject, clinic_id, role) -> str:
    return _create_token(
        subject, clinic_id, role,
        dt.timedelta(days=settings.refresh_token_expire_days), "refresh",
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
