# Tenant isolation

PostgreSQL forces row-level security for operational tenant tables. A transaction-local setting comes from the authenticated principal, and queries bind the tenant explicitly. SQLite fallback has application isolation. Run cross-tenant read tests under the non-superuser PostgreSQL app role after schema changes.
