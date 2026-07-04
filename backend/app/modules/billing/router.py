"""Módulo financeiro: cobranças Pix (via PaymentGateway) + webhook do provedor.

CRUD de cobrança é escopado por tenant (RLS). O webhook do provedor chega sem
JWT e localiza a clínica pelo charge_id (ver service.handle_webhook).
"""

import hashlib
import hmac
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.tenant import get_tenant_session
from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.billing import service
from app.modules.billing.schemas import ChargeCreate, GatewayWebhook, PaymentOut

logger = logging.getLogger("billing.router")

router = APIRouter(prefix="/billing", tags=["billing"])


def _verify_mercadopago_signature(request: Request, data_id: str) -> bool:
    """Valida o header `x-signature` do Mercado Pago (HMAC-SHA256).

    Template do manifesto (docs do MP): `id:<data.id>;request-id:<x-request-id>;ts:<ts>;`.
    Retorna True quando não há segredo configurado (verificação desligada, compat).
    """
    secret = settings.mercadopago_webhook_secret
    if not secret:
        return True
    sig = request.headers.get("x-signature") or ""
    parts = dict(
        p.strip().split("=", 1) for p in sig.split(",") if "=" in p
    )
    ts, v1 = parts.get("ts"), parts.get("v1")
    if not ts or not v1:
        return False
    request_id = request.headers.get("x-request-id", "")
    # data.id alfanumérico deve ir em minúsculas no manifesto (regra do MP).
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{ts};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(v1, expected)


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


@router.delete("/charges/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_charge(
    payment_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    await service.delete_charge(session, user.clinic_id, payment_id)


@router.post("/charges/{payment_id}/refresh", response_model=PaymentOut)
async def refresh_charge(
    payment_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    return await service.refresh_status(session, user.clinic_id, payment_id)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def gateway_webhook(payload: GatewayWebhook):
    """Notificação genérica (mock/teste): recebe {charge_id, status} direto.
    Responde 200 mesmo para charge_id desconhecido (padrão de webhooks).

    SEM autenticação nem assinatura: quem souber um charge_id conseguiria marcar
    a cobrança como paga sem pagar. Por isso só existe em dev/CI. Em produção, a
    confirmação vem pelo webhook do provedor real (/billing/mercadopago/webhook),
    que reconsulta o status na API do gateway."""
    if settings.environment == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    ok = await service.handle_webhook(payload.charge_id, payload.status)
    return {"ok": ok}


@router.post("/mercadopago/webhook", status_code=status.HTTP_200_OK)
async def mercadopago_webhook(request: Request):
    """Webhook do Mercado Pago: manda só o id do pagamento (no corpo
    `data.id` ou na query `id`); consultamos o status na API. Responde 200
    sempre (boa prática de webhook)."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    ev_type = (body.get("type") if isinstance(body, dict) else None) or (
        request.query_params.get("topic") or request.query_params.get("type")
    )
    if ev_type not in (None, "payment"):
        return {"ok": False}

    payment_id = ""
    if isinstance(body, dict):
        payment_id = str((body.get("data") or {}).get("id") or "")
    if not payment_id:
        payment_id = (
            request.query_params.get("id")
            or request.query_params.get("data.id")
            or ""
        )

    if not payment_id:
        return {"ok": False}

    # Autenticidade: só o Mercado Pago (que conhece a chave secreta) assina.
    if not _verify_mercadopago_signature(request, payment_id):
        logger.warning("Webhook do Mercado Pago com assinatura inválida; ignorado.")
        return {"ok": False}

    try:
        ok = await service.handle_mercadopago_event(payment_id)
    except Exception:
        logger.exception("Falha ao processar webhook do Mercado Pago")
        return {"ok": False}
    return {"ok": ok}
