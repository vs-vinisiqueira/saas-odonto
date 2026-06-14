import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.db_url import prepare_asyncpg

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# Migrations rodam pela conexão ADMIN (ADMIN_DATABASE_URL): o role DONO das
# tabelas. Ele cria tabelas, habilita RLS e define políticas/funções e, por ser
# o dono (e não FORCE RLS), ignora o RLS — funciona tanto com o superusuário do
# Postgres local quanto com o role dono do Neon (que não é superusuário).
db_url = os.getenv("ADMIN_DATABASE_URL") or os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("Defina ADMIN_DATABASE_URL (ou ao menos DATABASE_URL) no ambiente.")
config.set_main_option("sqlalchemy.url", db_url)

# Migrations escritas à mão nesta fase — sem autogenerate.
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    # Normaliza a URL admin para o asyncpg (SSL do Neon). Use o endpoint DIRETO
    # (sem -pooler) aqui: PgBouncer atrapalha DDL/migrations.
    url, connect_args = prepare_asyncpg(db_url)
    connectable = create_async_engine(
        url, poolclass=pool.NullPool, connect_args=connect_args
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
