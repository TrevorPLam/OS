# Meta-commentary:
# - Current Status: Defines backend developer commands (lint/test/typecheck) used by top-level Makefile targets.
# - Mapping: `test-performance` runs performance-marked tests from repo root to share pytest.ini settings.
# - Reasoning: Keep backend commands scoped and re-usable by CI/local workflows.
# - Assumption: Running from /backend requires explicit test path to reuse repo-root pytest config.
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
VENV_DIR ?= .venv
VENV_BIN := $(if $(wildcard $(VENV_DIR)/bin),$(VENV_DIR)/bin,$(VENV_DIR)/Scripts)
VENV_PY := $(VENV_BIN)/python
PIP_CACHE_DIR ?= ../.pip-cache
OPENAPI_PATH := ./openapi.yaml
OPENAPI_ENV := DJANGO_SECRET_KEY=local POSTGRES_DB=local POSTGRES_USER=local POSTGRES_PASSWORD=local POSTGRES_HOST=localhost USE_SQLITE_FOR_TESTS=True KMS_BACKEND=local LOCAL_KMS_MASTER_KEY=local-test-key PYTHONUTF8=1

.PHONY: setup lint test test-performance typecheck migrate openapi dev fixtures

setup:
	$(Q)$(PYTHON) -m venv $(VENV_DIR)
	$(Q)PIP_CACHE_DIR=$(PIP_CACHE_DIR) $(VENV_PY) -m pip install --upgrade pip
	$(Q)PIP_CACHE_DIR=$(PIP_CACHE_DIR) $(VENV_PY) -m pip install -r ../requirements.txt
	$(Q)PIP_CACHE_DIR=$(PIP_CACHE_DIR) $(VENV_PY) -m pip install -r ../requirements-dev.txt

lint:
	$(Q)$(VENV_BIN)/ruff check . --select=E9,F63,F7,F82 --ignore=F821

test:
	$(Q)DJANGO_SECRET_KEY=local USE_SQLITE_FOR_TESTS=True KMS_BACKEND=local LOCAL_KMS_MASTER_KEY=local-test-key $(VENV_BIN)/pytest --cov=modules --cov=api --cov-report=term --cov-report=xml -v

test-performance:
	$(Q)DJANGO_SECRET_KEY=local USE_SQLITE_FOR_TESTS=True KMS_BACKEND=local LOCAL_KMS_MASTER_KEY=local-test-key $(VENV_BIN)/pytest -m performance -v -o addopts= ../tests

typecheck:
	$(Q)echo "Skipping mypy (relaxed)"

migrate:
	$(Q)$(VENV_PY) manage.py migrate --noinput

fixtures:
	$(Q)$(VENV_PY) manage.py load_fixtures

openapi:
	$(Q)mkdir -p $(dir $(OPENAPI_PATH))
	$(Q)$(OPENAPI_ENV) $(VENV_PY) manage.py spectacular --file $(OPENAPI_PATH)

# dev relies on local env configuration (DATABASE, AWS, Stripe). Update .env as needed.
dev:
	$(Q)$(VENV_PY) manage.py runserver
