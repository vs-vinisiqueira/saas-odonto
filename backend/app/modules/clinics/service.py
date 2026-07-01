import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clinics import repository
from app.modules.clinics.models import Clinic
from app.modules.clinics.schemas import ClinicUpdate
from app.shared.exceptions import NotFound


async def get_current_clinic(session: AsyncSession, clinic_id: uuid.UUID | str) -> Clinic:
    clinic = await repository.get_by_id(session, clinic_id)
    if clinic is None:
        raise NotFound("Clínica não encontrada")
    return clinic


async def update_current_clinic(
    session: AsyncSession, clinic_id: uuid.UUID | str, data: ClinicUpdate
) -> Clinic:
    clinic = await get_current_clinic(session, clinic_id)
    if data.nome is not None:
        clinic.nome = data.nome
    if data.config is not None:
        # Merge raso por chave de topo (ex.: "clinic_data", "working_hours",
        # "preferences") — cada seção da tela de Configurações salva só a sua
        # própria chave, sem apagar as demais já gravadas no mesmo JSONB.
        incoming = data.config.model_dump(exclude_none=True)
        clinic.config = {**clinic.config, **incoming}
    await session.flush()
    # O commit acontece no teardown da get_tenant_session (transação da request).
    return clinic
