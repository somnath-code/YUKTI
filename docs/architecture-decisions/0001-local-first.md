# ADR 0001 Local first

Status is accepted for the current release. Use PostgreSQL for operational records and immutable content-addressed artifacts for exact PDF bytes. Keep the browser, business logic and service integrations separate. Airflow schedules drafts while the database maintains publication state. This keeps the local release reproducible and allows production storage or identity infrastructure to change at adapter boundaries.
