"""users: nome + telefone (perfil)

Revision ID: 0008_users_profile
Revises: 0007_conversations
Create Date: 2026-06-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_users_profile"
down_revision: Union[str, None] = "0007_conversations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable: usuários já existentes (criados pelo seed) não têm esses campos.
    op.add_column("users", sa.Column("nome", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("telefone", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "telefone")
    op.drop_column("users", "nome")
