#!/usr/bin/env bash
set -euo pipefail
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=db_password="$DB_APP_PASSWORD" <<'SQL'
CREATE ROLE yukti_app LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD :'db_password';
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO yukti_app;
SQL
