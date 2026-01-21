# CODEAUDIT.md — Code Audit Runbook

**Authority & Precedence:**
1) CODEBASECONSTITUTION.md
2) READMEAI.md
3) P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md (Task Truth Source)
4) This audit runbook (CODEAUDIT.md)
5) Supporting docs (CODE_AUDIT.md, CODE_AUDIT_REPORT.md)

**Purpose:** Ensure code changes comply with constitutional rules, security expectations, and documented architecture boundaries without losing project-specific guidance.

## AGENT EXECUTION
- **Inputs to Inspect:** CODEBASECONSTITUTION.md, READMEAI.md, P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md, CODE_AUDIT.md, CODE_AUDIT_REPORT.md, CI configurations, docs/BOUNDARY_RULES.md (or equivalent), recent PRs/commits linked in TODO tasks.
- **Outputs to Produce:**
  - Findings recorded as tasks in P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md with IDs and acceptance criteria.
  - Notes appended to the `Summary` section below.
  - References to any exceptions or deferrals.
- **Stop Rules:**
  - Do not remove project-specific constraints from CODE_AUDIT.md or other docs.
  - Do not change build/test commands without explicit TODO coverage.
  - If secrets or security regressions are suspected, halt and escalate via SECURITYAUDIT.md guidance.

## Standard Checklist
- Linting and formatting commands defined and enforced.
- Type checking configured and passing (mypy/pyright as applicable).
- Security scanning (dependencies + code) enabled or TODO-tracked.
- Tests required for merge; coverage expectations documented.
- Build artifacts reproducible (Docker and package builds).
- Documentation (API/OpenAPI, architecture) updated alongside code changes.
- Architectural boundaries respected (no bypasses across layers/modules).

## Preserved Project Audit Pipeline (from CODE_AUDIT.md)
- Pre-Commit: `make lint` (ruff + black), type checking, and security scanning must pass; prefer auto-fix via `make format` where safe.
- Pre-Merge: `make test`, Docker build verification, documentation validation (links and OpenAPI), and security gates (no hardcoded secrets, RLS, permissions, input validation).
- Post-Merge: Periodic dependency health, documentation drift checks, and architectural compliance reviews.
- Violation Handling: Severity-based responses with exceptions documented in PRs and tracked in P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md.

## Reporting
- Record audit runs with date/time, scope, and findings.
- Link resulting tasks and PRs for traceability.
- Note any conflicts between governance layers and preserve both until resolved.

---

## Summary (append-only)
- Pending entries.
