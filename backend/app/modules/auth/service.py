import datetime as dt
import uuid

import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth import refresh_repository as refresh_repo
from app.modules.auth.repository import find_user_for_auth

# Hash bcrypt fixo (senha aleatória) verificado quando o e-mail NÃO existe, para
# gastar o mesmo tempo do caso "existe" e não vazar, por timing, quais e-mails
# têm conta (enumeração de usuários).
_DUMMY_PASSWORD_HASH = hash_password("timing-attack-mitigation-dummy")


async def _issue_tokens(
    session: AsyncSession, user_id, clinic_id, role
) -> dict:
    """Emite access + refresh e PERSISTE o jti do refresh (para rotação/revogação)."""
    jti = uuid.uuid4()
    expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
        days=settings.refresh_token_expire_days
    )
    await refresh_repo.create(session, jti, user_id, clinic_id, expires_at)
    return {
        "access_token": create_access_token(user_id, clinic_id, role),
        "refresh_token": create_refresh_token(user_id, clinic_id, role, jti),
        "token_type": "bearer",
    }


async def authenticate(session: AsyncSession, email: str, password: str) -> dict:
    # E-mail é case-insensitive: normalizamos para casar com o que foi gravado
    # (evita falha de login por maiúscula automática do teclado, p.ex. no mobile).
    user = await find_user_for_auth(session, email.strip().lower())
    # Roda o bcrypt SEMPRE (com hash dummy quando não há usuário) para igualar o
    # tempo de resposta e evitar enumeração por timing.
    password_hash = user["password_hash"] if user else _DUMMY_PASSWORD_HASH
    password_ok = verify_password(password, password_hash)
    if user is None or not user["is_active"] or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas"
        )
    tokens = await _issue_tokens(session, user["id"], user["clinic_id"], user["role"])
    await session.commit()
    return tokens


async def refresh_tokens(session: AsyncSession, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        )
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Tipo de token inválido"
        )

    jti = payload.get("jti")
    # Tokens antigos (pré-rotação, sem jti) não são mais aceitos: força re-login.
    row = await refresh_repo.get(session, jti) if jti else None
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        )
    if row.revoked:
        # Reuso de um token já rotacionado => sinal de roubo. Revoga TODA a
        # família de tokens do usuário e recusa.
        await refresh_repo.revoke_all_for_user(session, row.user_id)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada. Faça login novamente.",
        )

    # Rotação: invalida o token atual e emite um novo par.
    await refresh_repo.revoke(session, jti)
    tokens = await _issue_tokens(
        session, payload["sub"], payload["clinic_id"], payload["role"]
    )
    await session.commit()
    return tokens


async def logout(session: AsyncSession, refresh_token: str) -> None:
    """Revoga o refresh token apresentado (logout real). Idempotente: um token
    inválido/desconhecido simplesmente não revoga nada."""
    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError:
        return
    jti = payload.get("jti")
    if jti:
        await refresh_repo.revoke(session, jti)
        await session.commit()
