"""garante GRANTs do role app_user em todas as tabelas/sequences

Revision ID: 0009_grant_app_user
Revises: 0008_users_profile
Create Date: 2026-06-22

Contexto: em provedores como o Neon, o `ALTER DEFAULT PRIVILEGES` rodado no SQL
Editor pode ser registrado por um role diferente do dono que as migrations usam
(neondb_owner), e então NÃO se aplica às tabelas criadas pelas migrations. O
resultado é `permission denied for table ...` quando a aplicação (app_user)
faz SELECT direto — o login mascara isso por usar uma função SECURITY DEFINER.

Esta migration roda como o MESMO dono das migrations e concede os privilégios
explicitamente (idempotente). Só age se o role app_user existir, para não
quebrar ambientes que não o tenham.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0009_grant_app_user"
down_revision: Union[str, None] = "0008_users_profile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


GRANT_BLOCK = """
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        EXECUTE 'GRANT USAGE ON SCHEMA public TO app_user';
        EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user';
        EXECUTE 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user';
        EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user';
        EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO app_user';
    END IF;
END
$$;
"""


def upgrade() -> None:
    op.execute(GRANT_BLOCK)


def downgrade() -> None:
    # Não revogamos: remover privilégios da app em rollback quebraria o runtime.
    pass
