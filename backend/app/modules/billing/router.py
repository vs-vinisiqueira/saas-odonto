"""Módulo financeiro: cobranças Pix (via PaymentGateway) + webhook do provedor.

CRUD de cobrança é escopado por tenant (RLS). O webhook do provedor chega sem
JWT e localiza a clínica pelo charge_id (ver service.handle_webhook).
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_tenant_session
from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.billing import service
from app.modules.billing.schemas import ChargeCreate, GatewayWebhook, PaymentOut

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post(
    "/charges", response_model=PaymentOut, status_code=status.HTTP_201_CREATED
)
async def create_charge(
    body: ChargeCreate,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.create_charge(session, user.clinic_id, body)


@router.get("/charges", response_model=list[PaymentOut])
async def list_charges(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.list_payments(session, user.clinic_id)


@router.get("/charges/{payment_id}", response_model=PaymentOut)
async def get_charge(
    payment_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.get_payment(session, user.clinic_id, payment_id)


@router.post("/charges/{payment_id}/refresh", response_model=PaymentOut)
async def refresh_charge(
    payment_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.refresh_status(session, user.clinic_id, payment_id)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def gateway_webhook(payload: GatewayWebhook):
    """Notificação do provedor. Responde 200 mesmo para charge_id desconhecido
    (padrão de webhooks: não revelar e não pedir retry infinito)."""
    ok = await service.handle_webhook(payload.charge_id, payload.status)
    return {"ok": ok}
