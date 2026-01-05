# BOOTSTRAP_GUIDE.md — How to Use This Template

Document Type: Guide
Canonical Status: Canonical
Owner: Trevor
Audience: Humans + agents
Last Updated: 2026-01-05

## Goal
Bootstrap an AI-operable repo with minimal cost and maximum clarity.

## Quick start (human)
1) Read `READMEAI.md`
2) Add your real project details to:
   - `specs/product-brief.md`
   - `specs/project-spec.md`
   - `specs/technical-plan.md`
3) Populate `TODO.md` with your first 5–15 tasks (small, measurable).
4) Run optional checks (no CI required):
   - `make governance`
   - `make security`
   - `make check`

## Quick start (agent)
1) Read `CODEBASECONSTITUTION.md` → `READMEAI.md` → `TODO.md`
2) If TODO is empty: run `CODEAUDIT.md` to create a first backlog.
3) Ask clarifying questions early; do not implement with ambiguous requirements.

## Cost control defaults
- GitHub Actions are parked in `githubactions/` (disabled).
- Hooks are off unless enabled via env vars (see `scripts/README.md`).

## When you’re ready for CI
1) Enable GitHub Actions in repo settings
2) Copy `githubactions/workflows/*` → `githubactions/workflows (disabled by default)/`
3) Commit and verify runs

## Repo hygiene
- Keep root docs ≤ ~12.
- Avoid duplicate docs; deprecate/merge instead.
