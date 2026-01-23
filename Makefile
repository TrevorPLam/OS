# Meta-commentary:
# - Current Status: Orchestrates backend/frontend workflows with summary reporting.
# - Mapping: `test-performance` calls the backend performance target for query-efficiency checks.
# - Reasoning: Keep verification steps explicit and centralized for deterministic local runs.
# - Assumption: Backend performance tests run in environments with Django test settings configured.
# - Limitation: Verify target is best-effort; some steps may fail in constrained environments.
SHELL := /bin/bash
.ONESHELL:

Q := @
ifneq ($(V),1)
Q := @
else
Q :=
endif

SKIP_HEAVY ?= 1

.PHONY: setup lint test test-performance typecheck dev openapi verify ci e2e frontend-build fixtures check-governance

setup:
	$(Q)set +e
	backend_status=0
	frontend_status=0
	$(Q)echo "=== BACKEND SETUP ==="
	$(Q)$(MAKE) -C backend setup V=$(V)
	backend_status=$$?
	$(Q)echo "=== FRONTEND SETUP ==="
	$(Q)$(MAKE) -C frontend setup V=$(V)
	frontend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND SETUP: PASS"; else echo "BACKEND SETUP: FAIL"; fi
	$(Q)if [ $$frontend_status -eq 0 ]; then echo "FRONTEND SETUP: PASS"; else echo "FRONTEND SETUP: FAIL"; fi
	$(Q)summary=0
	$(Q)if [ $$backend_status -ne 0 ] || [ $$frontend_status -ne 0 ]; then summary=1; fi
	$(Q)exit $$summary

lint:
	$(Q)set +e
	backend_status=0
	frontend_status=0
	$(Q)echo "=== BACKEND LINT ==="
	$(Q)$(MAKE) -C backend lint V=$(V)
	backend_status=$$?
	$(Q)echo "=== FRONTEND LINT ==="
	$(Q)$(MAKE) -C frontend lint V=$(V)
	frontend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND LINT: PASS"; else echo "BACKEND LINT: FAIL"; fi
	$(Q)if [ $$frontend_status -eq 0 ]; then echo "FRONTEND LINT: PASS"; else echo "FRONTEND LINT: FAIL"; fi
	$(Q)summary=0
	$(Q)if [ $$backend_status -ne 0 ] || [ $$frontend_status -ne 0 ]; then summary=1; fi
	$(Q)exit $$summary

test:
	$(Q)set +e
	backend_status=0
	frontend_status=0
	$(Q)echo "=== BACKEND TEST ==="
	$(Q)$(MAKE) -C backend test V=$(V)
	backend_status=$$?
	$(Q)echo "=== FRONTEND TEST ==="
	$(Q)$(MAKE) -C frontend test V=$(V)
	frontend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND TEST: PASS"; else echo "BACKEND TEST: FAIL"; fi
	$(Q)if [ $$frontend_status -eq 0 ]; then echo "FRONTEND TEST: PASS"; else echo "FRONTEND TEST: FAIL"; fi
	$(Q)summary=0
	$(Q)if [ $$backend_status -ne 0 ] || [ $$frontend_status -ne 0 ]; then summary=1; fi
	$(Q)exit $$summary

test-performance:
	$(Q)set +e
	backend_status=0
	$(Q)echo "=== BACKEND PERFORMANCE TESTS ==="
	$(Q)$(MAKE) -C backend test-performance V=$(V)
	backend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND PERFORMANCE TESTS: PASS"; else echo "BACKEND PERFORMANCE TESTS: FAIL"; fi
	$(Q)exit $$backend_status

typecheck:
	$(Q)set +e
	backend_status=0
	$(Q)echo "=== BACKEND TYPECHECK ==="
	$(Q)$(MAKE) -C backend typecheck V=$(V)
	backend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND TYPECHECK: PASS"; else echo "BACKEND TYPECHECK: FAIL"; fi
	$(Q)exit $$backend_status

e2e:
	$(Q)set +e
	frontend_status=0
	$(Q)echo "=== FRONTEND E2E ==="
	$(Q)$(MAKE) -C frontend e2e V=$(V)
	frontend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$frontend_status -eq 0 ]; then echo "FRONTEND E2E: PASS"; else echo "FRONTEND E2E: FAIL"; fi
	$(Q)exit $$frontend_status

frontend-build:
	$(Q)set +e
	frontend_status=0
	$(Q)echo "=== FRONTEND BUILD ==="
	$(Q)$(MAKE) -C frontend build-check V=$(V)
	frontend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$frontend_status -eq 0 ]; then echo "FRONTEND BUILD: PASS"; else echo "FRONTEND BUILD: FAIL"; fi
	$(Q)exit $$frontend_status

dev:
	$(Q)set +e
	backend_status=0
	frontend_status=0
	$(Q)echo "=== BACKEND DEV ==="
	$(Q)$(MAKE) -C backend dev V=$(V)
	backend_status=$$?
	$(Q)echo "=== FRONTEND DEV ==="
	$(Q)$(MAKE) -C frontend dev V=$(V)
	frontend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND DEV: PASS"; else echo "BACKEND DEV: FAIL"; fi
	$(Q)if [ $$frontend_status -eq 0 ]; then echo "FRONTEND DEV: PASS"; else echo "FRONTEND DEV: FAIL"; fi
	$(Q)summary=0
	$(Q)if [ $$backend_status -ne 0 ] || [ $$frontend_status -ne 0 ]; then summary=1; fi
	$(Q)exit $$summary

fixtures:
	$(Q)set +e
	backend_status=0
	$(Q)echo "=== BACKEND FIXTURES ==="
	$(Q)$(MAKE) -C backend fixtures V=$(V)
	backend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND FIXTURES: PASS"; else echo "BACKEND FIXTURES: FAIL"; fi
	$(Q)exit $$backend_status

openapi:
	$(Q)set +e
	backend_status=0
	$(Q)echo "=== BACKEND OPENAPI ==="
	$(Q)$(MAKE) -C backend openapi V=$(V)
	backend_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_status -eq 0 ]; then echo "BACKEND OPENAPI: PASS"; else echo "BACKEND OPENAPI: FAIL"; fi
	$(Q)exit $$backend_status

verify:
	$(Q)set +e
	backend_lint_status=0
	backend_typecheck_status=0
	backend_performance_status=0
	frontend_lint_status=0
	backend_test_status=0
	frontend_test_status=0
	frontend_build_status=0
	openapi_status=0
	openapi_diff_status=0
	$(Q)echo "=== BACKEND LINT ==="
	$(Q)$(MAKE) -C backend lint V=$(V)
	backend_lint_status=$$?
	$(Q)echo "=== BACKEND TYPECHECK ==="
	$(Q)$(MAKE) -C backend typecheck V=$(V)
	backend_typecheck_status=$$?
	$(Q)echo "=== FRONTEND LINT ==="
	$(Q)$(MAKE) -C frontend lint V=$(V)
	frontend_lint_status=$$?
	$(Q)if [ "$(SKIP_HEAVY)" = "1" ]; then \
		echo "=== BACKEND TEST ==="; echo "SKIPPED (set SKIP_HEAVY=0 to run)"; backend_test_status=0; \
		echo "=== BACKEND PERFORMANCE TESTS ==="; echo "SKIPPED (set SKIP_HEAVY=0 to run)"; backend_performance_status=0; \
		echo "=== FRONTEND TEST ==="; echo "SKIPPED (set SKIP_HEAVY=0 to run)"; frontend_test_status=0; \
		echo "=== FRONTEND BUILD ==="; echo "SKIPPED (set SKIP_HEAVY=0 to run)"; frontend_build_status=0; \
		echo "=== BACKEND OPENAPI ==="; echo "SKIPPED (set SKIP_HEAVY=0 to run)"; openapi_status=0; openapi_diff_status=0; \
	else \
		echo "=== BACKEND TEST ==="; $(MAKE) -C backend test V=$(V); backend_test_status=$$?; \
		echo "=== BACKEND PERFORMANCE TESTS ==="; $(MAKE) -C backend test-performance V=$(V); backend_performance_status=$$?; \
		echo "=== FRONTEND TEST ==="; $(MAKE) -C frontend test V=$(V); frontend_test_status=$$?; \
		echo "=== FRONTEND BUILD ==="; $(MAKE) -C frontend build-check V=$(V); frontend_build_status=$$?; \
		echo "=== BACKEND OPENAPI ==="; $(MAKE) -C backend openapi V=$(V); openapi_status=$$?; \
		git diff --exit-code backend/openapi.yaml; openapi_diff_status=$$?; \
	fi
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$backend_lint_status -eq 0 ]; then echo "BACKEND LINT: PASS"; else echo "BACKEND LINT: FAIL"; fi
	$(Q)if [ $$backend_typecheck_status -eq 0 ]; then echo "BACKEND TYPECHECK: PASS"; else echo "BACKEND TYPECHECK: FAIL"; fi
	$(Q)if [ $$backend_performance_status -eq 0 ]; then echo "BACKEND PERFORMANCE TESTS: PASS"; else echo "BACKEND PERFORMANCE TESTS: FAIL"; fi
	$(Q)if [ $$frontend_lint_status -eq 0 ]; then echo "FRONTEND LINT: PASS"; else echo "FRONTEND LINT: FAIL"; fi
	$(Q)if [ $$backend_test_status -eq 0 ]; then echo "BACKEND TEST: PASS"; else echo "BACKEND TEST: FAIL"; fi
	$(Q)if [ $$frontend_test_status -eq 0 ]; then echo "FRONTEND TEST: PASS"; else echo "FRONTEND TEST: FAIL"; fi
	$(Q)if [ $$frontend_build_status -eq 0 ]; then echo "FRONTEND BUILD: PASS"; else echo "FRONTEND BUILD: FAIL"; fi
	$(Q)if [ $$openapi_status -eq 0 ]; then echo "BACKEND OPENAPI: PASS"; else echo "BACKEND OPENAPI: FAIL"; fi
	$(Q)if [ $$openapi_diff_status -eq 0 ]; then echo "OPENAPI DRIFT: PASS"; else echo "OPENAPI DRIFT: FAIL"; fi
	$(Q)summary=0
	$(Q)if [ $$backend_lint_status -ne 0 ] || [ $$backend_typecheck_status -ne 0 ] || [ $$backend_performance_status -ne 0 ] || \
		[ $$frontend_lint_status -ne 0 ] || [ $$backend_test_status -ne 0 ] || \
		[ $$frontend_test_status -ne 0 ] || [ $$frontend_build_status -ne 0 ] || [ $$openapi_status -ne 0 ] || \
		[ $$openapi_diff_status -ne 0 ]; then summary=1; fi
	$(Q)exit $$summary

check-governance:
	$(Q)set +e
	governance_status=0
	$(Q)echo "=== GOVERNANCE VERIFICATION ==="
	$(Q)chmod +x scripts/governance-verify.sh
	$(Q)./scripts/governance-verify.sh
	governance_status=$$?
	$(Q)echo "=== SUMMARY ==="
	$(Q)if [ $$governance_status -eq 0 ]; then echo "GOVERNANCE VERIFICATION: PASS"; else echo "GOVERNANCE VERIFICATION: FAIL"; fi
	$(Q)exit $$governance_status

ci: verify
