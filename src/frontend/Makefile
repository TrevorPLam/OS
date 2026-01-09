SHELL := /bin/bash
.ONESHELL:

Q := @
ifneq ($(V),1)
Q := @
else
Q :=
endif

NPM ?= npm

.PHONY: setup lint test build dev deps-check e2e

setup:
	$(Q)$(NPM) ci

lint:
	$(Q)$(NPM) run lint

test:
	$(Q)$(NPM) run typecheck
	$(Q)$(NPM) run test

e2e:
	$(Q)if [ ! -d node_modules ]; then $(NPM) ci; fi
	$(Q)if [ -z "$$E2E_SKIP_BROWSER_INSTALL" ]; then $(NPM) run e2e:install; fi
	$(Q)$(NPM) run e2e

build:
	$(Q)$(NPM) run build

dev:
	$(Q)$(NPM) run dev

deps-check:
	$(Q)$(NPM) run deps:check
