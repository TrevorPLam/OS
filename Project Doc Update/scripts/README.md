# scripts/README.md — Local Tools (Optional)

Last Updated: 2026-01-05

These scripts are **optional helpers**. They exist to reduce manual work, but they must not become a dependency for progress.

## Activation (opt-in)
- **Default**: run scripts manually as needed.
- **Opt-in hooks**: set `ENABLE_GITHOOKS=1` when running `scripts/bootstrap.sh`.
- **Opt-in GitHub Actions**: see `githubactions/README.md`.

## Key scripts
- `scripts/check.sh` — best-effort local verification (lint/test/build if available)
- `scripts/security-scan.sh` — lightweight checks (no paid tools required)
- `scripts/ai-audit.sh` — validates required governance files exist and basic invariants hold
- `scripts/sync-todo.sh` — generates `TODO.generated.md` from `specs/project-tasks.md (non-binding notes)` (non-binding)

## Non-binding rule
- `TODO.md` is the task truth source.
- `TODO.generated.md` is informational only and may be discarded.
