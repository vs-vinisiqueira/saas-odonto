"""row-level security policies + auth lookup function

Revision ID: 0002_rls_policies
Revises: 0001_initial
Create Date: 2026-06-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_rls_policies"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Cada item é UM único comando SQL. O driver asyncpg não aceita múltiplos
# comandos num mesmo prepared statement, por isso executamos um a um.
# NOTA: NÃO usamos `FORCE ROW LEVEL SECURITY`. Sem FORCE, o RLS vale para todos
# os roles EXCETO o DONO das tabelas. Isso é proposital e essencial fora do
# Postgres local: provedores gerenciados como o Neon não têm superusuário, então
# o admin é apenas o dono das tabelas — e precisa ignorar o RLS para rodar
# migrations, o seed e a função de login (SECURITY DEFINER). A aplicação conecta
# pelo role `app_user` (NÃO-dono), que continua totalmente sujeito ao RLS.
UPGRADE_STATEMENTS = [
    # RLS na tabela clinics (a chave do tenant é a própria coluna id)
    "ALTER TABLE clinics ENABLE ROW LEVEL SECURITY",
    """
    CREATE POLICY tenant_isolation ON clinics
        USING (id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
        WITH CHECK (id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
    """,
    # RLS na tabela users (escopo por clinic_id)
    "ALTER TABLE users ENABLE ROW LEVEL SECURITY",
    """
    CREATE POLICY tenant_isolation ON users
        USING (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
        WITH CHECK (clinic_id = NULLIF(current_setting('app.current_clinic', true), '')::uuid)
    """,
    # Função SECURITY DEFINER: o login acha o usuário por e-mail SEM contexto de
    # tenant. Roda como o DONO das tabelas, que (sem FORCE) ignora o RLS.
    """
    CREATE OR REPLACE FUNCTION auth_find_user_by_email(p_email text)
    RETURNS TABLE (
        id uuid,
        clinic_id uuid,
        email text,
        password_hash text,
        role text,
        is_active boolean
    )
    LANGUAGE sql
    SECURITY DEFINER
    SET search_path = public
    AS $$
        SELECT id, clinic_id, email::text, password_hash::text, role::text, is_active
        FROM users
        WHERE email = p_email;
    $$
    """,
    "REVOKE ALL ON FUNCTION auth_find_user_by_email(text) FROM PUBLIC",
    "GRANT EXECUTE ON FUNCTION auth_find_user_by_email(text) TO app_user",
]

DOWNGRADE_STATEMENTS = [
    "DROP FUNCTION IF EXISTS auth_find_user_by_email(text)",
    "DROP POLICY IF EXISTS tenant_isolation ON users",
    "DROP POLICY IF EXISTS tenant_isolation ON clinics",
    "ALTER TABLE users DISABLE ROW LEVEL SECURITY",
    "ALTER TABLE clinics DISABLE ROW LEVEL SECURITY",
]


def upgrade() -> None:
    for stmt in UPGRADE_STATEMENTS:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in DOWNGRADE_STATEMENTS:
        op.execute(stmt)
