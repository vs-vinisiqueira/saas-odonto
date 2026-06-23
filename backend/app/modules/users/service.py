import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.auth.repository import find_user_for_auth
from app.modules.users import repository
from app.modules.users.schemas import PasswordReset, UserCreate, UserUpdate
from app.shared.exceptions import Conflict, NotFound


async def list_users(session: AsyncSession, clinic_id: uuid.UUID | str) -> list[User]:
    return await repository.list_all(session, clinic_id)


async def list_dentists(session: AsyncSession, clinic_id: uuid.UUID | str) -> list[User]:
    return await repository.list_dentists(session, clinic_id)


async def get_user(
    session: AsyncSession, clinic_id: uuid.UUID | str, user_id: uuid.UUID | str
) -> User:
    user = await repository.get_by_id(session, clinic_id, user_id)
    if user is None:
        raise NotFound("Usuário não encontrado")
    return user


async def create_user(
    session: AsyncSession, clinic_id: uuid.UUID | str, data: UserCreate
) -> User:
    # E-mail normalizado (minúsculo, sem espaços) para casar com o login, que é
    # case-insensitive, e garantir a unicidade global de forma consistente.
    email = data.email.strip().lower()
    # E-mail é único GLOBALMENTE. O RLS impediria de "ver" um e-mail de outra
    # clínica, então checamos via a função SECURITY DEFINER (ignora RLS) para
    # dar um 409 claro em vez de estourar a constraint do banco.
    if await find_user_for_auth(session, email):
        raise Conflict("Já existe um usuário com esse e-mail")

    user = User(
        clinic_id=clinic_id,
        email=email,
        password_hash=hash_password(data.password),
        role=data.role,
        nome=data.nome,
        telefone=data.telefone,
        is_active=True,
    )
    return await repository.add(session, user)


async def update_user(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    user_id: uuid.UUID | str,
    actor_id: str,
    data: UserUpdate,
) -> User:
    user = await get_user(session, clinic_id, user_id)

    # Trava de auto-lockout: o owner não pode rebaixar o próprio papel nem se
    # desativar (perderia o acesso de administração).
    if str(user.id) == str(actor_id):
        if data.role is not None and data.role != user.role:
            raise Conflict("Você não pode alterar o seu próprio papel")
        if data.is_active is False:
            raise Conflict("Você não pode desativar o seu próprio usuário")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await session.flush()
    return user


async def reset_password(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    user_id: uuid.UUID | str,
    data: PasswordReset,
) -> None:
    user = await get_user(session, clinic_id, user_id)
    user.password_hash = hash_password(data.password)
    await session.flush()
