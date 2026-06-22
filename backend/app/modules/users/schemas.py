import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.auth.models import ROLES


def _validate_role(v: str) -> str:
    if v not in ROLES:
        raise ValueError(f"Papel inválido. Use um de: {', '.join(sorted(ROLES))}")
    return v


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str
    nome: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=32)

    _check_role = field_validator("role")(_validate_role)


class UserUpdate(BaseModel):
    nome: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=32)
    role: str | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def _role(cls, v: str | None) -> str | None:
        return _validate_role(v) if v is not None else v


class PasswordReset(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    role: str
    nome: str | None
    telefone: str | None
    is_active: bool
    created_at: dt.datetime
