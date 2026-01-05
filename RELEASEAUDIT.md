# RELEASEAUDIT.md — Release Audit (No-CI Deployment Readiness)

Document Type: Audit Runbook
Last Updated: 2026-01-05
Precedence: `CODEBASECONSTITUTION.md` → `READMEAI.md` → `TODO.md` → this document
Owner: AGENT

Purpose: Provide a deterministic release checklist and a release record that works even when CI/CD is disabled.

## AGENT execution (runbook)
Inputs to inspect:
- `README / deployment notes`
- `package.json scripts (if present)`
- `Any deployment configs`
- `Vercel settings docs (if present)`

Execution steps:
1) List the minimum commands to verify locally (build/test/lint) based on what exists in the repo (do not invent commands).
2) Define a manual smoke test checklist for critical flows (mobile-first).
3) Define a rollback plan (provider-level + git-level).
4) Create tasks for any missing release essentials (env docs, error pages, monitoring hooks).

Stop conditions:
- If a release requires an external action (DNS, provider settings, secret rotation), create Owner: Trevor task and mark BLOCKED until done.

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
