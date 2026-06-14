"""appointments table + RLS

Revision ID: 0004_appointments
Revises: 0003_patients
Create Date: 2026-06-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_appointments"
down_revision: Union[str, None] = "0003_patients"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


RLS_STATEMENTS = [
    "ALTER TABLE appointments ENABLE ROW LEVEL SECURITY",
    """
    CREATE POLICY tenant_isolation ON appointments
        USING (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
        WITH CHECK (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
    """,
]


def upgrade() -> None:
    op.create_table(
        "appointments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dentist_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), server_default="scheduled", nullable=False),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dentist_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_appointments_clinic_id", "appointments", ["clinic_id"])
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_dentist_id", "appointments", ["dentist_id"])
    op.create_index("ix_appointments_starts_at", "appointments", ["starts_at"])
    for stmt in RLS_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON appointments")
    op.execute("ALTER TABLE appointments DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_appointments_starts_at", table_name="appointments")
    op.drop_index("ix_appointments_dentist_id", table_name="appointments")
    op.drop_index("ix_appointments_patient_id", table_name="appointments")
    op.drop_index("ix_appointments_clinic_id", table_name="appointments")
    op.drop_table("appointments")
