# YUKTI 1.1 Local Release Verification

Verified on 14 November 2026 using Python 3.12.14, uv 0.13.6, PostgreSQL 16.2, Keycloak 26.4.7, LanguageTool 6.6, Ollama 0.13.1, Spark 4.0.0, Airflow 3.1.8 and WeasyPrint 70.0. The integrations used disposable native services on loopback.

| Check | Observed result |
| --- | --- |
| Requested repository paths | The verifier found every listed directory and named file. It loaded and cross-checked 20 YAML policies. |
| Locked setup | uv sync --locked installed the declared environment. The API image’s runtime export matches uv.lock. |
| Automated tests | 27 passed with the PostgreSQL, LanguageTool, Ollama and Spark integrations enabled. The standalone SQLite run passed 23 tests and skipped four optional integrations. The Airflow schedule test passed separately. |
| Keycloak and API | Six disposable users completed OAuth S256 PKCE. The API verified JWT audience, issuer, tenant and roles. A reader was denied write and administration access. |
| Ingestion and quality | News and research collection parsed their respective fixtures. Tests verified duplicate prevention, tenant isolation, evidence quarantine and recovery, source validation, XML protection and publication types. |
| Search and AI | Native Ollama returned text and embeddings. The authenticated hybrid endpoint retrieved an indexed brief after merging text and vector results. |
| Editorial and private release | Real LanguageTool checked the brief. Separate users reviewed the article, generated the issue, confirmed the PDF hash, approved it and released it to the private test tenant. |
| Airflow | All five DAG test runs succeeded. The Sunday 06:00 Asia/Kolkata run created a four-page draft using reviewed input. It recorded no approval or release. |
| A4 PDF and handbook | The sample is seven pages. Tests checked A4 dimensions, folios, DOI normalisation, numbered citations, corrections links, tags and English metadata. The sample issue and updated 12-page DOCX rendered for a visual check. |
| Packaging and infrastructure syntax | Compose v2.40.3 parsed all profiles. Kustomize built the private API base. Promtool accepted the config and rule. Terraform formatted and downloaded its pinned provider. The provider handshake failed in this runtime, so schema validation remains open. |
| Runtime security and syntax | pip-audit reported no known advisories for the exported runtime dependencies at verification. Python compiled, and shell and JavaScript syntax checks passed. The test client emitted one Starlette HTTPX deprecation warning. |

## Reproduce locally

```bash
uv sync --locked
make check test pdf
```

Set the optional endpoints to disposable services installed on your host. The Compose defaults expose API and Keycloak on loopback. PostgreSQL, LanguageTool and Ollama need native endpoints or explicit test bindings to run the suite from your host.

```bash
YUKTI_TEST_DATABASE='postgresql://yukti_app:LOCAL_PASSWORD@127.0.0.1:5432/yukti' \
YUKTI_TEST_GRAMMAR='http://127.0.0.1:8010/v2/check' \
YUKTI_TEST_OLLAMA='http://127.0.0.1:11434' \
YUKTI_TEST_SPARK=1 uv run --locked --group spark python -m pytest -q
```

For the live auth and editorial smoke, use a disposable realm and workspace. Provide the bootstrap password through the environment. The smoke creates temporary users and releases one issue inside the test tenant.

```bash
export YUKTI_SMOKE_KEYCLOAK=http://localhost:8081
export YUKTI_SMOKE_API=http://localhost:8000
export YUKTI_SMOKE_ADMIN=local-admin
read -rsp 'Disposable Keycloak administrator password: ' YUKTI_QA_KC_ADMIN
export YUKTI_QA_KC_ADMIN
uv run --locked python -m scripts.verification.smoke_live
unset YUKTI_QA_KC_ADMIN
```

## Limits and remaining checks

- Docker Compose configuration passed. This environment had no Docker Engine, so the complete image build, inter-container volumes, full Compose startup, PostgreSQL 17.9 image and Grafana connectivity were not exercised together.
- GitHub Actions, Terraform provider schema validation and live staging/Kubernetes deployment were not run successfully end to end here. Production infrastructure requires an actual target and credentials. Remote S3 enforcement, external outbox relay, alert delivery, production accessibility certification, load and recovery drills remain open.
- Airflow used fixture collection for this verification. The previous release exercised both configured remote feed payloads and the local Iceberg catalog round-trip. The updated suite exercised Spark and Parquet again.
- The private hosted sample portal was already deployed. This ZIP refresh did not deploy any new website changes or modify access. The local portal uses the revised bundled preview. Issue approval and release remain private operational actions.
