# YUKTI Research Intelligence

YUKTI collects evidence from primary sources and helps a private editorial team produce SUTRA, a weekly English research magazine. SUTRA covers AI, data engineering, finance, mathematical modeling and research papers. Every brief has What, When, Why and Context, Action, Result sections plus an original-source citation. The portal labels preprints and peer-reviewed publications explicitly.

[Project walkthrough with architecture, flow, and screenshots](docs/YUKTI_SUTRA_WALKTHROUGH.md)

## Start locally

Install Docker with Compose v2, Python 3.12 and a browser. Install uv for locked development commands. From an unzipped repository:

```bash
python3 scripts/setup/init_env.py
docker compose up -d --build --wait
docker compose exec api python -m scripts.maintenance.yukti seed
docker compose exec api python -m scripts.maintenance.yukti collect
docker compose exec api python -m scripts.maintenance.yukti validate
```

| Application | Local URL |
| --- | --- |
| Sample magazine portal | http://localhost:8000/portal/ |
| Research dashboard | http://localhost:8000/dashboard/ |
| Editorial console | http://localhost:8000/console/ |
| Authenticated SUTRA archive | http://localhost:8000/sutra/ |
| Swagger API | http://localhost:8000/docs |
| Keycloak administration | http://localhost:8081/ |

The portal opens immediately with three sample archive issues and a preview PDF. The other applications use Keycloak. Read [operations](docs/operations/README.md) to create users and configure roles. The Keycloak import contains no users or passwords. The tenant `demo` matches the seed command and local scheduler. Run the following for a separate editor account, or use the Keycloak administration UI:

```bash
uv sync --locked
uv run --locked python -m scripts.setup.create_local_users --user editor-local --role editor
```

Repeat for curator, approver, publisher and reader with distinct account names. The editor reviews drafts and confirms their sources. Open the preview before approving the matching checksum. A different publisher can then release the frozen PDF to the authenticated tenant archive.

### Scheduler, AI and bulk processing

```bash
docker compose --profile scheduler up -d --build
docker compose --profile ai up -d
docker compose exec ollama ollama pull qwen2.5:1.5b
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec api python -m scripts.maintenance.yukti index
docker compose --profile monitoring up -d
```

Open Airflow at port 8080 and unpause all five YUKTI and SUTRA DAGs listed in the [operations guide](docs/operations/README.md). SUTRA draft generation is scheduled at 06:00 every Sunday in Asia/Kolkata. It uses previously reviewed briefs. The scheduler has no release permission. Ollama is optional for summaries and embeddings. Semantic suggestions remain subject to editorial review.

Install Java 21 on the host to run bulk tests alongside the local Python environment.

```bash
uv sync --locked --group spark
uv run --locked --group spark python -m scripts.maintenance.yukti spark data/samples/analytics.jsonl var/analytics
make test-spark
docker compose --profile scheduler --profile ai --profile monitoring down
```

### Run API without Docker

Install Pango, HarfBuzz and DejaVu fonts using the OS package manager, then run:

```bash
uv sync --locked
uv run --locked python -m scripts.maintenance.yukti migrate
uv run --locked python -m scripts.maintenance.yukti seed
uv run --locked python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

The standalone path defaults to SQLite. Set `DATABASE_URL`, `OIDC_ISSUER`, `OIDC_JWKS_URL` and `LANGUAGETOOL_URL` to connect installed services. Signed-in endpoints require Keycloak. The proof-of-concept hosted URL serves the private sample website. The database-backed console and scheduler run locally.

## Repository guide

| Path | Purpose |
| --- | --- |
| apps | Portal, dashboard, API, editorial console and SUTRA reader |
| packages | Business rules, typed records, workflows and interfaces |
| adapters | PostgreSQL, object storage, Iceberg, Spark, search, vectors, Ollama, Keycloak, language, messaging and PDF |
| workers and workflows | Collection, validation, AI, layout, release and Airflow |
| database and config | Migrations, local fixtures and explicit policies |
| templates | Navy-and-gold cover and A4 issue layout |
| infrastructure and security | Images, Compose, identity, monitoring and security model |
| tests and docs | Automated tests, setup and operating references |
| docx | YUKTI and SUTRA platform handbook |

Start with [Architecture](docs/architecture/README.md), [API](docs/api/README.md), [Governance](docs/data-governance/README.md), [Operations](docs/operations/README.md), [Roadmap](docs/roadmap.md) and [Test report](TEST_REPORT.md). Choose an appropriate license before any public redistribution. The included license is preserved from the original MVP.

## Verify the repository

Run `make check test pdf` to validate the agreed directory tree, pinned configuration, local tests and a seven-page sample preview. The profile-specific and native-service checks are recorded in TEST_REPORT.md. The release workflow is manually triggered and packages a private Actions artifact. It never opens the hosted portal to the public.
