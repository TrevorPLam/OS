# Documentation Index (DOCS_INDEX)

This repository is documentation-led. Canonical specifications define what the platform is and the invariants it must satisfy. Implementation blueprints describe how to build it. Product surface maps describe navigation and role-based views without drifting into business advice.

If a file is missing, it should be created rather than inferred.

---

## Reader paths

Fast orientation (10–15 minutes)
1. README.md
2. ARCHITECTURE_OVERVIEW.md
3. DECISION_LOG.md

Architect / reviewer path (45–90 minutes)
1. SYSTEM_SPEC.md
2. DOMAIN_MODEL.md
3. PERMISSIONS_MODEL.md
4. DATA_GOVERNANCE.md
5. DOCUMENTS_AND_STORAGE_SPEC.md
6. BILLING_LEDGER_SPEC.md
7. EDGE_CASES_CATALOG.md
8. OPEN_QUESTIONS.md (if present)

Engineer path (45–120 minutes)
1. MONOREPO_STRUCTURE.md
2. API_CONTRACTS.md
3. DB_SCHEMA_AND_MIGRATIONS.md
4. WORKERS_AND_QUEUES.md
5. OBSERVABILITY_AND_SRE.md
6. TEST_STRATEGY.md
7. EDGE_CASES_CATALOG.md

Product / UX path (30–60 minutes)
1. STAFF_APP_INFORMATION_ARCHITECTURE.md
2. CLIENT_PORTAL_INFORMATION_ARCHITECTURE.md
3. ROLE_BASED_VIEWS.md
4. PERMISSIONS_MODEL.md (to understand gating)

---

## Document taxonomy

Normative (binding; code must comply)
- SYSTEM_SPEC.md
- DOMAIN_MODEL.md
- DATA_GOVERNANCE.md
- PERMISSIONS_MODEL.md
- PRICING_ENGINE_SPEC.md
- RECURRENCE_ENGINE_SPEC.md
- ORCHESTRATION_ENGINE_SPEC.md
- DELIVERY_TEMPLATES_SPEC.md
- BILLING_LEDGER_SPEC.md
- DOCUMENTS_AND_STORAGE_SPEC.md
- EMAIL_INGESTION_SPEC.md
- CALENDAR_SYNC_SPEC.md

Explanatory (mental models; not binding)
- ARCHITECTURE_OVERVIEW.md

Blueprints (how to build; patterns, boundaries, conventions)
- MONOREPO_STRUCTURE.md
- API_CONTRACTS.md
- DB_SCHEMA_AND_MIGRATIONS.md
- WORKERS_AND_QUEUES.md
- OBSERVABILITY_AND_SRE.md

Quality (how to keep it correct)
- TEST_STRATEGY.md
- EDGE_CASES_CATALOG.md
- SECURITY_MODEL.md

Product surface maps (UI structure; not business strategy)
- STAFF_APP_INFORMATION_ARCHITECTURE.md
- CLIENT_PORTAL_INFORMATION_ARCHITECTURE.md
- ROLE_BASED_VIEWS.md

Repo operations / collaboration
- CONTRIBUTING.md
- CODEOWNERS
- CHANGELOG.md
- CRITIQUE_PACKET.md
- OPEN_QUESTIONS.md
- DECISION_LOG.md

---

## Platform entry-point docs

- README.md  
  What the platform is, repo map, local run placeholder, links to specs and decisions.

- ARCHITECTURE_OVERVIEW.md  
  “Two apps + one brain,” tenancy model, core object graph, eventing and workers at a high level.

- DECISION_LOG.md  
  ADR-lite: one entry per major decision with consequences and links.

---

## Canonical specifications (source of truth)

- SYSTEM_SPEC.md  
  Consolidated spec with explicit must/should/may statements, boundaries, and invariants.

- DOMAIN_MODEL.md  
  Entities + relationships, state machines, key invariants, forbidden transitions.

- DATA_GOVERNANCE.md  
  PII classification, retention/anonymization/erasure workflows, soft delete, audit retention rules.

- PERMISSIONS_MODEL.md  
  RBAC registry, portal permissions + scopes, document permission evaluation rules, simulator requirements.

- PRICING_ENGINE_SPEC.md  
  Versioned JSON rule schema, evaluation context, trace output, snapshotting into QuoteVersion, examples reference.

- RECURRENCE_ENGINE_SPEC.md  
  Period rules + timezone policy, dedupe constraints, generation semantics, pause/resume/cancel behaviors.

- ORCHESTRATION_ENGINE_SPEC.md  
  Execution model (steps, retries, DLQ), error classification, idempotency, compensation boundaries.

- DELIVERY_TEMPLATES_SPEC.md  
  Template DAG model, validation rules, instantiation semantics into WorkItems.

- BILLING_LEDGER_SPEC.md  
  Ledger entries (invoice/payment/retainer), allocations, reporting outputs, audit requirements.

- DOCUMENTS_AND_STORAGE_SPEC.md  
  Storage adapter contract, versioning + locking, signed URLs, malware scanning hooks, access logging.

- EMAIL_INGESTION_SPEC.md  
  Artifact storage, mapping suggestions, confidence scoring, staleness/triage rules, remap workflow + audit.

- CALENDAR_SYNC_SPEC.md  
  External event idempotency, sync attempt log schema, retries, manual resync tooling.

---

## Implementation blueprints

- MONOREPO_STRUCTURE.md  
  Apps/packages responsibilities, dependency boundaries, code ownership map.

- API_CONTRACTS.md  
  Endpoint groups per domain, auth/permission enforcement patterns, event emission patterns, pagination/filtering/sorting conventions.

- DB_SCHEMA_AND_MIGRATIONS.md  
  Schema-per-tenant provisioning workflow, migration runner design, index/constraint standards, naming conventions.

- WORKERS_AND_QUEUES.md  
  Job types + payload schemas, priorities, concurrency model, advisory locks/SKIP LOCKED usage, DLQ and reprocessing rules.

- OBSERVABILITY_AND_SRE.md  
  Required metrics/dashboards, alert thresholds, log correlation IDs, audit log access patterns.

---

## Testing, security, and correctness

- TEST_STRATEGY.md  
  Unit/integration/e2e boundaries, contract tests (pricing/permissions/recurrence), deterministic time/timezone testing.

- EDGE_CASES_CATALOG.md  
  Recurrence DST/leap-year cases, email threading staleness, permission pitfalls, ledger idempotency cases.

- SECURITY_MODEL.md  
  Threat model summary, secrets handling, audit and breach response hooks.

---

## Product surface maps

- STAFF_APP_INFORMATION_ARCHITECTURE.md  
  Navigation map, module definitions + cross-links, shared “Client Profile editor” pattern.

- CLIENT_PORTAL_INFORMATION_ARCHITECTURE.md  
  Permission-gated navigation, account switcher behavior, common flows (message/upload/book/pay).

- ROLE_BASED_VIEWS.md  
  Which roles see which modules; least-privilege defaults.

---

## Reviewer packets (optional but recommended)

- CRITIQUE_PACKET.md  
  What to evaluate, known open questions, invariants to test, how to submit critique.

- OPEN_QUESTIONS.md  
  Only truly unresolved decisions; options + consequences; links to related specs/decisions.

---

## Cross-linking rules (to prevent drift)

1. SYSTEM_SPEC.md is the authoritative normative spec for cross-domain invariants.
2. Every normative doc must link back to SYSTEM_SPEC.md sections it refines.
3. Every major decision must have:
   - a DECISION_LOG entry, and
   - the corresponding spec updates (or an explicit “deferred” note).
4. If a decision is open, it lives in OPEN_QUESTIONS.md with a clear owner section and consequences.

---
