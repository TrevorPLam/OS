# PROJECT_STATUS.md — Working Status & Decisions

Document Type: Operations
Canonical Status: Canonical
Owner: Trevor
Audience: Humans + agents
Last Updated: 2026-01-22

## Purpose
A lightweight place to record the current state of the project, major decisions, and open questions.
This is not a task list; tasks belong in `TODO.md`.

## Current snapshot
- Phase: Backend hardening and test backfill
- Environment: Local development (tests run with SQLite; RLS probes skip without PostgreSQL)
- Last known “green” state (commit/tag): After completing T-026, T-060, T-123
- Key risks: RLS enforcement requires PostgreSQL for full validation; ensure background jobs wrap DB access in `firm_db_session` before releasing.
- Recent change: Enabled GitHub Actions workflows and removed cost-control governance language.

## Decisions (append-only)
Use this format:

- Date: 2026-01-20
  - Decision: Implement SAML CSRF protection using RelayState parameter instead of removing csrf_exempt decorators.
  - Why: SAML POST requests come from external IdPs, not from our forms. Standard Django CSRF tokens don't work for cross-origin requests. RelayState is the SAML-standard approach for preventing CSRF attacks.
  - Alternatives considered: Removing csrf_exempt entirely (rejected—breaks SAML spec), using custom CSRF middleware (rejected—overcomplicated).
  - Trade-offs: Must keep csrf_exempt decorator but add explicit RelayState validation. Requires session storage for state tokens.
  - Follow-up (task IDs in TODO.md): T-128 (SAML CSRF protection), T-134 (defensive attribute extraction), T-136 (error message sanitization)

- Date: 2026-01-06
  - Decision: Enable PostgreSQL row-level security for all firm-scoped tables using `app.current_firm_id` session context.
  - Why: Close remaining tenant isolation gaps and provide database-level enforcement beyond application query guards.
  - Alternatives considered: Per-app gradual rollout (would delay coverage), relaxing policies when `app.current_firm_id` is unset (rejected—would weaken isolation).
  - Trade-offs: Requires session scoping for background jobs/CLI access; PostgreSQL-specific enforcement (tests skip on SQLite).
  - Follow-up (task IDs in TODO.md): T-123 (document RLS model + ops implications)

- Date: 2026-01-22
  - Decision: Run GitHub Actions workflows from `.github/workflows/` and remove disabled-by-default governance.
  - Why: Actions are now enabled, so workflows should live in the standard directory with docs aligned.
  - Alternatives considered: Keeping a parking-lot directory (rejected—conflicts with enabled CI).
  - Trade-offs: CI runs on pushes and PRs; keep workflows scoped to needed checks.
  - Follow-up (task IDs in TODO.md): T-148 (enable workflows + governance updates)

- Date: 2026-01-20
  - Decision: Created PERFECT.md to track comprehensive codebase cleanup and optimization project across 9 analysis criteria.
  - Why: Problem statement requires systematic transformation of codebase to production-ready, world-class status with holistic quality tracking beyond individual TODO tasks.
  - Alternatives considered: Using only TODO.md (rejected—lacks holistic quality view), creating separate tracking files per criterion (rejected—fragmented view).
  - Trade-offs: PERFECT.md is read-mostly and must defer to TODO.md for task authority per CODEBASECONSTITUTION.md. Adds documentation overhead but provides essential progress visibility.
  - Follow-up (task IDs in TODO.md): Phase 1 tasks (T-129, T-130) for critical security completion; new tasks to be created for gaps identified in 9-criteria analysis.

## Open questions
- Q:
  - Context:
  - Needed input:
  - Task (BLOCKED) ID:
