# 🔒 TIER 1 EXECUTION PROMPT — SCHEMA TRUTH & CI TRUTH

You are executing Tier 1 only of a multi-tier build.
Tier 1 ensures the database schema and CI reflect reality. No feature work.

## Authority

* `/docs/claude/NOTES_TO_CLAUDE.md` is authoritative.
* Tier 0 must already be implemented. Do not re-architect Tier 0—only adjust if a Tier 1 change forces it.

## Scope (WHAT YOU MAY DO)

You may modify only what is required to:

1. Remove deterministic runtime blockers that prevent boot/schema generation
2. Ensure all Django models have migrations committed
3. Ensure tenant keys + referential integrity are structurally enforced (firm/client ownership FKs where required)
4. Make CI truthful (no skipped checks; frontend build/typecheck enforced)
5. Add a minimum safety test set protecting core invariants (tenant isolation/portal containment/engagement immutability/billing approval gates)
6. Ensure makemigrations is clean and migrate works from a fresh DB

### Explicitly IN SCOPE

* Fix app loading errors (AppConfig, label conflicts, import errors)
* Fix API schema generation errors (e.g., drf-spectacular enum/path issues)
* Create/commit missing migrations for all apps/models (including portal/chat/doc/assets)
* Tighten FK constraints and add required indexes needed for tenancy correctness (firm_id/client_id propagation)
* CI pipeline edits to:
  * remove `|| true` / "skip on fail"
  * enforce backend lint/test failures
  * enforce frontend build + TS typecheck failures
* Add targeted tests that fail hard if invariants break:
  * cross-firm isolation
  * portal default-deny
  * signed engagement immutability (if model exists)
  * time entry approval gate (if model exists; otherwise add placeholder test that asserts no unapproved time is invoiceable via current APIs)

### Explicitly OUT OF SCOPE (DO NOT TOUCH)

* Implementing new billing features, payment flows, pricing calculator, renewals
* Refactoring architecture "for cleanliness"
* UI/UX work except what's required for build/typecheck correctness
* Performance tuning beyond indexes required for tenant-scoped queries
* Large test suites; only minimum invariant coverage

## Invariants (MUST HOLD)

* CI must fail on real failures (lint/build/tests/typecheck)
* No model exists without migrations
* Tenant boundaries are enforced structurally (FKs + indexes where required)
* No "fix" may weaken scoping or permissions to make tests pass

## Execution Steps (DO THESE IN ORDER)

1. Identify and fix deterministic backend blockers preventing:
   * server boot
   * migrations
   * schema generation
2. Inventory all Django models; ensure migrations exist for every model.
3. Run/ensure makemigrations is a no-op and migrate is clean from empty DB.
4. Ensure tenant keys exist where required (firm/client), with non-null constraints where ownership is mandatory; add indexes supporting tenant-scoped queries.
5. Fix frontend compilation/type errors that block truthful CI gates (only to restore build correctness; no feature work).
6. Update CI so it cannot lie:
   * remove skipped lint
   * add frontend build + TS checks
7. Add minimal invariant tests (small count, high value) and wire into CI.

## Completion Checklist (STOP WHEN TRUE)

* [ ] Backend boots without deterministic exceptions.
* [ ] API schema generation completes without error.
* [ ] Fresh DB: migrations apply cleanly.
* [ ] makemigrations yields no changes.
* [ ] CI fails on lint errors and build/type errors (backend + frontend).
* [ ] Minimal invariant tests exist and run in CI.

## Output Requirements

Before stopping, report:

1. Files modified
2. Blockers found + exact fixes applied
3. Migration summary (apps touched, key tables/FKs/indexes)
4. CI changes (what gates added/removed)
5. Tests added (what each protects)
6. What was intentionally NOT touched

## Stop Conditions

* If a Tier 1 fix requires a product decision: STOP AND ASK.
* Do not proceed to Tier 2.
* Do not add "temporary bypasses" (no try/except swallowing, no `|| true`, no skipping checks).
