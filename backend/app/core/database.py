from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.db_url import prepare_asyncpg


class Base(DeclarativeBase):
    """Base declarativa de todos os modelos ORM."""


# Normaliza a URL para o asyncpg (SSL do Neon + pooler PgBouncer).
_url, _connect_args = prepare_asyncpg(settings.database_url)
engine = create_async_engine(
    _url, echo=False, pool_pre_ping=True, connect_args=_connect_args
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Sessão SEM contexto de tenant. Use apenas onde RLS não se aplica
    (ex.: login, que precisa achar o usuário antes de existir um token)."""
    async with async_session_maker() as session:
        yield session
