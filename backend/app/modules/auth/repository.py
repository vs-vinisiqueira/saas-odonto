from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def find_user_for_auth(session: AsyncSession, email: str):
    """Busca o usuário por e-mail via função SECURITY DEFINER, que ignora o RLS
    (o login acontece antes de haver contexto de tenant)."""
    result = await session.execute(
        text(
            "SELECT id, clinic_id, email, password_hash, role, is_active "
            "FROM auth_find_user_by_email(:email)"
        ),
        {"email": email},
    )
    return result.mappings().first()
