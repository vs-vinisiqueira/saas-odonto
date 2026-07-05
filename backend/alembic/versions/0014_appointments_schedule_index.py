"""índice composto p/ consultas da agenda (clinic_id, dentist_id, starts_at)

Revision ID: 0014_appointments_schedule_index
Revises: 0013_refresh_tokens
Create Date: 2026-07-05

As duas consultas quentes da agenda filtram por `clinic_id` + faixa de tempo:
- `repository.find_conflict` (roda em TODO agendar/reagendar): clinic_id +
  dentist_id + faixa de starts_at/ends_at — caminho crítico de concorrência.
- `repository.list_in_range` (grade do dia/semana): clinic_id + faixa de starts_at,
  com dentist_id opcional.

Num tenant único (uma clínica grande), o índice `ix_appointments_clinic_id` tem
baixa seletividade — quase todas as linhas compartilham o mesmo clinic_id. Este
índice composto permite ao planner casar clinic_id (+ dentist_id no find_conflict)
e fazer range scan por starts_at, acelerando tanto a checagem de conflito quanto a
listagem por dentista. O índice GiST do EXCLUDE (0012) cobre a SOBREPOSIÇÃO, mas
não as comparações btree (`starts_at < :end`) usadas por estas queries.

Observação: a tabela ainda é pequena, então um CREATE INDEX comum (transacional,
dentro da migration) é rápido. Se um dia a tabela crescer a ponto de o lock de
escrita incomodar, trocar por CREATE INDEX CONCURRENTLY (fora de transação).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0014_appointments_schedule_index"
down_revision: Union[str, None] = "0013_refresh_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "ix_appointments_clinic_dentist_start"


def upgrade() -> None:
    op.create_index(
        INDEX_NAME,
        "appointments",
        ["clinic_id", "dentist_id", "starts_at"],
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="appointments")
