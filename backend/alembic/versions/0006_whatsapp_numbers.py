"""whatsapp_numbers table + RLS + funcao de resolucao do tenant pelo phone_number_id

Revision ID: 0006_whatsapp_numbers
Revises: 0005_payments
Create Date: 2026-06-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_whatsapp_numbers"
down_revision: Union[str, None] = "0005_payments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


POST_STATEMENTS = [
    "ALTER TABLE whatsapp_numbers ENABLE ROW LEVEL SECURITY",
    """
    CREATE POLICY tenant_isolation ON whatsapp_numbers
        USING (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
        WITH CHECK (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
    """,
    # O webhook da Meta chega SEM tenant. Esta função (SECURITY DEFINER, roda como
    # o dono das tabelas, que ignora o RLS) resolve a clínica pelo phone_number_id.
    """
    CREATE OR REPLACE FUNCTION whatsapp_clinic_for_number(p_phone_number_id text)
    RETURNS uuid
    LANGUAGE sql
    SECURITY DEFINER
    SET search_path = public
    AS $$
        SELECT clinic_id FROM whatsapp_numbers WHERE phone_number_id = p_phone_number_id;
    $$
    """,
    "REVOKE ALL ON FUNCTION whatsapp_clinic_for_number(text) FROM PUBLIC",
    "GRANT EXECUTE ON FUNCTION whatsapp_clinic_for_number(text) TO app_user",
]


def upgrade() -> None:
    op.create_table(
        "whatsapp_numbers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone_number_id", sa.String(64), nullable=False),
        sa.Column("label", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("phone_number_id", name="uq_whatsapp_numbers_phone_number_id"),
    )
    op.create_index("ix_whatsapp_numbers_clinic_id", "whatsapp_numbers", ["clinic_id"])
    for stmt in POST_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS whatsapp_clinic_for_number(text)")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON whatsapp_numbers")
    op.execute("ALTER TABLE whatsapp_numbers DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_whatsapp_numbers_clinic_id", table_name="whatsapp_numbers")
    op.drop_table("whatsapp_numbers")
