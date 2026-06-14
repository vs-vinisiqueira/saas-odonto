from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_tenant_session
from app.modules.auth.deps import CurrentUser, get_current_user, require_role
from app.modules.clinics import service
from app.modules.clinics.schemas import ClinicOut, ClinicUpdate

router = APIRouter(prefix="/clinics", tags=["clinics"])


@router.get("/me", response_model=ClinicOut)
async def get_my_clinic(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.get_current_clinic(session, user.clinic_id)


@router.patch(
    "/me",
    response_model=ClinicOut,
    dependencies=[Depends(require_role("owner"))],
)
async def update_my_clinic(
    body: ClinicUpdate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.update_current_clinic(session, user.clinic_id, body)
