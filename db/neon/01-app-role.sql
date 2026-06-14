-- ===========================================================================
-- Neon: criação do role da aplicação (app_user)
-- ===========================================================================
-- O Neon NÃO executa o /docker-entrypoint-initdb.d (isso é só do Postgres em
-- container). Então, ao usar o Neon, rode este script UMA vez no SQL Editor do
-- Neon (já conectado ao banco do seu projeto), ANTES de aplicar as migrations.
--
-- O SQL Editor conecta como o role DONO do projeto. As migrations (Alembic) e o
-- seed também usam esse mesmo role dono (ADMIN_DATABASE_URL) — por isso o
-- ALTER DEFAULT PRIVILEGES abaixo cobre as tabelas que as migrations criarão.
--
-- IMPORTANTE: troque 'TROQUE_ESTA_SENHA' pela MESMA senha que você colocar em
-- APP_DB_PASSWORD / no usuário do DATABASE_URL no seu .env.
-- ===========================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user LOGIN PASSWORD 'TROQUE_ESTA_SENHA';
    END IF;
END
$$;

-- (CONNECT no banco já vem do PUBLIC por padrão; não precisa conceder.)
GRANT USAGE ON SCHEMA public TO app_user;

-- Privilégios em tabelas/sequences FUTURAS criadas pelo dono (as migrations):
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO app_user;

-- Caso você rode este script DEPOIS de já ter criado as tabelas, descomente:
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
