import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User

# O RLS já isola por tenant (app.current_clinic). Filtramos por clinic_id
# explicitamente também — defesa em profundidade, igual aos demais módulos.


async def list_all(session: AsyncSession, clinic_id: uuid.UUID | str) -> list[User]:
    result = await session.execute(
        select(User)
        .where(User.clinic_id == clinic_id)
        .order_by(User.is_active.desc(), User.nome, User.email)
    )
    return list(result.scalars().all())


async def get_by_id(
    session: AsyncSession, clinic_id: uuid.UUID | str, user_id: uuid.UUID | str
) -> User | None:
    result = await session.execute(
        select(User).where(User.id == user_id, User.clinic_id == clinic_id)
    )
    return result.scalar_one_or_none()


async def add(session: AsyncSession, user: User) -> User:
    session.add(user)
    await session.flush()
    return user
