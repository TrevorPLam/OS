# docs/GOVERNANCE_HEALTH.md — Governance Health

Last Updated: 2026-01-05

This document defines what “healthy governance” means for this repo.

## Invariants (must be true)
- `CODEBASECONSTITUTION.md` exists and is the top authority.
- `READMEAI.md` exists and reflects reality.
- `TODO.md` is the task truth source and includes a `Task Truth Source:` line.
- Completed tasks live in `TODOCOMPLETED.md`.
- GitHub Actions are **off by default** and stored under `githubactions/`.

## Health checks (quick)
Run (optional):
- `scripts/ai-audit.sh` (file presence + basic invariants)
- `scripts/check.sh` (lint/test/build if available)
- `scripts/security-scan.sh` (lightweight checks)

Optional helper:
- `scripts/sync-todo.sh` generates `TODO.generated.md` from `specs/project-tasks.md` (non-binding; informational only)

## Failure policy
- If an invariant fails, create a task in `TODO.md` and mark it `BLOCKED` if external action is required.
- If a security invariant fails (secrets/auth bypass), create a `P0` task and stop work until resolved.
