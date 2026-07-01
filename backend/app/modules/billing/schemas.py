import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ChargeCreate(BaseModel):
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    descricao: str | None = None
    patient_id: uuid.UUID | None = None
    appointment_id: uuid.UUID | None = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    valor: Decimal
    descricao: str | None
    metodo: str
    status: str
    charge_id: str
    qr_code: str | None
    qr_code_base64: str | None
    patient_id: uuid.UUID | None
    patient_nome: str | None = None
    appointment_id: uuid.UUID | None


class GatewayWebhook(BaseModel):
    charge_id: str
    status: str
