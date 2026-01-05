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
