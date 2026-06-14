import uuid

from pydantic import BaseModel, ConfigDict


class ClinicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    config: dict


class ClinicUpdate(BaseModel):
    nome: str | None = None
    config: dict | None = None
