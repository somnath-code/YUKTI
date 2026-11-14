# Local service images

The root compose.yaml builds the API, Airflow and LanguageTool from this directory. Docker build context is the repository root. The LanguageTool image verifies the upstream ZIP against its pinned SHA-256 before extraction. The database bootstrap script creates a local non-superuser service role. Manage local volumes through Compose as described in docs/operations.

The API image installs the runtime export of uv.lock. Regenerate it with `uv export --locked --no-dev --no-hashes --no-emit-project --no-header --quiet -o infrastructure/local/docker/requirements-runtime.lock`. The pinned worker requirements are the subset used to extend the official Airflow base image.
