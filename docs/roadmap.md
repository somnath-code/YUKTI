# Production scaling

This repository is a single-host reference implementation. Build capacity targets from measured peak reads, write bursts, outstanding PDF jobs, weekday collection volume, daily bytes and Ollama token rates.

| Area | Local implementation | Future work |
| --- | --- | --- |
| API and IAM | One process, Keycloak development mode | Multiple replicas, shared external Keycloak database, HTTPS, rotation, OIDC/session hardening |
| Operational data | PostgreSQL and RLS, connection per transaction | Split schema owner from runtime grants, pooling, replicas, recovery drills |
| Artifacts and lake | Local digest-addressed files, Parquet and Iceberg adapter | Versioned object storage, retention lock, catalog auth, compaction and lifecycle policies |
| Messaging and indexing | Persistent outbox, bounded vector scan | Retrying outbox relay with subscriber dedupe, scalable indexes, backpressure and alerting |
| Airflow | LocalExecutor, standalone metadata for development | Independently managed metastore, workers and job concurrency limits |
| Operations | Liveness and documented backup | Traces, service-level objectives, rate limits, tested failover, disaster recovery and abuse controls |

Workload examples are planning arithmetic. If 5,000 briefs average 4 KB of operational data per day, the payload starts near 20 MB/day before indexes, raw feeds, audit, WAL, vectors, backups or replicas. If every PDF costs five CPU seconds and a burst contains 60 requests per minute, the theoretical work is five CPU cores before variability or headroom. Measure actual processing, disk growth, model memory, p95/p99 latency and queue age before selecting capacity. No multi-user-scale target or availability guarantee is implied by a smoke run.
