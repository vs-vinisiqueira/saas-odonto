from typing import Any

from pydantic import BaseModel


class IntegrationUpdate(BaseModel):
    """Entrada de PUT /integrations/{provider}.

    `secrets` é write-only: cada campo em branco/ausente PRESERVA o valor já
    gravado (assim o dono pode editar o resto sem redigitar o token). `public_config`
    aceita os campos não-secretos do provedor. Chaves desconhecidas são ignoradas.
    """

    enabled: bool | None = None
    public_config: dict[str, Any] = {}
    secrets: dict[str, str] = {}


class IntegrationOut(BaseModel):
    """Status de uma integração. NUNCA inclui segredos em claro — só dicas
    mascaradas (ex.: '••••1234') para os campos que estão preenchidos."""

    provider: str
    label: str
    enabled: bool
    configured: bool
    public_config: dict[str, Any]
    secret_hints: dict[str, str]
    secret_fields: list[str]
    public_fields: list[str]
    required_fields: list[str]
