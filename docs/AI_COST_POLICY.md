# AI_COST_POLICY.md

Last Updated: 2026-01-02

Goal: prevent runaway agent sessions and “rewrite the world” diffs.

## Hard limits (recommended defaults)
- One task per run (Builder mode).
- Max files changed per run: 6 (unless the task explicitly requires more).
- Max diff size per run: ~300 LOC net (unless approved in Planner mode).
- Prefer “small PRs” over big refactors.

## Stop conditions
Stop and ask (or switch to Planner) when:
- You must guess a requirement.
- You discover missing context needed to proceed.
- The change would break public APIs / database schema without an ADR.
- The diff exceeds limits.

## Reporting
Every run should include:
- Confidence 0–100
- Commands run
- Next Immediate Step
- Any UNKNOWNs blocking progress
