import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    direction: str
    sender: str
    text: str
    created_at: dt.datetime


class ConversationOut(BaseModel):
    """Item da lista do inbox: dados da conversa + prévia da última mensagem."""

    id: uuid.UUID
    patient_id: uuid.UUID | None
    patient_nome: str | None
    external_number: str
    channel: str
    ai_enabled: bool
    last_message_at: dt.datetime | None
    last_message_preview: str | None
    last_message_sender: str | None
    unread: bool


class ManualMessageIn(BaseModel):
    text: str


class ConversationUpdate(BaseModel):
    ai_enabled: bool | None = None
