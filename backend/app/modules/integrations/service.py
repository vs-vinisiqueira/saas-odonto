"""Casos de uso das integrações por clínica.

Responsabilidades:
- Ler o status de cada integração SEM vazar segredos (só dicas mascaradas).
- Gravar credenciais cifrando os segredos (preserva os não reenviados).
- `load_credentials`: usado pelo runtime (agente, billing, calendário) para
  obter as credenciais decifradas de uma clínica — ou None se não configurada.

Segurança: os tokens vão cifrados (core/crypto) em `secrets_encrypted`; a API
nunca devolve o valor em claro. Tudo escopado por clinic_id (RLS).
"""
import logging
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crypto
from app.modules.integrations import constants, repository
from app.modules.integrations.models import ClinicIntegration
from app.modules.integrations.schemas import IntegrationOut, IntegrationUpdate
from app.shared.exceptions import Conflict, NotFound

logger = logging.getLogger("integrations.service")


def _mask(value: str) -> str:
    v = (value or "").strip()
    if len(v) <= 4:
        return "••••"
    return "••••" + v[-4:]


def _is_configured(provider: str, public_config: dict, secrets: dict) -> bool:
    merged = {**public_config, **secrets}
    return all(str(merged.get(f, "")).strip() for f in constants.required_fields(provider))


def _to_out(provider: str, row: ClinicIntegration | None) -> IntegrationOut:
    public_config = dict(row.public_config) if row and row.public_config else {}
    secrets = crypto.decrypt_dict(row.secrets_encrypted) if row else {}
    # Só exibe os campos públicos conhecidos do provedor (evita vazar lixo).
    public_view = {f: public_config.get(f) for f in constants.public_fields(provider) if f in public_config}
    hints = {f: _mask(secrets[f]) for f in constants.secret_fields(provider) if secrets.get(f)}
    return IntegrationOut(
        provider=provider,
        label=constants.label(provider),
        enabled=bool(row.enabled) if row else False,
        configured=_is_configured(provider, public_config, secrets),
        public_config=public_view,
        secret_hints=hints,
        secret_fields=constants.secret_fields(provider),
        public_fields=constants.public_fields(provider),
        required_fields=constants.required_fields(provider),
    )


async def list_integrations(
    session: AsyncSession, clinic_id: uuid.UUID | str
) -> list[IntegrationOut]:
    rows = {r.provider: r for r in await repository.list_all(session, clinic_id)}
    return [_to_out(p, rows.get(p)) for p in constants.PROVIDERS]


async def get_integration(
    session: AsyncSession, clinic_id: uuid.UUID | str, provider: str
) -> IntegrationOut:
    if not constants.is_valid_provider(provider):
        raise NotFound("Integração não encontrada")
    row = await repository.get(session, clinic_id, provider)
    return _to_out(provider, row)


async def update_integration(
    session: AsyncSession,
    clinic_id: uuid.UUID | str,
    provider: str,
    data: IntegrationUpdate,
) -> IntegrationOut:
    if not constants.is_valid_provider(provider):
        raise NotFound("Integração não encontrada")

    row = await repository.get(session, clinic_id, provider)
    if row is None:
        row = ClinicIntegration(
            clinic_id=clinic_id, provider=provider, public_config={}, enabled=False
        )
        await repository.add(session, row)

    # Merge dos segredos: campo em branco/ausente preserva o valor já gravado.
    secrets = crypto.decrypt_dict(row.secrets_encrypted)
    for field in constants.secret_fields(provider):
        if field in data.secrets:
            value = (data.secrets[field] or "").strip()
            if value:
                secrets[field] = value
    row.secrets_encrypted = crypto.encrypt_dict(secrets) if secrets else None

    # Merge da config pública (só campos conhecidos do provedor).
    public_config = dict(row.public_config or {})
    for field in constants.public_fields(provider):
        if field in data.public_config:
            value = data.public_config[field]
            if value in (None, ""):
                public_config.pop(field, None)
            else:
                public_config[field] = value
    row.public_config = public_config  # reatribui para o SQLAlchemy detectar a mudança

    if data.enabled is not None:
        row.enabled = data.enabled

    # Efeito colateral do WhatsApp: o webhook (sem tenant) descobre a clínica pelo
    # phone_number_id via whatsapp_numbers. Mantemos esse roteamento em sincronia.
    if provider == constants.WHATSAPP:
        phone_number_id = public_config.get("phone_number_id")
        if phone_number_id:
            await _sync_whatsapp_number(session, clinic_id, str(phone_number_id))

    await session.flush()
    return _to_out(provider, row)


async def disconnect(
    session: AsyncSession, clinic_id: uuid.UUID | str, provider: str
) -> IntegrationOut:
    if not constants.is_valid_provider(provider):
        raise NotFound("Integração não encontrada")
    row = await repository.get(session, clinic_id, provider)
    if row is not None:
        row.enabled = False
        row.secrets_encrypted = None
        await session.flush()
    return _to_out(provider, row)


async def load_credentials(
    session: AsyncSession, clinic_id: uuid.UUID | str, provider: str
) -> dict | None:
    """Credenciais decifradas (segredos + config pública) de uma clínica para
    uso em runtime. Retorna None se a integração não existe, está desligada ou
    incompleta — nesse caso o chamador cai no padrão global/mock."""
    row = await repository.get(session, clinic_id, provider)
    if row is None or not row.enabled:
        return None
    public_config = dict(row.public_config or {})
    secrets = crypto.decrypt_dict(row.secrets_encrypted)
    if not _is_configured(provider, public_config, secrets):
        return None
    return {**public_config, **secrets}


async def _sync_whatsapp_number(
    session: AsyncSession, clinic_id: uuid.UUID | str, phone_number_id: str
) -> None:
    from app.modules.whatsapp import repository as whatsapp_repo

    try:
        await whatsapp_repo.get_or_create(session, clinic_id, phone_number_id)
    except IntegrityError:
        raise Conflict(
            "Esse phone_number_id já está registrado em outra clínica."
        )
