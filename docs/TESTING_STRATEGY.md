# TESTING_STRATEGY.md

Document Type: Reference
Version: 2.0.0
Last Updated: 2026-01-02
Owner: Repository Root
Status: Active

This is a template testing strategy. Real projects should extend it.

## Principles
- Every task must be verifiable.
- Prefer fast, deterministic tests.
- Record verification commands in the task itself.

## Standard commands
- Governance + security + best-effort checks: `make ci`
- Repo-specific checks: define in `repo.manifest.yaml` under `commands.*`

## Minimum acceptable verification per change
- A runnable command (tests, lint, build, or a smoke check)
- Evidence in the session output (commands + results)

## When to add more
Add coverage when:
- You introduce a new module boundary
- You add external integrations
- You change APIs or data models
