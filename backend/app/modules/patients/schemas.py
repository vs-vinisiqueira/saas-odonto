import uuid

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
