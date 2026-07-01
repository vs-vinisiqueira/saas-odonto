import uuid

from pydantic import BaseModel, ConfigDict


class ClinicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    config: dict


class ClinicDataConfig(BaseModel):
    """Seção "Dados da clínica" dentro de `clinics.config`."""

    cnpj: str | None = None
    razao_social: str | None = None
    endereco: str | None = None
    telefone: str | None = None
    logo_url: str | None = None


class DayHours(BaseModel):
    closed: bool = False
    start: str = "09:00"
    end: str = "18:00"
    lunch_start: str | None = None
    lunch_end: str | None = None


class WorkingHoursConfig(BaseModel):
    """Seção "Horários" — uma entrada por dia da semana (chaves em inglês,
    consumidas por `scheduling.service._working_hours_for_day`)."""

    mon: DayHours | None = None
    tue: DayHours | None = None
    wed: DayHours | None = None
    thu: DayHours | None = None
    fri: DayHours | None = None
    sat: DayHours | None = None
    sun: DayHours | None = None


class PreferencesConfig(BaseModel):
    """Seção "Preferências" — hoje só o toggle de lembretes de consulta."""

    reminders_enabled: bool = False


class ClinicConfig(BaseModel):
    """Estrutura completa de `clinics.config` (JSONB). Cada seção da tela de
    Configurações grava a sua própria chave; o service faz merge raso."""

    clinic_data: ClinicDataConfig | None = None
    working_hours: WorkingHoursConfig | None = None
    preferences: PreferencesConfig | None = None


class ClinicUpdate(BaseModel):
    nome: str | None = None
    config: ClinicConfig | None = None
