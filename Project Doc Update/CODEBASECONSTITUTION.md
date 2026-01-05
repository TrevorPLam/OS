# CODEBASECONSTITUTION.md — Governance & “Perfect Codebase” Standards

Document Type: Constitution
Version: 2.1.0
Last Updated: 2026-01-05
Status: Active

This is the highest authority in the repo. If anything conflicts with it, this wins.

## 1) North Star
This repo must be:
- Deterministic (next step discoverable)
- Auditable (changes traceable)
- Safe (no secrets in git; minimal blast radius)
- Maintainable (agents and humans can operate without guesswork)

## 2) Core operating principles
1) **Truth**: never invent facts; use **UNKNOWN** + cite checked files
2) **Clarify**: if requirements are ambiguous, ask before implementing
3) **Small diffs**: reversible changes preferred; large refactors require tasks
4) **Verify**: tests/lint/build or observable behavior is required
5) **Continuity**: keep `PROJECT_STATUS.md` and `CHANGELOG.md` accurate

## 3) Task governance
- Task truth source is `TODO.md`.
- Completed tasks move to `TODOCOMPLETED.md` (preserve original records).
- `specs/` are non-binding notes until converted into tasks.

## 4) Cost control constraints
- GitHub Actions are OFF by default.
- Any automation that increases spend must be explicitly approved in a task (Owner: Trevor).
- Workflows are stored under `githubactions/` for safe keeping.

## 5) Security non-negotiables
- Never commit secrets (keys, tokens, credentials).
- Authorization must be enforced server-side for privileged or per-user data.
- If a credible secret leak or auth bypass is found: create a P0 task and stop.

## 6) Documentation expectations
- Docs must reflect reality.
- If a doc’s truth cannot be verified, mark **UNKNOWN** and create a verification task.

## 7) Amendment protocol
Constitution changes require:
- A task in `TODO.md`
- A short rationale in the change description (or `CHANGELOG.md`)
