import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.modules.auth.repository import find_user_for_auth


def _issue_tokens(user_id, clinic_id, role) -> dict:
    return {
        "access_token": create_access_token(user_id, clinic_id, role),
        "refresh_token": create_refresh_token(user_id, clinic_id, role),
        "token_type": "bearer",
    }


async def authenticate(session: AsyncSession, email: str, password: str) -> dict:
    user = await find_user_for_auth(session, email)
    if (
        user is None
        or not user["is_active"]
        or not verify_password(password, user["password_hash"])
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas"
        )
    return _issue_tokens(user["id"], user["clinic_id"], user["role"])


async def refresh_tokens(refresh_token: str) -> dict:
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
    return _issue_tokens(payload["sub"], payload["clinic_id"], payload["role"])
