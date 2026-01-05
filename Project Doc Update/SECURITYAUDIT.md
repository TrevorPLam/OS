# SECURITYAUDIT.md — Security Audit (Budget-Constrained Hardening)

Document Type: Audit Runbook
Last Updated: 2026-01-05
Precedence: `CODEBASECONSTITUTION.md` → `READMEAI.md` → `TODO.md` → this document
Owner: AGENT

Purpose: Find issues that could cause data exposure, account compromise, fraud, or runaway spend—without relying on paid scanners.

## AGENT execution (runbook)
Inputs to inspect:
- `.env.example (if present)`
- `.gitignore`
- `Auth-related code`
- `API routes / server handlers`
- `Client input handling`
- `Deployment config (Vercel/headers) if present`

Execution steps:
1) Check for secrets in repo (config files, docs, examples).
2) Verify server-side authorization for any privileged actions and any per-user data access (IDOR).
3) Review input validation boundaries for common injection classes (XSS/SQL/SSRF/ReDoS) based on actual code patterns found.
4) Confirm safe defaults for headers and error handling (no stack traces to users).
5) Write tasks with business impact in Context and explicit verification steps in Acceptance Criteria.

Stop conditions:
- If a secret is found in git history or current files, create a P0 task that instructs rotation/revocation and stop.
- If an auth bypass/IDOR is credible, create a P0 task and stop.

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
