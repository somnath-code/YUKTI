# Backup and recovery

Take a database dump with pg_dump and a matching artifact snapshot. Back up the Keycloak database and Airflow metadata volume separately. Store encrypted copies with an access and retention policy that fits the tenant. Restore into an isolated environment before testing sample checksum integrity, database role access, tenant isolation and ability to generate a draft.
