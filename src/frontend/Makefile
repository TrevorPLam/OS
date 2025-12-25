SHELL := /bin/bash
.ONESHELL:

Q := @
ifneq ($(V),1)
Q := @
else
Q :=
endif

NPM ?= npm

.PHONY: setup lint test build dev

setup:
	$(Q)$(NPM) ci

lint:
	$(Q)$(NPM) run lint

test:
	$(Q)$(NPM) run typecheck

build:
	$(Q)$(NPM) run build

dev:
	$(Q)$(NPM) run dev
