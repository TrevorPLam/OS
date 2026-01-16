# Meta-commentary:
# - Current Status: Defines backend developer commands (lint/test/typecheck) used by top-level Makefile targets.
# - Mapping: `test-performance` runs performance-marked tests from repo root to share pytest.ini settings.
# - Reasoning: Keep backend commands scoped and re-usable by CI/local workflows.
# - Assumption: Running from /src requires explicit test path to reuse repo-root pytest config.
# - Limitation: Performance runs bypass repo addopts to avoid coverage flags in minimal environments.
SHELL := /bin/bash
.ONESHELL:

Q := @
ifneq ($(V),1)
Q := @
else
Q :=
endif

PYTHON ?= python
OPENAPI_PATH := ../docs/03-reference/api/openapi.yaml
OPENAPI_ENV := DJANGO_SECRET_KEY=local POSTGRES_DB=local POSTGRES_USER=local POSTGRES_PASSWORD=local POSTGRES_HOST=localhost USE_SQLITE_FOR_TESTS=True

.PHONY: setup lint test test-performance typecheck migrate openapi dev fixtures

setup:
	$(Q)$(PYTHON) -m pip install --upgrade pip
	$(Q)$(PYTHON) -m pip install -r ../requirements.txt

lint:
	$(Q)ruff check . --select=E9,F63,F7,F82
	$(Q)ruff check . --statistics
	$(Q)black --check . --line-length=120

test:
	$(Q)pytest --cov=modules --cov=api --cov-report=term -v

test-performance:
	$(Q)pytest -m performance -v -o addopts= ../tests

typecheck:
	$(Q)mypy .

migrate:
	$(Q)$(PYTHON) manage.py migrate --noinput

fixtures:
	$(Q)$(PYTHON) manage.py load_fixtures

openapi:
	$(Q)mkdir -p $(dir $(OPENAPI_PATH))
	$(Q)$(OPENAPI_ENV) $(PYTHON) manage.py spectacular --file $(OPENAPI_PATH)

# dev relies on local env configuration (DATABASE, AWS, Stripe). Update .env as needed.
dev:
	$(Q)$(PYTHON) manage.py runserver
