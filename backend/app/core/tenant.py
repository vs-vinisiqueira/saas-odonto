import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.modules.auth.deps import CurrentUser, get_current_user


@asynccontextmanager
async def open_tenant_session(
    clinic_id: str | uuid.UUID,
) -> AsyncGenerator[AsyncSession, None]:
    """Abre uma sessão JÁ ESCOPADA ao tenant `clinic_id`.

    Define `app.current_clinic` numa transação; a partir daí o RLS do Postgres
    garante que qualquer query só enxerga o tenant certo. Usado tanto pelo
    dependency HTTP (tenant vindo do JWT) quanto pelo agente de IA (tenant vindo
    do canal/webhook, sem JWT).
    """
    async with async_session_maker() as session:
        async with session.begin():
            await session.execute(
                text("SELECT set_config('app.current_clinic', :cid, true)"),
                {"cid": str(clinic_id)},
            )
            yield session


async def get_tenant_session(
    current_user: CurrentUser = Depends(get_current_user),
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency HTTP: sessão escopada ao tenant do usuário autenticado.

    O clinic_id vem de dentro do JWT (nunca de parâmetro do cliente).
    """
    async with open_tenant_session(current_user.clinic_id) as session:
        yield session
