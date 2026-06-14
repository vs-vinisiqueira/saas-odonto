"""patients table + RLS

Revision ID: 0003_patients
Revises: 0002_rls_policies
Create Date: 2026-06-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_patients"
down_revision: Union[str, None] = "0002_rls_policies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# RLS escopado por clinic_id (mesmo padrão da migration 0002). Sem FORCE: o dono
# das tabelas (admin/Neon) ignora o RLS; a aplicação (app_user) fica sujeita a ele.
RLS_STATEMENTS = [
    "ALTER TABLE patients ENABLE ROW LEVEL SECURITY",
    """
    CREATE POLICY tenant_isolation ON patients
        USING (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
        WITH CHECK (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
    """,
]


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("telefone", sa.String(32), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_patients_clinic_id", "patients", ["clinic_id"])
    op.create_index("ix_patients_telefone", "patients", ["telefone"])
    for stmt in RLS_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON patients")
    op.execute("ALTER TABLE patients DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_patients_telefone", table_name="patients")
    op.drop_index("ix_patients_clinic_id", table_name="patients")
    op.drop_table("patients")
