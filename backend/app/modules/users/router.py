"""Gestão de usuários da clínica (Configurações > Usuários).

Todas as rotas exigem o papel `owner` (RBAC via require_role). O isolamento por
tenant vem do RLS (get_tenant_session) — um owner só enxerga/gerencia usuários
da própria clínica. "Excluir" é desativar (is_active=false), preservando o
histórico; não há remoção física.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_tenant_session
from app.modules.auth.deps import CurrentUser, get_current_user, require_role
from app.modules.users import service
from app.modules.users.schemas import (
    DentistOut,
    PasswordReset,
    UserCreate,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])

# Só o owner gerencia a equipe.
_owner_only = Depends(require_role("owner"))


@router.get("", response_model=list[UserOut])
async def list_users(
    user: CurrentUser = _owner_only,
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.list_users(session, user.clinic_id)


@router.get("/dentists", response_model=list[DentistOut])
async def list_dentists(
    # Qualquer usuário autenticado da clínica pode listar dentistas (para o
    # seletor de "dentista responsável" na agenda). Não é gestão de equipe.
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.list_dentists(session, user.clinic_id)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    user: CurrentUser = _owner_only,
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.create_user(session, user.clinic_id, body)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    user: CurrentUser = _owner_only,
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.update_user(session, user.clinic_id, user_id, user.id, body)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    user_id: uuid.UUID,
    body: PasswordReset,
    user: CurrentUser = _owner_only,
    session: AsyncSession = Depends(get_tenant_session),
):
    await service.reset_password(session, user.clinic_id, user_id, body)
