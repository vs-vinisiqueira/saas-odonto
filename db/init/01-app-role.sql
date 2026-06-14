-- Executado automaticamente pelo Postgres na PRIMEIRA inicialização do volume
-- (diretório /docker-entrypoint-initdb.d). Roda como o superusuário POSTGRES_USER.
--
-- Cria o role da aplicação: NÃO é superusuário e NÃO é dono das tabelas,
-- portanto fica SUJEITO ao Row-Level Security. As migrations e o seed rodam
-- como superusuário (postgres), que ignora o RLS de propósito.

-- A senha é interpolada a partir de APP_DB_PASSWORD via o script de entrypoint
-- do container (ver docker-compose). Aqui usamos um placeholder padrão de dev.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user LOGIN PASSWORD 'app_password';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE saas_odonto TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;

-- Privilégios em objetos FUTUROS criados pelo superusuário (as migrations):
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO app_user;
