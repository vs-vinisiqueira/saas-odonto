"""payments table + RLS + funcao de resolucao do tenant pelo charge_id

Revision ID: 0005_payments
Revises: 0004_appointments
Create Date: 2026-06-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_payments"
down_revision: Union[str, None] = "0004_appointments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


POST_STATEMENTS = [
    "ALTER TABLE payments ENABLE ROW LEVEL SECURITY",
    """
    CREATE POLICY tenant_isolation ON payments
        USING (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
        WITH CHECK (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
    """,
    # O webhook do provedor chega SEM tenant. Esta função (SECURITY DEFINER, roda
    # como o dono das tabelas, que ignora o RLS) resolve a clínica pelo charge_id.
    """
    CREATE OR REPLACE FUNCTION billing_clinic_for_charge(p_charge_id text)
    RETURNS uuid
    LANGUAGE sql
    SECURITY DEFINER
    SET search_path = public
    AS $$
        SELECT clinic_id FROM payments WHERE charge_id = p_charge_id;
    $$
    """,
    "REVOKE ALL ON FUNCTION billing_clinic_for_charge(text) FROM PUBLIC",
    "GRANT EXECUTE ON FUNCTION billing_clinic_for_charge(text) TO app_user",
]


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=True),
        sa.Column("metodo", sa.String(16), server_default="pix", nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("charge_id", sa.String(64), nullable=False),
        sa.Column("qr_code", sa.Text(), nullable=True),
        sa.Column("qr_code_base64", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("charge_id", name="uq_payments_charge_id"),
    )
    op.create_index("ix_payments_clinic_id", "payments", ["clinic_id"])
    for stmt in POST_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS billing_clinic_for_charge(text)")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON payments")
    op.execute("ALTER TABLE payments DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_payments_clinic_id", table_name="payments")
    op.drop_table("payments")
