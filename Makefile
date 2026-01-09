SHELL := /bin/bash
.ONESHELL:

Q := @
ifneq ($(V),1)
Q := @
else
Q :=
endif

.PHONY: setup lint test dev openapi docs-validate docs-check verify e2e

setup:
	$(Q)set +e
	backend_status=0
	frontend_status=0
	docs_status=0
	$(Q)echo "=== BACKEND SETUP ==="
	$(Q)$(MAKE) -C src setup V=$(V)
	backend_status=$$?
	$(Q)echo "=== FRONTEND SETUP ==="
	$(Q)$(MAKE) -C src/frontend setup V=$(V)
	frontend_status=$$?
	$(Q)echo "=== DOCS SETUP ==="
	$(Q)echo "DOCS setup: SKIP"
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND SETUP: PASS"; else echo "BACKEND SETUP: FAIL"; fi
	$(Q)if [ $$frontend_status -eq 0 ]; then echo "FRONTEND SETUP: PASS"; else echo "FRONTEND SETUP: FAIL"; fi
	$(Q)echo "DOCS SETUP: SKIP"
	$(Q)summary=0
	$(Q)if [ $$backend_status -ne 0 ] || [ $$frontend_status -ne 0 ]; then summary=1; fi
	$(Q)exit $$summary

lint:
	$(Q)set +e
	backend_status=0
	frontend_status=0
	docs_status=0
	$(Q)echo "=== BACKEND LINT ==="
	$(Q)$(MAKE) -C src lint V=$(V)
	backend_status=$$?
	$(Q)echo "=== FRONTEND LINT ==="
	$(Q)$(MAKE) -C src/frontend lint V=$(V)
	frontend_status=$$?
	$(Q)echo "=== DOCS QUALITY CHECK ==="
	$(Q)$(MAKE) -C docs docs-check V=$(V)
	docs_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND LINT: PASS"; else echo "BACKEND LINT: FAIL"; fi
	$(Q)if [ $$frontend_status -eq 0 ]; then echo "FRONTEND LINT: PASS"; else echo "FRONTEND LINT: FAIL"; fi
	$(Q)if [ $$docs_status -eq 0 ]; then echo "DOCS QUALITY: PASS"; else echo "DOCS QUALITY: FAIL"; fi
	$(Q)summary=0
	$(Q)if [ $$backend_status -ne 0 ] || [ $$frontend_status -ne 0 ] || [ $$docs_status -ne 0 ]; then summary=1; fi
	$(Q)exit $$summary

test:
	$(Q)set +e
	backend_status=0
	frontend_status=0
	docs_status=0
	$(Q)echo "=== BACKEND TEST ==="
	$(Q)$(MAKE) -C src test V=$(V)
	backend_status=$$?
	$(Q)echo "=== FRONTEND TEST ==="
	$(Q)$(MAKE) -C src/frontend test V=$(V)
	frontend_status=$$?
	$(Q)echo "=== DOCS TEST ==="
	$(Q)echo "DOCS test: SKIP"
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND TEST: PASS"; else echo "BACKEND TEST: FAIL"; fi
	$(Q)if [ $$frontend_status -eq 0 ]; then echo "FRONTEND TEST: PASS"; else echo "FRONTEND TEST: FAIL"; fi
	$(Q)echo "DOCS TEST: SKIP"
	$(Q)summary=0
	$(Q)if [ $$backend_status -ne 0 ] || [ $$frontend_status -ne 0 ]; then summary=1; fi
	$(Q)exit $$summary

e2e:
	$(Q)set +e
	frontend_status=0
	$(Q)echo "=== FRONTEND E2E ==="
	$(Q)$(MAKE) -C src/frontend e2e V=$(V)
	frontend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$frontend_status -eq 0 ]; then echo "FRONTEND E2E: PASS"; else echo "FRONTEND E2E: FAIL"; fi
	$(Q)exit $$frontend_status

dev:
	$(Q)set +e
	backend_status=0
	frontend_status=0
	docs_status=0
	$(Q)echo "=== BACKEND DEV ==="
	$(Q)$(MAKE) -C src dev V=$(V)
	backend_status=$$?
	$(Q)echo "=== FRONTEND DEV ==="
	$(Q)$(MAKE) -C src/frontend dev V=$(V)
	frontend_status=$$?
	$(Q)echo "=== DOCS DEV ==="
	$(Q)echo "DOCS dev: SKIP"
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND DEV: PASS"; else echo "BACKEND DEV: FAIL"; fi
	$(Q)if [ $$frontend_status -eq 0 ]; then echo "FRONTEND DEV: PASS"; else echo "FRONTEND DEV: FAIL"; fi
	$(Q)echo "DOCS DEV: SKIP"
	$(Q)summary=0
	$(Q)if [ $$backend_status -ne 0 ] || [ $$frontend_status -ne 0 ]; then summary=1; fi
	$(Q)exit $$summary

openapi:
	$(Q)set +e
	backend_status=0
	$(Q)echo "=== BACKEND OPENAPI ==="
	$(Q)$(MAKE) -C src openapi V=$(V)
	backend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND OPENAPI: PASS"; else echo "BACKEND OPENAPI: FAIL"; fi
	$(Q)exit $$backend_status

docs-validate:
	$(Q)set +e
	docs_status=0
	$(Q)echo "=== DOCS QUALITY CHECK ==="
	$(Q)$(MAKE) -C docs docs-check V=$(V)
	docs_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$docs_status -eq 0 ]; then echo "DOCS QUALITY: PASS"; else echo "DOCS QUALITY: FAIL"; fi
	$(Q)exit $$docs_status

docs-check:
	$(Q)$(MAKE) docs-validate V=$(V)

verify:
	$(Q)set +e
	backend_lint_status=0
	frontend_lint_status=0
	docs_status=0
	backend_test_status=0
	frontend_test_status=0
	openapi_status=0
	openapi_diff_status=0
	$(Q)echo "=== BACKEND LINT ==="
	$(Q)$(MAKE) -C src lint V=$(V)
	backend_lint_status=$$?
	$(Q)echo "=== FRONTEND LINT ==="
	$(Q)$(MAKE) -C src/frontend lint V=$(V)
	frontend_lint_status=$$?
	$(Q)echo "=== DOCS VALIDATE ==="
	$(Q)$(MAKE) -C docs validate V=$(V)
	docs_status=$$?
	$(Q)echo "=== BACKEND TEST ==="
	$(Q)$(MAKE) -C src test V=$(V)
	backend_test_status=$$?
	$(Q)echo "=== FRONTEND TEST ==="
	$(Q)$(MAKE) -C src/frontend test V=$(V)
	frontend_test_status=$$?
	$(Q)echo "=== BACKEND OPENAPI ==="
	$(Q)$(MAKE) -C src openapi V=$(V)
	openapi_status=$$?
	$(Q)git diff --exit-code docs/03-reference/api/openapi.yaml
	openapi_diff_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_lint_status -eq 0 ]; then echo "BACKEND LINT: PASS"; else echo "BACKEND LINT: FAIL"; fi
	$(Q)if [ $$frontend_lint_status -eq 0 ]; then echo "FRONTEND LINT: PASS"; else echo "FRONTEND LINT: FAIL"; fi
	$(Q)if [ $$docs_status -eq 0 ]; then echo "DOCS VALIDATE: PASS"; else echo "DOCS VALIDATE: FAIL"; fi
	$(Q)if [ $$backend_test_status -eq 0 ]; then echo "BACKEND TEST: PASS"; else echo "BACKEND TEST: FAIL"; fi
	$(Q)if [ $$frontend_test_status -eq 0 ]; then echo "FRONTEND TEST: PASS"; else echo "FRONTEND TEST: FAIL"; fi
	$(Q)if [ $$openapi_status -eq 0 ]; then echo "BACKEND OPENAPI: PASS"; else echo "BACKEND OPENAPI: FAIL"; fi
	$(Q)if [ $$openapi_diff_status -eq 0 ]; then echo "OPENAPI DRIFT: PASS"; else echo "OPENAPI DRIFT: FAIL"; fi
	$(Q)summary=0
	$(Q)if [ $$backend_lint_status -ne 0 ] || [ $$frontend_lint_status -ne 0 ] || [ $$docs_status -ne 0 ] || \
		[ $$backend_test_status -ne 0 ] || [ $$frontend_test_status -ne 0 ] || [ $$openapi_status -ne 0 ] || [ $$openapi_diff_status -ne 0 ]; then summary=1; fi
	$(Q)exit $$summary
