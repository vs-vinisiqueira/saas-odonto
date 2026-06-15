import uuid

from pydantic import BaseModel, ConfigDict


class WhatsAppNumberCreate(BaseModel):
    phone_number_id: str
    label: str | None = None


class WhatsAppNumberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone_number_id: str
    label: str | None
