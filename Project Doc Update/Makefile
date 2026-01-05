SHELL := /usr/bin/env bash

.PHONY: help governance security sync-todo check fix ci

help:
	@echo "Targets:"
	@echo "  make sync-todo   - Regenerate TODO.md from specs/project-tasks.md (non-binding notes)"
	@echo "  make governance  - Run governance audit"
	@echo "  make security    - Run lightweight security scan"
	@echo "  make check       - Run repo checks (best-effort, stack-aware)"
	@echo "  make ci          - Strict checks for CI"

sync-todo:
	@./scripts/sync-todo.sh

governance:
	@./scripts/ai-audit.sh

security:
	@./scripts/security-scan.sh

check:
	@./scripts/check.sh

fix:
	@echo "No universal fixer in template. Add repo-specific fix steps (formatter/autofix) to scripts/check.sh."

ci: sync-todo governance security check
