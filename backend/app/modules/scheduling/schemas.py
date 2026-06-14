import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field


class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    starts_at: dt.datetime
    duration_min: int = Field(default=30, ge=5, le=480)
    dentist_id: uuid.UUID | None = None
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    starts_at: dt.datetime | None = None
    duration_min: int | None = Field(default=None, ge=5, le=480)
    dentist_id: uuid.UUID | None = None
    status: str | None = None
    notes: str | None = None


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    dentist_id: uuid.UUID | None
    starts_at: dt.datetime
    ends_at: dt.datetime
    status: str
    notes: str | None


class SlotOut(BaseModel):
    starts_at: dt.datetime
    ends_at: dt.datetime
