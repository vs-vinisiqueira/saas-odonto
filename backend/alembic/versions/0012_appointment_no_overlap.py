"""constraint anti-overlap de agendamentos (EXCLUDE gist)

Revision ID: 0012_appointment_no_overlap
Revises: 0011_appointment_tipo
Create Date: 2026-07-01

Fecha a race condition do check-then-act (find_conflict + INSERT): dois pedidos
concorrentes para o mesmo horário passavam os dois pela checagem e inseriam
agendamentos sobrepostos. A constraint EXCLUDE (via btree_gist) garante no BANCO
que dois agendamentos ATIVOS do mesmo dentista não podem se sobrepor no tempo —
independente de concorrência.

Observação: linhas com `dentist_id` NULL não entram na constraint (regra do
EXCLUDE, como no UNIQUE) — o conflito "sem dentista" (clínica inteira) continua
sendo tratado na aplicação (`repository.find_conflict`).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0012_appointment_no_overlap"
down_revision: Union[str, None] = "0011_appointment_tipo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UPGRADE_STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS btree_gist",
    """
    ALTER TABLE appointments
        ADD CONSTRAINT appointments_no_overlap
        EXCLUDE USING gist (
            clinic_id WITH =,
            dentist_id WITH =,
            tstzrange(starts_at, ends_at) WITH &&
        ) WHERE (status IN ('scheduled', 'confirmed'))
    """,
]


def upgrade() -> None:
    for stmt in UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    op.execute("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_no_overlap")
    # Não removemos a extensão btree_gist: pode estar em uso por outros objetos.
