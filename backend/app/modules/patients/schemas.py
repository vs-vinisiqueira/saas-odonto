import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class PatientBase(BaseModel):
    nome: str
    telefone: str
    email: EmailStr | None = None
    observacoes: str | None = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    nome: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    observacoes: str | None = None


class PatientOut(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class RecordAppointment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    starts_at: dt.datetime
    ends_at: dt.datetime
    status: str
    notes: str | None


class RecordCharge(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    valor: Decimal
    descricao: str | None
    status: str
    charge_id: str
    created_at: dt.datetime


class PatientRecordOut(BaseModel):
    patient: PatientOut
    appointments: list[RecordAppointment]
    charges: list[RecordCharge]
