from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.db_url import prepare_asyncpg


class Base(DeclarativeBase):
    """Base declarativa de todos os modelos ORM."""


# Normaliza a URL para o asyncpg (SSL do Neon + pooler PgBouncer).
_url, _connect_args = prepare_asyncpg(settings.database_url)
# Pool explícito e tunável por env (ver Settings). `pool_pre_ping` descarta
# conexões mortas no checkout; `pool_recycle` evita retê-las além do idle do
# pooler do Neon; `pool_timeout` limita a espera por uma conexão sob carga.
engine = create_async_engine(
    _url,
    echo=False,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    connect_args=_connect_args,
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Sessão SEM contexto de tenant. Use apenas onde RLS não se aplica
    (ex.: login, que precisa achar o usuário antes de existir um token)."""
    async with async_session_maker() as session:
        yield session
