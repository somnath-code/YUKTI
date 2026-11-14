# Production deployment contract

Define availability, isolation, retention and recovery objectives before selecting infrastructure. Provision TLS and a managed secrets store, an independently owned schema and migration role, a restricted app database role, versioned artifacts, rate limits and a separate Airflow metastore. Run approval tests against the tenant archive. The local Compose deployment serves a single development host. Production deployments, traffic shifts and incident drills remain future work.
