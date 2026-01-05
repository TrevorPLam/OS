# Coding Constitution

Version: 1.0  
Status: Canonical  
Scope: This document defines the non-negotiable rules for how this repository is built, changed, reviewed, tested, deployed, and operated. If a change conflicts with this constitution, the change is rejected or the constitution is explicitly amended via an ADR.

---

## 1) Purpose

This repository exists to produce software that is:

- **Buildable**: deterministically reproducible from a clean machine/CI runner.
- **Verifiable**: behavior is proven by contracts and tests, not promises.
- **Secure by default**: safe configuration and least privilege are the default state.
- **Operable**: failures are diagnosable and recoverable via runbooks and automation.
- **Evolvable**: architecture is clear, enforced, and changes remain localized.
- **Accountable**: sensitive actions are authorized and auditable.

---

## 2) Authority and Amendments

2.1 **Supremacy**  
This document outranks all other repo guidance unless explicitly superseded by a newer version of `CODEBASECONSTITUTION.md` or a formal ADR that amends it.

2.2 **Amendment Process**  
A rule may be changed only by:
- An ADR in `docs/05-decisions/` (or equivalent decision-log directory) that:
  - states the proposed change,
  - explains why the old rule is insufficient,
  - includes migration/transition steps,
  - includes a rollback plan if applicable.

2.3 **No Silent Exceptions**  
If a rule is broken, the PR must:
- label it as an exception,
- include evidence of impact,
- include a plan and date to remove the exception.

---

## 3) The Golden Rules (Non-Negotiable)

3.1 **No Hallucinated Code or Configuration**
- All changes must be grounded in repo evidence.
- Do not introduce “guess-based” code paths or configs without tests and docs.

3.2 **No Undocumented Behavior**
- If behavior matters, it must be documented and testable.
- Docs must point to the authoritative source (contract/tests), not hand-wavy claims.

3.3 **No Merge Without Proof**
A change may merge only if:
- build passes,
- tests pass,
- security gates pass,
- docs checks pass (where applicable),
- and the change is reviewable and traceable (see Section 7).

3.4 **No Unsafe Defaults**
- Production must be safe by default.
- If a feature is dangerous without configuration, it must be disabled by default.

3.5 **No Breaking Changes Without Versioning**
- All public interfaces (API, events, SDK) require compatibility planning.

---

## 4) Architecture Constitution

4.1 **Boundaries Must Be Explicit**
- Modules/services have defined responsibilities and owners.
- Cross-boundary dependencies are minimized and justified.

4.2 **Layering Rules**
Unless explicitly overridden by ADR, layering must follow:

- **UI / Delivery** (controllers, handlers, pages)  
  may call → **Application/Use Cases**
- **Application/Use Cases**  
  may call → **Domain Logic**
- **Domain Logic**  
  may call → **Ports/Interfaces**, not concrete frameworks
- **Infrastructure Adapters** (DB, queues, external APIs)  
  implement → ports/interfaces

4.3 **No Boundary Bypasses**
- UI must not call persistence directly.
- Domain must not import framework-specific modules directly (unless the framework is the deliberate domain substrate and this is documented).

4.4 **Shared Utilities Governance**
- No “misc utils dumping ground.”
- Shared code must be:
  - cohesive,
  - versioned within the repo,
  - and explicitly depended on by consumers.

4.5 **Extensibility by Design**
- New integrations/features should be additive (new module/adapter), not invasive refactors.

---

## 5) Configuration and Environment Constitution

5.1 **Configuration Schema is Mandatory**
- All runtime configuration must be declared in a schema:
  - name, type, required, default, secret flag, description.

5.2 **Fail-Fast Startup Validation**
- The application must refuse to start if configuration is invalid or incomplete.

5.3 **Environment Parity**
- Dev/staging/prod must share the same configuration shape.
- Differences are values, not missing keys.

5.4 **Secrets Discipline**
- Secrets must not be committed.
- Secrets must not be printed in logs.
- Secrets must be rotatable by policy and tooling.

5.5 **Time and Locale Discipline**
- Store timestamps in UTC.
- Convert at the edge (UI/reporting).
- Any scheduling logic must be DST-safe and tested.

---

## 6) Security Constitution

6.1 **Authentication and Authorization**
- Authentication must be consistent across all entry points.
- Authorization must be centralized, least-privilege, and test-covered.
- Any sensitive action must be authorized and auditable.

6.2 **Injection and Input Safety**
- Validate inputs at boundaries.
- Encode outputs appropriately for the sink (HTML/JSON/SQL).
- Prefer safe framework primitives over custom implementations.

6.3 **Session Safety**
- Secure cookie flags and sensible TTLs are mandatory.
- Token rotation and revocation must be supported (as relevant).

6.4 **Abuse Protections**
- Rate limiting, throttling, and/or quotas must exist where endpoints can be abused.
- Any expensive endpoint must have hard limits.

6.5 **File Handling Safety (If Applicable)**
- Validate file types (server-side).
- Prevent path traversal.
- Malware scanning or strict sandboxing if files are user-supplied.
- Never trust client MIME types.

6.6 **Continuous Security Gates**
CI must include:
- secret scanning,
- dependency vulnerability scanning,
- SAST (or equivalent),
- IaC scanning if infrastructure exists.

6.7 **Threat Model**
- A threat model must exist and be updated for major changes.
- Each mitigation must point to code/tests.

---

## 7) Contracts and Compatibility Constitution

7.1 **Contracts are the Source of Truth**
- API schemas (OpenAPI/GraphQL) define the contract.
- Event/webhook schemas define payload expectations.

7.2 **Contract Tests are Mandatory**
- Provider tests validate the implementation matches the schema.
- Consumer/compat tests exist for SDKs or external dependencies where feasible.

7.3 **Backward Compatibility Policy**
- Breaking changes require:
  - versioning,
  - a migration path,
  - a deprecation window (time- or release-count-based),
  - and explicit communication in release notes.

7.4 **Error Model Discipline**
- Errors must be machine-readable and consistent.
- Avoid “everything is 500.”

7.5 **Pagination and Limits**
- List endpoints must have pagination and maximum limits.
- Never allow unbounded reads by default.

7.6 **Webhook Safety**
- Verify webhook signatures.
- Enforce idempotency.
- Provide replay tooling for recoverability.

---

## 8) Data Integrity Constitution

8.1 **Constraints First**
- Use database constraints (FK, UNIQUE, CHECK) to prevent invalid states.
- Application validation complements constraints; it does not replace them.

8.2 **Migration Safety Policy**
- Migrations must be safe for production:
  - avoid long locks,
  - use backfills for large changes,
  - document irreversible migrations explicitly.

8.3 **Idempotency Everywhere It Matters**
- Any write that can be retried must support idempotency keys or dedupe strategy.

8.4 **Transaction Boundaries Must Be Correct**
- Multi-step operations must not partially commit without compensation strategy.

8.5 **Concurrency Control**
- Critical aggregates must have optimistic concurrency control (or equivalent).
- “Last write wins” must be explicit and justified.

8.6 **Retention and Deletion**
- If regulated or sensitive data exists, retention and deletion must be implemented and auditable.

---

## 9) Reliability and Resilience Constitution

9.1 **Timeouts are Mandatory**
- All remote calls must have timeouts.

9.2 **Retries are Disciplined**
- Retries must include jitter and budgets.
- Do not retry non-idempotent operations without safeguards.

9.3 **Graceful Degradation**
- One failing dependency must not take down the entire system where avoidable.
- Define critical vs non-critical dependencies.

9.4 **Health Checks**
- Liveness and readiness checks must be correct and meaningful.
- Readiness must reflect dependency availability where needed.

9.5 **Async Systems (If Applicable)**
- Jobs must have:
  - retry policy,
  - DLQ strategy,
  - replay tooling,
  - and poison-message handling.

9.6 **Multi-Step Workflow Safety**
- Sagas/compensation or equivalent must exist where partial failure would corrupt state.

---

## 10) Testing Constitution (The Safety Net)

10.1 **CI Runs the Truth**
- Tests must run in CI and gate merges.

10.2 **Coverage Where it Counts**
- Critical modules must be explicitly covered:
  - auth/authz,
  - data integrity,
  - payments/billing/compliance,
  - tenancy/isolation if applicable.

10.3 **Determinism**
- Tests must be deterministic:
  - frozen time,
  - seeded randomness,
  - hermetic dependencies where feasible.

10.4 **Contract Tests**
- Contract tests are mandatory for APIs/events/webhooks.

10.5 **Regression Discipline**
- Every bug fix adds a regression test.
- Regression tests must reproduce the failure and verify the fix.

10.6 **Elite Testing (Optional but Preferred)**
- Property-based tests for invariants.
- Mutation testing for critical logic.
- Perf regression tests for hot paths.

---

## 11) CI/CD and Release Constitution

11.1 **Merge Gating**
- No merges without CI green on required checks.

11.2 **Build Once, Promote**
- The same artifact is promoted from staging to production (no rebuild drift).

11.3 **Versioning and Provenance**
- Releases are versioned and traceable to commits.
- Prefer SBOM generation and artifact signing where feasible.

11.4 **Rollback**
- Rollback is defined, rehearsed, and scripted where possible.

11.5 **Migration Coordination**
- Deploy and migrations follow a defined ordering and safety policy.

11.6 **Feature Flags**
- Feature flags must have:
  - owners,
  - cleanup dates,
  - and removal plans.

---

## 12) Observability and Operations Constitution

12.1 **Structured Logging**
- Logs must be structured (JSON or equivalent).
- Logging schema must be stable across versions.

12.2 **Correlation IDs**
- Requests must carry correlation IDs across service boundaries.

12.3 **Metrics and Tracing**
- Key SLO metrics exist:
  - latency,
  - error rate,
  - saturation,
  - queue depth/backlog (if async).
- Distributed tracing exists if the system is distributed.

12.4 **Dashboards and Alerts as Code**
- Dashboards and alert rules are stored as code where feasible.
- Every alert has a runbook.

12.5 **No Sensitive Data in Logs**
- Redaction is centralized and enforced.
- Sensitive logs are blocked by tests/gates.

12.6 **Runbooks**
- Runbooks exist for:
  - common failures,
  - critical workflows,
  - incident response and recovery.

---

## 13) Privacy/Multi-Tenant/Audit Guarantees (Enable if Applicable)

This section applies if the product claims any of the below. Mark each as:
- **ENABLED**: enforced and tested
- **PLANNED**: documented but not enforced
- **NOT APPLICABLE**: does not apply

13.1 **Multi-Tenant Isolation**
- Tenant boundaries are enforced in code and tested with cross-tenant attack suites.
- Defense-in-depth is preferred (application scoping + optional DB-level policies).

13.2 **Privacy Non-Leakage**
- “No content logging” is enforced by tests.
- Redaction is centralized and used everywhere.

13.3 **Strong Auditability**
- Sensitive actions are logged in an append-only audit trail.
- Break-glass access (if any) is time-bound, approved, and audited.

13.4 **Immutability of Facts**
- Ledgers/facts are append-only; corrections are additive, not edits.
- Constraints and property tests enforce immutability invariants.

13.5 **Encryption Key Lifecycle**
- Envelope encryption and KMS strategy (or equivalent).
- Rotation/rewrap tooling exists, resumable, audited.

13.6 **Integration Reconciliation**
- Drift detection, replay tooling, and sandbox/prod parity checks exist.

---

## 14) PR Checklist (Enforced Expectations)

A PR must include:
- Evidence of correctness (tests or reproducible manual proof)
- Docs updates if behavior changes
- Migration notes if schema changes
- Rollout/rollback notes for user-impacting changes
- Security impact notes for auth/data surface changes

---

## 15) Minimal Enforcement Plan (Recommended)

To ensure this constitution is not aspirational, implement:
- CI check: fails if required directories/docs are missing
- CI check: fails if OpenAPI schema drift is detected
- CI check: fails if secrets are detected
- CI check: fails if unsafe prod config flags are enabled
- CI check: boundary rules (forbidden imports) enforced by tooling

---

## 16) Quick Reference: “Perfect Change” Standard

A change is “perfect” when:
- It is traceable (issue/spec/ADR linked)
- It is safe (tests + gates + rollback)
- It is compatible (contracts + versioning)
- It is operable (logs/metrics/runbook impact considered)
- It is aligned with invariants and constraints

---

End of document.