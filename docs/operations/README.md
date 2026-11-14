# Local operations

From the repository root, run `python3 scripts/setup/init_env.py`, then `docker compose up -d --build --wait`. Ports bind to loopback. Use the browser address `http://localhost:8000` for the applications so the Keycloak callback matches the configured client. Keycloak is at `http://localhost:8081`. The bootstrap admin username is `local-admin` and the password is in the generated `.env`. In the yukti realm create distinct users, set their `tenant_id` attribute to `demo`, set passwords and assign realm roles. The local Python helper prompts for secrets and can automate account provisioning.

Seed drafts and collect evidence with `docker compose exec api python -m scripts.maintenance.yukti seed` and `docker compose exec api python -m scripts.maintenance.yukti collect`. Run `validate` for quick inspection. Change `LIVE_FEEDS` to 1 and recreate containers to enable official feed downloads. Initial source coverage is limited to the configured PostgreSQL and arXiv endpoints.

With `docker compose --profile scheduler up -d --build`, open Airflow at `http://localhost:8080`. Find its generated standalone login in `docker compose logs airflow` or the standalone password file in its data volume. Enable the five DAGs below. The draft workflow validates existing evidence and refreshes the editorial queue before rendering. Inspect reruns by logical date. A previously existing weekly draft for that tenant and date is returned as-is.

Enable the optional AI profile with `docker compose --profile ai up -d`. Pull configured models with `docker compose exec ollama ollama pull qwen2.5:1.5b` and `docker compose exec ollama ollama pull nomic-embed-text`, then run `docker compose exec api python -m scripts.maintenance.yukti index`. Prometheus is available at `http://localhost:9090` under the monitoring profile. It scrapes a minimal liveness metric.

Use `docker compose ps` and `docker compose logs --tail=100 api db keycloak languagetool` for startup failures. A 401 often means expired token, issuer mismatch, missing audience or wrong browser hostname. A 403 means the user's role is absent or a reviewer is trying to approve their own issue. A 404 for a draft can be intentional concealment. A grammar 503 means the grammar server is unavailable at its container URL. An unreviewed queue yields no weekly PDF. An invalid layout stops draft creation. The approval gate checks the artifact digest every time. Restore missing artifacts from backup.

Shut down with `docker compose --profile scheduler --profile ai --profile monitoring down` and keep volumes. Snapshot the database with `docker compose exec -T db pg_dump -U postgres -Fc yukti > yukti.dump`. Back up the artifact and Keycloak volumes using your host backup procedure. To restore safely, restore into an isolated database and matching artifact volume, confirm the application role can access its own tenant only, and verify sample PDF digests against the database. Promote restored storage after a smoke test. Use `down -v` only to intentionally erase local data.

For the local Iceberg example, generate the Parquet output first. Download the Apache Iceberg Spark runtime for Spark 4.0 and Scala 2.13 from Maven Central. The example was exercised with Iceberg 1.10.1.

```bash
SPARK_LOCAL_IP=127.0.0.1 python -m scripts.verification.iceberg_smoke \
  --jar /path/to/iceberg-spark-runtime-4.0_2.13-1.10.1.jar \
  --input var/analytics --warehouse var/iceberg
```

Use a fresh warehouse for each smoke run if you want exactly three seeded rows. The adapter appends to an existing table deliberately.

## Airflow schedule

All times use Asia/Kolkata.

| DAG | Time | Result |
| --- | --- | --- |
| yukti_daily_news | Daily 05:00 | Official news snapshots |
| yukti_daily_research | Daily 05:10 | Official research snapshots |
| yukti_quality_validation | Daily 05:25 | Evidence validation and quarantine |
| sutra_weekly_editorial | Sunday 05:45 | Review counts and eligible revisions |
| sutra_draft_weekly | Sunday 06:00 | A private draft PDF for reviewed content |

Set the Airflow DAG folder to workflows/airflow/dags for a native installation. Use a fresh Airflow metadata store when comparing workflow definitions in this release. On an upgrade, pause the retired yukti_collect_daily DAG. The weekly draft DAG retains its existing ID.
