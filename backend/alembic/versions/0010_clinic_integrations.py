"""clinic_integrations table + RLS + grants

Revision ID: 0010_clinic_integrations
Revises: 0009_grant_app_user
Create Date: 2026-06-23

Guarda, por clínica, a configuração de cada integração externa (WhatsApp,
Mercado Pago, Google Calendar, IA). Os segredos (tokens de API) ficam em
`secrets_encrypted` CIFRADOS (Fernet, ver core/crypto.py) — nunca em claro. Os
campos não-secretos (modelo da IA, calendar_id, phone_number_id, etc.) vão em
`public_config` (JSONB).

RLS por clinic_id (mesmo padrão das demais tabelas). O GRANT do app_user é
explícito aqui porque a migration 0009 (que concede em massa) já rodou nos
ambientes existentes e não cobre tabelas criadas depois (pegadinha do Neon).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_clinic_integrations"
down_revision: Union[str, None] = "0009_grant_app_user"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


RLS_STATEMENTS = [
    "ALTER TABLE clinic_integrations ENABLE ROW LEVEL SECURITY",
    """
    CREATE POLICY tenant_isolation ON clinic_integrations
        USING (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
        WITH CHECK (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
    """,
]

# Concede ao app_user os privilégios na nova tabela (idempotente; só age se o
# role existir). Necessário porque a 0009 já rodou antes desta tabela existir.
GRANT_BLOCK = """
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON clinic_integrations TO app_user';
    END IF;
END
$$;
"""


def upgrade() -> None:
    op.create_table(
        "clinic_integrations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("secrets_encrypted", sa.Text(), nullable=True),
        sa.Column(
            "public_config",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_clinic_integrations_clinic_id", "clinic_integrations", ["clinic_id"]
    )
    op.create_index(
        "uq_clinic_integrations_clinic_provider",
        "clinic_integrations",
        ["clinic_id", "provider"],
        unique=True,
    )

    for stmt in RLS_STATEMENTS:
        op.execute(stmt)
    op.execute(GRANT_BLOCK)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON clinic_integrations")
    op.execute("ALTER TABLE clinic_integrations DISABLE ROW LEVEL SECURITY")
    op.drop_index(
        "uq_clinic_integrations_clinic_provider", table_name="clinic_integrations"
    )
    op.drop_index(
        "ix_clinic_integrations_clinic_id", table_name="clinic_integrations"
    )
    op.drop_table("clinic_integrations")
