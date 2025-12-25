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

.PHONY: setup lint test migrate openapi dev

setup:
	$(Q)$(PYTHON) -m pip install --upgrade pip
	$(Q)$(PYTHON) -m pip install -r ../requirements.txt

lint:
	$(Q)flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	$(Q)flake8 . --count --max-complexity=10 --max-line-length=120 --statistics
	$(Q)black --check . --line-length=120
	$(Q)isort --check-only . --profile black

test:
	$(Q)pytest --cov=modules --cov=api --cov-report=term -v

migrate:
	$(Q)$(PYTHON) manage.py migrate --noinput

openapi:
	$(Q)mkdir -p $(dir $(OPENAPI_PATH))
	$(Q)$(OPENAPI_ENV) $(PYTHON) manage.py spectacular --file $(OPENAPI_PATH)

# dev relies on local env configuration (DATABASE, AWS, Stripe). Update .env as needed.
dev:
	$(Q)$(PYTHON) manage.py runserver
