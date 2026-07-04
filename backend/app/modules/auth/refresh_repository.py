"""Acesso à tabela `refresh_tokens` (rotação/revogação).

Sem contexto de tenant: o refresh é pré-tenant (a tabela não tem RLS). A
identificação é sempre pelo `jti` (uuid aleatório do token)."""

import datetime as dt
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import RefreshToken


async def create(
    session: AsyncSession,
    jti: uuid.UUID,
    user_id: uuid.UUID | str,
    clinic_id: uuid.UUID | str,
    expires_at: dt.datetime,
) -> None:
    session.add(
        RefreshToken(
            jti=jti, user_id=user_id, clinic_id=clinic_id, expires_at=expires_at
        )
    )
    await session.flush()


async def get(session: AsyncSession, jti: uuid.UUID | str) -> RefreshToken | None:
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.jti == jti)
    )
    return result.scalar_one_or_none()


async def revoke(session: AsyncSession, jti: uuid.UUID | str) -> None:
    await session.execute(
        update(RefreshToken).where(RefreshToken.jti == jti).values(revoked=True)
    )


async def revoke_all_for_user(
    session: AsyncSession, user_id: uuid.UUID | str
) -> None:
    """Revoga todos os refresh tokens de um usuário (logout global, reset de
    senha, ou reuso detectado de um token roubado)."""
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
