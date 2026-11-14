UV ?= uv
COMPOSE ?= docker compose
PYTHON ?= python3
PROFILES = --profile scheduler --profile ai --profile monitoring
.PHONY: setup check test test-spark pdf up down seed verify-structure

setup:
	$(UV) sync --locked

verify-structure:
	$(UV) run --locked python -m scripts.verification.structure

check: verify-structure
	$(UV) run --locked python -m compileall -q apps packages adapters workers workflows scripts

test:
	$(UV) run --locked python -m pytest -q

test-spark:
	YUKTI_TEST_SPARK=1 $(UV) run --locked --group spark python -m pytest -q tests/integration

pdf:
	$(UV) run --locked python -m scripts.publishing.render_sample

up:
	test -f .env || $(PYTHON) scripts/setup/init_env.py
	$(COMPOSE) up --build -d --wait

down:
	$(COMPOSE) $(PROFILES) down

seed:
	$(COMPOSE) exec api python -m scripts.maintenance.yukti seed
	$(COMPOSE) exec api python -m scripts.maintenance.yukti collect
	$(COMPOSE) exec api python -m scripts.maintenance.yukti validate
