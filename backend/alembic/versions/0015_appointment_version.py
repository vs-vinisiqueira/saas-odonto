"""appointments.version (locking otimista)

Revision ID: 0015_appointment_version
Revises: 0014_appointments_schedule_index
Create Date: 2026-07-06

Coluna gerenciada pelo SQLAlchemy (`version_id_col`). Fecha o *lost update* na
edição concorrente de um agendamento: dois atendentes que carregam a mesma linha
e salvam — o segundo UPDATE casa 0 linhas (WHERE version=<lido>) e o ORM levanta
StaleDataError, que o service traduz para 409. A sobreposição de horário já é
coberta pelo EXCLUDE (0012); isto cobre a edição concorrente dos demais campos.

`server_default='1'` faz o backfill das linhas existentes; em INSERTs novos o
próprio ORM define version=1 explicitamente.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015_appointment_version"
down_revision: Union[str, None] = "0014_appointments_schedule_index"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "appointments",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("appointments", "version")
