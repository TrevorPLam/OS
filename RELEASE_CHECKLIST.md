# RELEASE CHECKLIST

Precedence: CODEBASECONSTITUTION.md → READMEAI.md → specs/* → this document.

Purpose: ship changes safely and repeatably without relying on CI/GitHub Actions. This checklist is designed for non-coders and AI-driven development: it favors deterministic “confirm + record” steps and small, verifiable smoke tests.

Release types:

* Patch: bugfixes, no behavior changes expected
* Minor: new features, backward compatible
* Major: breaking changes or significant behavior changes

Primary outputs (must be updated):

* CHANGELOG.md (release entry)
* TODO.md / TODO_COMPLETED.md (tasks reconciled)
* Optional: DECISIONS.md (if tradeoffs/choices were made)
---

## AGENT EXECUTION PROMPT (RUN THIS EXACTLY)

You are a release agent. Prepare a release by following this checklist in order.

Constraints:

* Assume the repo owner does not run scripts and does not rely on GitHub Actions.
* Prefer actions that can be verified by reading code, reading configuration, and using the deployment preview (e.g., Vercel Preview) rather than local command execution.
* If you would normally “run tests,” instead:

  1. confirm test files exist and are relevant, and
  2. perform the manual smoke tests listed below using the preview deployment or the app UI.

Deliverables:

1. A completed checklist record (copy into the bottom “Release Record” section).
2. A release-ready CHANGELOG.md entry.
3. A short “Release Notes” summary (5–15 bullets).
4. Any discovered gaps converted into TODO.md tasks with IDs.

⠀
Stop conditions:

* If any P0 blocker is found, stop and write a “BLOCKED” release record with required fixes as P0 tasks.
---

## Phase 0 — Define the Release

1. Identify target version

⠀
* If you use SemVer:

  * Patch: x.y.(z+1)
  * Minor: x.(y+1).0
  * Major: (x+1).0.0
* If you don’t use SemVer yet:

  * Use date-based version: YYYY.MM.DD (e.g., 2026.01.02)

1. Name the release (short)

2. Examples:

⠀
* “Fix booking confirmation”
* “Add payments capture flow”
* “UI polish + reliability improvements”

1. Confirm scope

⠀
* List the included features/bugfixes in 5–15 bullets.
* Confirm what is explicitly NOT included.

Gate:

* You can explain what’s shipping in one paragraph.
---

## Phase 1 — Backlog Hygiene (Must Be Clean)

1. Run a quick task sanity pass

⠀
* TODO.md:

  * No completed tasks remain.
  * Top tasks align with what you’re shipping.
* TODO_COMPLETED.md:

  * Completed work for this release is recorded (dated).

1. Docs must not contain executable tasks

⠀
* If you spot TODO/FIXME in docs related to the release:

  * Convert to TODO.md tasks (T-###)
  * Replace in docs with “Tracked in TODO: T-###”

Gate:

* The backlog matches reality and release scope.
---

## Phase 2 — Risk Review (Lightweight but Mandatory)

Answer these questions in the Release Record:

A) What changed that could break users?

* UI flow changes?
* Data model changes?
* Auth/permissions changes?
* Payment logic changes?
* Integrations changed?

B) Who could be affected?

* New users vs returning users
* Admin vs standard user roles
* Mobile vs desktop
* Different environments (staging/prod)

C) What is the rollback plan?

* “Revert to previous deployment” (most common)
* “Disable feature path” (if feature flags exist)
* “Restore config to previous values”

Gate:

* Risks are explicitly listed with mitigation.
---

## Phase 3 — Configuration & Secrets Safety

Because you’re not running CI, this phase is about preventing the most common catastrophic mistakes.

1. Secrets check (must confirm)

⠀
* No API keys, passwords, tokens, private keys are committed in:

  * .env*, env.example, config files, code constants
* env.example contains placeholders only, not real values.

1. Environment variables sanity

⠀
* All new required env vars are documented in env.example.
* If an env var is removed/renamed:

  * document the change in CHANGELOG.md under “Breaking” or “Changed”
  * add migration notes to Release Notes

1. External service configuration

⠀
* Confirm any external dashboards/settings changes required for release are documented (Stripe settings, webhooks, OAuth settings, etc.).

Gate:

* No secrets in repo; env changes are documented.
---

## Phase 4 — Data & Migration Safety (If Applicable)

Only do this if your app has persistent data (database/storage).

1. Data model changes

⠀
* Identify what changed (tables/fields/objects).
* Confirm compatibility:

  * does old data still load?
  * do new fields have defaults?
  * does the UI handle missing fields?

1. Backwards compatibility

⠀
* If API contracts changed:

  * document contract changes
  * ensure old clients won’t crash (or mark as breaking)

1. Recovery plan

⠀
* If a change could corrupt data:

  * document the recovery approach (restore backup, revert schema, etc.)

Gate:

* Data changes are safe or explicitly marked as breaking with recovery plan.
---

## Phase 5 — Manual Smoke Tests (Non-Negotiable)

Run these tests in the Preview Deployment (preferred) or the app UI.

Choose the relevant set and record pass/fail.

### Universal UI tests (always)

* App loads without a blank screen.
* Primary navigation works.
* At least one “happy path” completes end-to-end.
* Error states exist (you can trigger at least one).
* Mobile view is usable (basic layout not broken).

### Auth tests (if auth exists)

* Sign in works.
* Sign out works.
* Unauthorized access is blocked (try direct URL).
* Password reset / magic link path works (if implemented).

### Payments tests (if payments exist)

* Checkout/payment flow completes in test mode.
* Failure path works (declined payment scenario or invalid method).
* Receipts/confirmation screen appears.
* Idempotency: refreshing or double-clicking doesn’t double-charge (verify in logic and/or test env behavior).

### CRUD/data tests (if data entry exists)

* Create item → view → update → delete (or archive).
* Validation catches invalid input.
* Data persists after refresh.

### Integrations (if any)

* Webhook event received/handled (or at least handler exists and logs safely).
* OAuth/connect flow works (if applicable).

Gate:

* All selected smoke tests pass, or failures are logged as P0/P1 tasks and release is blocked if P0.
---

## Phase 6 — Quality Gate Without CI

Because you may not run tests/lint locally, do these “static gates”:

1. Diff sanity (human/agent read)

⠀
* No accidental large deletions of critical files.
* No debug code left behind (obvious console.log, “TEMP”, “REMOVE ME”).
* No commented-out large blocks used as “feature toggles” (unless explicitly intended).

1. Error handling & UX sanity

⠀
* New API calls have:

  * loading state
  * error state
  * user-friendly messaging (not raw stack traces)
* Inputs have validation and helpful messages.

1. Accessibility basics (fast)

⠀
* Buttons have labels.
* Forms have labels.
* Contrast isn’t obviously broken (quick visual check).

Gate:

* No obvious footguns remain.
---

## Phase 7 — Documentation Updates (Release-Linked)

1. Update CHANGELOG.md (required)

2. Include:

⠀
* Version + date
* Added / Changed / Fixed
* Breaking changes (if any)
* Migration notes (if needed)

1. Update docs where behavior changed

⠀
* If user-facing behavior changed, ensure the relevant docs reflect it.
* If developer/operator behavior changed, update READMEAI.md / RUNBOOK.md as appropriate.

Gate:

* Anyone reading docs can understand the new behavior.
---

## Phase 8 — Final “Go/No-Go”

Go if:

* Smoke tests passed
* No P0 tasks remain unresolved
* Changelog updated
* Rollback plan stated

No-Go if:

* Any P0 blocker exists
* Payment/data safety uncertain
* Secrets/env changes not documented
---

## Release Record (Fill This In Every Time)

Release Version:

Release Name:

Release Date (YYYY-MM-DD):

## Scope Summary (5–15 bullets):

Risk Review:

* Potential breakages:
* Affected users/roles:
* Rollback plan:

Secrets & Config:

* Secrets check: PASS/FAIL
* Env updates documented: PASS/FAIL
* External config required: YES/NO (details)

Data & Migration (if applicable):

* Data changes: YES/NO (details)
* Recovery plan documented: YES/NO

Manual Smoke Tests (record PASS/FAIL):

* Universal UI:
* Auth (if applicable):
* Payments (if applicable):
* CRUD/Data (if applicable):
* Integrations (if applicable):

Static Quality Gate:

* Diff sanity: PASS/FAIL
* Error handling states: PASS/FAIL
* Accessibility basics: PASS/FAIL

Docs:

* CHANGELOG updated: YES/NO
* Docs updated where needed: YES/NO

Decision:

* GO / NO-GO
* If NO-GO: list blockers as TODO.md tasks (T-###):

## Release Notes (final bullets to communicate):

---