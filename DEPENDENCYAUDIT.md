# DEPENDENCYAUDIT.md — Dependency Audit (Health & Minimalism)

Document Type: Audit Runbook
Last Updated: 2026-01-05
Precedence: `CODEBASECONSTITUTION.md` → `READMEAI.md` → `TODO.md` → this document
Owner: AGENT

Purpose: Keep dependencies safe, minimal, and understandable for agents and future humans—without requiring paid CI.

## AGENT execution (runbook)
Inputs to inspect:
- `package.json (if present)`
- `lockfiles (package-lock.json / pnpm-lock.yaml / yarn.lock)`
- `Any runtime config that loads dependencies`
- `README / docs referencing deps`

Execution steps:
1) Inventory direct dependencies and classify: critical / convenience / likely-unused.
2) Flag high-risk deps: unmaintained, native binaries, broad transitive tree, security-sensitive surface (auth, crypto, payments).
3) For any proposed new dependency: list 2–3 alternatives (stdlib, existing deps, small custom code).
4) Create tasks for: removals, upgrades (with evidence), consolidation, and documentation updates (what the dependency is for).

Stop conditions:
- If you find a committed secret or a likely auth/payment vulnerability, stop and escalate via SECURITYAUDIT.md tasks (P0).
- If the repo has no dependency manifests, record that as UNKNOWN and stop.

Required outputs:
- Update/create tasks in TODO.md (Owner: AGENT or Trevor as appropriate).
- Append a run summary to this document.

## Task writing rules
- Tasks must be created/updated in `TODO.md` using the required schema.
- If a task is ambiguous, set **Status: BLOCKED** and add a question in the task Context.
- Do not invent repo facts. If evidence is missing, write **UNKNOWN** and cite what you checked.

---

## Summary (append-only)
> Append a dated summary after each run. Do not delete old summaries.

### 2026-01-05 — Summary
- Agent: AGENT
- Scope: UNKNOWN (not yet run)
- Findings:
  - (none)
- Tasks created/updated:
  - (none)
- Questions for Trevor:
  - (none)

### 2026-01-06 — Comprehensive Dependency Audit
- Agent: AGENT
- Scope: Complete inventory (requirements.txt, requirements-dev.txt, package.json)
- Method: Analyzed 47 Python deps, 23 dev deps, 14 frontend deps; classified by criticality
- Findings:
  - ✅ No secrets found; all credentials properly loaded from environment.
  - ✅ No auth/payment vulnerabilities detected.
  - ✅ Minimal frontend dependencies (well-chosen).
  - ⚠️ 3 unused dev dependencies: factory-boy, faker, import-linter.
  - ⚠️ boto3 1.34.11 outdated (should upgrade).
  - ⚠️ psycopg2-binary should replace with psycopg2 for production.
  - ⚠️ 5 native binary dependencies requiring careful maintenance.
  - ⚠️ python3-saml last updated 2+ years ago (maintenance concern).
  - ⚠️ Pillow: heavy dependency for single watermarking usage.
- High-Risk Dependencies: psycopg2-binary, boto3, cryptography, python3-saml, django-allauth
- Tasks created/updated:
  - T-031: Remove unused dev dependencies (P2, AGENT)
  - T-032: Consolidate pytest-cov/coverage (P2, AGENT)
  - T-033: Replace psycopg2-binary → psycopg2 (P1, AGENT)
  - T-034: Upgrade boto3 (P1, AGENT)
  - T-035: Evaluate python3-saml maintenance (P2, Trevor)
  - T-036: Evaluate DocuSign SDK adoption (P2, AGENT)
  - T-037: Evaluate Pillow single usage (P3, Trevor)
  - T-038: Create dependency documentation (P2, AGENT)
- Recommendation: Execute P1 tasks (T-033, T-034) within 7 days. Overall dependency health is GOOD.
- Questions for Trevor:
  - Is SAML authentication actively used in production? (affects T-035)
  - Is image watermarking feature essential? (affects T-037)
  - Any known issues with current DocuSign integration? (affects T-036)

### 2026-01-10 — DocuSign SDK Evaluation (T-036)
- Agent: AGENT
- Scope: DocuSign integration (SDK adoption evaluation)
- Method: Reviewed `src/modules/esignature/docusign_service.py` and `src/modules/esignature/views.py` for current API usage; attempted to fetch PyPI metadata for `docusign-esign` (blocked by network 403).
- Verification: `docs/scripts/check.sh` (failed: pytest invoked with `--cov` arguments, pytest-cov unavailable).
- Findings:
  - Current integration uses direct REST calls via `requests` for OAuth, user info, envelope create/send, status fetch, void, document download, and webhook signature verification.
  - SDK size and dependency tree are **UNKNOWN** due to blocked PyPI access in this environment.
  - Without verified SDK metadata or feature gaps, switching would add dependency risk without clear benefit.
- Tasks created/updated:
  - T-036: Marked complete after documenting evaluation and recommendation.
- Recommendation:
  - Stay with current custom integration until SDK dependency metadata and feature coverage can be verified in an environment with PyPI access, or until a concrete feature requirement (templates, embedded signing, bulk send) justifies the SDK.
- Questions for Trevor:
  - Can we allow PyPI metadata access for dependency evaluation in this environment?
  - Are there upcoming DocuSign features (templates, embedded signing, bulk send) that would require the SDK?
