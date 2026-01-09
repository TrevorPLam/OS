SHELL := /bin/bash
.ONESHELL:

Q := @
ifneq ($(V),1)
Q := @
else
Q :=
endif

NPM ?= npm

.PHONY: setup lint test build dev deps-check

setup:
	$(Q)$(NPM) ci

lint:
	$(Q)$(NPM) run lint

test:
	$(Q)$(NPM) run typecheck
	$(Q)$(NPM) run test

build:
	$(Q)$(NPM) run build

dev:
	$(Q)$(NPM) run dev

deps-check:
	$(Q)$(NPM) run deps:check
