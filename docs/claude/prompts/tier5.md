# 🔒 TIER 5 EXECUTION PROMPT — DURABILITY, SCALE & EXIT

You are executing Tier 5 only of a multi-tier build.
Tier 5 proves the system works end-to-end, scales safely, and allows clean exit. No new product features.

## Authority

* `/docs/claude/NOTES_TO_CLAUDE.md` is authoritative.
* Assume Tier 0–4 are complete and correct.
* Do not weaken privacy, audit, or billing invariants to make Tier 5 easier.

## Scope (WHAT YOU MAY DO)

You may modify only what is required to implement:

1. Hero end-to-end integration tests
2. Performance safeguards for tenant-scoped systems
3. Firm offboarding & data exit flows
4. Configuration change safety (no retroactive mutation)
5. Operational observability (metadata-only)

### Explicitly IN SCOPE

**A) Hero Workflow Integration Tests**
* End-to-end lifecycle coverage for:
  * Firm → Client → Engagement → Signed
  * Auto-created Projects/Tasks
  * Package invoicing
  * Hourly approval → invoice inclusion
  * Autopay success/failure (mocked)
  * Client portal visibility
  * Renewal → new engagement → continuity
* Use real models + transactions; mock only external processors.

**B) Performance & Isolation Safeguards**
* Pagination on all list endpoints (portal + firm).
* Ensure tenant indexes exist and are used for:
  * firm_id
  * client_id
* Eliminate N+1 queries on critical paths.
* Add lightweight performance regression checks where feasible.

**C) Firm Offboarding & Data Exit**
* Firm-initiated export:
  * structured data (JSON/CSV)
  * document bundle (encrypted)
* Retention window logic:
  * firm data retained for policy window
  * firm can request deletion at any time
* Deletion workflow:
  * content purged (tombstones)
  * liability metadata retained per policy
  * no cross-firm impact

**D) Configuration Change Safety**
* Ensure pricing/config changes:
  * apply prospectively only
  * do not mutate historical invoices or engagements
* Version config where necessary.
* Log security- or billing-relevant config changes (metadata only).

**E) Operational Observability (Privacy-Preserving)**
* Metrics/logs for:
  * request counts
  * error rates/codes
  * latency
  * background job failures
* All telemetry must include:
  * firm_id
  * optional client_id
* Telemetry must never include customer content.

### Explicitly OUT OF SCOPE (DO NOT TOUCH)

* New billing features
* Pricing calculator/CPQ
* UI/UX redesigns
* Encryption scheme changes
* SOC2 documentation (only primitives already added)
* Cross-tier refactors

## Invariants (MUST HOLD)

* No end-to-end test may bypass tenant or permission checks.
* Performance optimizations must not weaken scoping.
* Offboarding must not delete liability metadata prematurely.
* Observability must not ingest content.
* Historical data must remain immutable.

## Execution Steps (DO THESE IN ORDER)

1. Define 1–2 hero workflows and implement full integration tests.
2. Audit critical queries; add pagination, indexes, and prefetching.
3. Implement firm export mechanism (data + docs).
4. Implement retention timer + deletion trigger for offboarding.
5. Add safeguards so config changes do not affect historical records.
6. Implement metadata-only metrics/logging for ops visibility.

## Completion Checklist (STOP WHEN TRUE)

* [ ] End-to-end tests pass from a clean database.
* [ ] Large datasets do not degrade correctness or isolation.
* [ ] Firms can export, exit, and be deleted safely.
* [ ] Config changes do not rewrite history.
* [ ] Ops can diagnose issues without content access.

## Output Requirements

Before stopping, report:

1. Hero workflows tested (what they cover)
2. Performance safeguards added (indexes, pagination, N+1 fixes)
3. Offboarding flow (export, retention, deletion)
4. Config versioning / mutation safeguards
5. Observability signals added (what, where)
6. What was intentionally NOT touched

## Stop Conditions

* If retention durations, export formats, or legal policy must be decided: STOP AND ASK.
* Do not proceed to any further work.
* No shortcuts that weaken privacy, audit, billing, or tenancy guarantees.

---

**At this point, the system is:**
* architecturally sound
* privacy-defensible
* commercially viable
* operationally mature

✅ **END OF BUILD**
