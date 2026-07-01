"""appointments.tipo (tipo da consulta)

Revision ID: 0011_appointment_tipo
Revises: 0010_clinic_integrations
Create Date: 2026-07-01

Campo livre (não enum de banco, para facilitar evolução) usado pelo frontend
para colorir a grade da agenda por tipo de consulta (avaliação, limpeza,
restauração, canal, clareamento, cirurgia). Default "avaliacao" para não
quebrar agendamentos já existentes.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_appointment_tipo"
down_revision: Union[str, None] = "0010_clinic_integrations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "appointments",
        sa.Column(
            "tipo", sa.String(30), nullable=False, server_default="avaliacao"
        ),
    )


def downgrade() -> None:
    op.drop_column("appointments", "tipo")
