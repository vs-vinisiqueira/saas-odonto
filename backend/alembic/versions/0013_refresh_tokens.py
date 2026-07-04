"""refresh_tokens: rotação e revogação de refresh token

Revision ID: 0013_refresh_tokens
Revises: 0012_appointment_no_overlap
Create Date: 2026-07-01

Guarda um registro por refresh token emitido (identificado pelo claim `jti`),
para permitir rotação (invalidar o token anterior a cada refresh), revogação
(logout, reset de senha) e detecção de reuso (token já rotacionado sendo usado
de novo => possível roubo => revoga todos os do usuário).

SEM RLS: o refresh acontece ANTES de haver contexto de tenant (igual ao login,
que usa a função SECURITY DEFINER `auth_find_user_by_email`). A validação é por
`jti` (uuid aleatório), não enumerável; a tabela guarda só jti/user/timestamps,
nenhum segredo. O `app_user` recebe os grants explicitamente (pegadinha do Neon:
a 0009 rodou antes desta tabela existir).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_refresh_tokens"
down_revision: Union[str, None] = "0012_appointment_no_overlap"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


GRANT_BLOCK = """
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON refresh_tokens TO app_user';
    END IF;
END
$$;
"""


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("jti", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.execute(GRANT_BLOCK)


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
