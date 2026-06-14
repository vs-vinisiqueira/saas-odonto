"""Seed de desenvolvimento: cria 2 clínicas + 1 usuário owner cada.

Roda pela conexão ADMIN (superusuário), que ignora o RLS — por isso consegue
inserir dados de tenants diferentes na mesma transação. Idempotente: se o
e-mail do owner já existe, pula o par.

Uso (dentro do container):  uv run python -m scripts.seed
"""

import asyncio
import os
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.db_url import prepare_asyncpg
from app.core.security import hash_password

ADMIN_URL = os.getenv("ADMIN_DATABASE_URL") or os.getenv("DATABASE_URL")

# (nome da clínica, e-mail do owner)
CLINICS = [
    ("Clínica Sorriso", "owner@sorriso.com"),
    ("Clínica Bem Estar", "owner@bemestar.com"),
]
DEFAULT_PASSWORD = "senha123"


async def main() -> None:
    if not ADMIN_URL:
        raise SystemExit("Defina ADMIN_DATABASE_URL no ambiente.")

    _url, _connect_args = prepare_asyncpg(ADMIN_URL)
    engine = create_async_engine(_url, connect_args=_connect_args)
    async with engine.begin() as conn:
        for nome, email in CLINICS:
            exists = (
                await conn.execute(
                    text("SELECT 1 FROM users WHERE email = :e"), {"e": email}
                )
            ).first()
            if exists:
                print(f"= já existe: {email} (pulando)")
                continue

            clinic_id = uuid.uuid4()
            await conn.execute(
                text(
                    "INSERT INTO clinics (id, nome, config) "
                    "VALUES (:id, :nome, '{}'::jsonb)"
                ),
                {"id": clinic_id, "nome": nome},
            )
            await conn.execute(
                text(
                    "INSERT INTO users (id, clinic_id, email, password_hash, role) "
                    "VALUES (:id, :cid, :email, :ph, 'owner')"
                ),
                {
                    "id": uuid.uuid4(),
                    "cid": clinic_id,
                    "email": email,
                    "ph": hash_password(DEFAULT_PASSWORD),
                },
            )
            print(f"+ criado: {nome} | {email} | senha: {DEFAULT_PASSWORD}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
