"""Integrações por clínica (Configurações > Integrações).

Todas as rotas exigem o papel `owner` (RBAC). Isolamento por tenant via RLS
(get_tenant_session). Os segredos (tokens de API) são cifrados ao gravar e nunca
devolvidos em claro — o GET só traz dicas mascaradas.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_tenant_session
from app.modules.auth.deps import CurrentUser, require_role
from app.modules.integrations import service
from app.modules.integrations.schemas import IntegrationOut, IntegrationUpdate

router = APIRouter(prefix="/integrations", tags=["integrations"])

# Só o owner configura integrações da clínica.
_owner_only = Depends(require_role("owner"))


@router.get("", response_model=list[IntegrationOut])
async def list_integrations(
    user: CurrentUser = _owner_only,
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.list_integrations(session, user.clinic_id)


@router.get("/{provider}", response_model=IntegrationOut)
async def get_integration(
    provider: str,
    user: CurrentUser = _owner_only,
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.get_integration(session, user.clinic_id, provider)


@router.put("/{provider}", response_model=IntegrationOut)
async def update_integration(
    provider: str,
    body: IntegrationUpdate,
    user: CurrentUser = _owner_only,
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.update_integration(session, user.clinic_id, provider, body)


@router.delete("/{provider}", response_model=IntegrationOut)
async def disconnect_integration(
    provider: str,
    user: CurrentUser = _owner_only,
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.disconnect(session, user.clinic_id, provider)
