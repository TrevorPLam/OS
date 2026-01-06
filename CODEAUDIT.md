# CODEAUDIT.md — Code Audit (Task Factory)

Document Type: Audit Runbook
Last Updated: 2026-01-05
Precedence: `CODEBASECONSTITUTION.md` → `READMEAI.md` → `TODO.md` → this document
Owner: AGENT

Purpose: Convert code and doc findings into small, executable tasks with clear acceptance criteria.

## AGENT execution (runbook)
Inputs to inspect:
- `Repository tree`
- `TODO.md / TODOCOMPLETED.md`
- `Open TODO/FIXME markers in code`
- `docs/ and specs/ for mismatches`

Execution steps:
1) Scan for actionable TODO/FIXME/HACK notes and convert them into tasks in TODO.md (replace with task IDs when appropriate).
2) Identify hotspots: large files, duplicated logic, inconsistent patterns that slow agents.
3) Map critical flows (auth, payments, booking/creation, admin) to ensure each has explicit tasks/tests where needed.
4) Deduplicate tasks and ensure each task references exact files/paths.

Stop conditions:
- If you discover a P0 security issue, stop and create a P0 task under SECURITYAUDIT.md (do not continue scanning).

Required outputs:
- Update/create tasks in TODO.md.
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

### 2026-01-06 — Code Audit Execution
- Agent: AGENT
- Scope: Full codebase scan (src/, tests/, docs/)
- Findings:
  - ✅ All TODO/FIXME/HACK markers in source code are properly tracked or converted to DEFERRED.
  - ⚠️ 5 large files (>2000 lines) identified as refactoring candidates.
  - ⚠️ Authentication flows lack direct unit tests (only E2E coverage).
  - ⚠️ Deal management features lack dedicated test coverage.
  - ✅ Payment/billing flows have good test coverage.
  - ✅ No new P0 security issues found (SEC-6 already tracked).
  - ✅ User model import patterns are consistent.
  - ✅ Firm scoping patterns are well-established.
- Tasks created/updated:
  - T-025: Add direct authentication flow unit tests (P1, QUALITY, M)
  - T-026: Add deal management unit tests (P2, QUALITY, L)
  - T-027: Split crm/models.py into separate files (P2, CHORE, M)
  - T-028: Split clients/models.py into separate files (P2, CHORE, M)
  - T-029: Split documents/models.py into separate files (P3, CHORE, M)
  - T-030: Split calendar/services.py into focused service classes (P3, CHORE, M)
- Questions for Trevor:
  - None at this time. All findings can be addressed by AGENT.
