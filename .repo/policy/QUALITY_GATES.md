# Quality Gates

**File**: `.repo/policy/QUALITY_GATES.md`

Quality Gates are the merge rules. `governance-verify` enforces them.

> **Related**: See `.repo/policy/CONSTITUTION.md` for governance rules, `.repo/policy/PRINCIPLES.md` for operating principles, `.repo/policy/SECURITY_BASELINE.md` for security checks, `.repo/policy/HITL.md` for HITL item management, and `.repo/policy/BOUNDARIES.md` for boundary enforcement.

## Merge policy
Policy: soft block with auto-generated waivers for waiverable gate failures.
Meaning: if a waiverable gate fails, a waiver is generated and must be approved/expired rules apply.

## Hard gates (must pass; not waiverable)
These are "governance integrity" gates. If these fail, the repo is not self-governing.
- Required artifacts are missing for the declared change type (Task Packet, required logs, trace, ADR/HITL when triggered).
- Trace log is missing or invalid against `.repo/templates/AGENT_TRACE_SCHEMA.json`.
- Required HITL items are not Completed (or validly waived where policy allows).
- Waiver referenced is missing or expired.
- `governance-verify` fails.

## Waiverable gates (waiver required when failing)
- Coverage targets (gradual ratchet).
- Performance/bundle budgets (strict with fallback to default).
- Warning budgets (zero warnings; waiver required if warnings exist).
- Test coverage regression (coverage should not decrease).
Note: waivers must be rare + temporary (see Principle 22).

## Test Requirements

**Minimum Coverage Thresholds:**
- Backend: 80% for new code, gradual ratchet for existing code
- Frontend: 70% for new components, gradual ratchet for existing code
- Integration tests: Required for API changes and cross-module work

**Test File Requirements:**
- New viewsets must have corresponding test files
- New components must have corresponding test files
- New API endpoints must have integration tests
- Test files should be co-located or in `tests/` directory

**Coverage Validation:**
- `governance-verify` checks that test files exist for modified code
- Coverage regression is detected (coverage should not decrease)
- Missing tests for new code trigger warnings (waiverable)

**Test Patterns:**
- See `.repo/templates/examples/` for test examples:
  - `example_test_viewset.py` - Django ViewSet tests
  - `example_test_component.tsx` - React component tests
  - `example_test_api_integration.py` - API integration tests
- See folder-level `.AGENT.md` files for module-specific test patterns

## Coverage strategy: gradual ratchet
- Do not require perfection immediately.
- Each change should improve coverage or keep it from regressing.
- Over time, the minimum bar rises.

## Performance budgets: strict with fallback to default
- Repo may define explicit budgets.
- If missing, use the default budgets described in this file (or referenced standard).
- If budgets are exceeded: fail + require waiver + remediation plan.

## Warnings: zero warnings
Warnings are treated as failures. If a warning exists, it must be fixed or waived.

## PR size policy: no limits
No hard PR size limits. Constitution still requires decomposition into shippable increments (Article 4: Incremental Delivery).

## Required checks
`governance_verify_checks`: all
Meaning: `governance-verify` checks everything it knows how to check for this repo type.
