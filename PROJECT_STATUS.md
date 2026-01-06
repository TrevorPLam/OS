# PROJECT_STATUS.md — Working Status & Decisions

Document Type: Operations
Canonical Status: Canonical
Owner: Trevor
Audience: Humans + agents
Last Updated: 2026-01-05

## Purpose
A lightweight place to record the current state of the project, major decisions, and open questions.
This is not a task list; tasks belong in `TODO.md`.

## Current snapshot
- Phase:
- Environment:
- Last known “green” state (commit/tag):
- Key risks:

## Decisions (append-only)
Use this format:

- Date: 2026-01-06
  - Decision: Enable PostgreSQL row-level security for all firm-scoped tables using `app.current_firm_id` session context.
  - Why: Close remaining tenant isolation gaps and provide database-level enforcement beyond application query guards.
  - Alternatives considered: Per-app gradual rollout (would delay coverage), relaxing policies when `app.current_firm_id` is unset (rejected—would weaken isolation).
  - Trade-offs: Requires session scoping for background jobs/CLI access; PostgreSQL-specific enforcement (tests skip on SQLite).
  - Follow-up (task IDs in TODO.md): T-123 (document RLS model + ops implications)

## Open questions
- Q:
  - Context:
  - Needed input:
  - Task (BLOCKED) ID:
