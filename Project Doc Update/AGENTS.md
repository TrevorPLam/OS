# AGENTS.md — Agent Instructions (Root)

Last Updated: 2026-01-05
Applies To: Any coding/documentation agent operating in this repo

## Authority order
1) `CODEBASECONSTITUTION.md`
2) `READMEAI.md`
3) `TODO.md`
4) Audit runbooks (`CODEAUDIT.md`, `SECURITYAUDIT.md`, etc.)
5) `specs/` (non-binding notes)

## Non-negotiables
- Do not invent facts about the repo. Use **UNKNOWN** + cite what you checked.
- If requirements are ambiguous, ask questions before implementing.
- `TODO.md` is the task truth source. Do not auto-edit it except to add/update tasks.
- Secrets must never be committed.

## Output expectations
- Prefer small, reversible diffs.
- Every change must include verification (tests/lint/build or observable behavior).
- When you create tasks, include exact file paths and acceptance criteria.

## Cost control
- Assume GitHub Actions are OFF by default. See `githubactions/README.md`.
- Prefer local scripts and manual checks over paid services.
