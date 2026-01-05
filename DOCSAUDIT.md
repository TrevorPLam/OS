# DOCSAUDIT.md — Docs Audit (Findability & Truth)

Document Type: Audit Runbook
Last Updated: 2026-01-05
Precedence: `CODEBASECONSTITUTION.md` → `READMEAI.md` → `TODO.md` → this document
Owner: AGENT

Purpose: Keep documentation searchable, consistent, and non-contradictory so agents can operate with less context load.

## AGENT execution (runbook)
Inputs to inspect:
- `docs/ directory`
- `Root docs`
- `specs/ (non-binding notes)`
- `repo.manifest.yaml`

Execution steps:
1) Ensure docs do not contradict the Constitution, READMEAI, or TODO truth model.
2) Create/refresh docs index so an agent can find what it needs quickly.
3) Remove/convert task leakage from docs into TODO.md tasks, leaving references behind.
4) Archive outdated docs instead of deleting when uncertain.

Stop conditions:
- If a doc’s truth cannot be verified, mark UNKNOWN and create a task to verify rather than guessing.

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
