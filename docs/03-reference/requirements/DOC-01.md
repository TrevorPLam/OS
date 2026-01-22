# Unified Operations Suite (UBOS) — Monorepo

This repository contains the specification-first, multi-tenant platform for running a professional-services firm end-to-end: CRM → intake/qualification → pricing/quoting → engagements/projects/work → documents → communications → calendar → billing/ledger, with a client portal and a staff app.

The repo is organized as a publishable documentation system (canonical specs + implementation blueprints), not a loose collection of notes. If something isn’t implemented yet, it should still be defined in the specs with clear boundaries and invariants.

## What this platform is (technical)

At a high level: **two apps + one brain**.

- **Staff App**: internal firm UI for pipeline, client/account management, engagements, work execution, billing, documents, communications, calendar, and knowledge (SOPs/training).
- **Client Portal**: external client UI for messaging, uploads, booking, payments, and visibility into allowed work artifacts.
- **The Brain (platform services)**: shared domain model, permissions, pricing rules, recurrence and orchestration engines, storage/document semantics, integrations (email/calendar), and background workers.

Key architectural principles:

- **Multi-tenancy**: firm-scoped row-level isolation (every model has a `firm` ForeignKey; isolation enforced at query layer via FirmScopedQuerySet). See ADR-0010 in docs/03-reference/requirements/DOC-04.md.
- **Core object graph** (canonical): `Account / Contact / Engagement / EngagementLine / WorkItem`
- **Eventing + background jobs**: async processing for ingestion, sync, recurrence generation, orchestration steps, and notifications.
- **Auditability and governance**: explicit data classification, retention rules, soft delete semantics, and access logging.

## Current status

This is an evolving repository. Expect some areas to be “spec-defined but not implemented.” The intent is to keep the system critique-able and buildable at every stage by treating specs as the source of truth.

## Repository map (high-level)

This is a monorepo. Exact folder names may vary as the structure stabilizes, but the intended layout is:

- `apps/`
  - `staff/` — Staff App (firm-side UI)
  - `portal/` — Client Portal (client-side UI)
- `packages/` (shared libraries)
  - `domain-core/` — entities, invariants, state machines (no DB calls)
  - `permissions/` — RBAC registry, scopes, evaluation rules
  - `pricing-engine/` — versioned JSON rules + evaluator + trace output
  - `recurrence-engine/` — period rules, dedupe constraints, generation workers
  - `orchestration-engine/` — step execution, retries, DLQ, idempotency
  - `storage/` — document/storage adapter contracts, signed URL policies
  - `integrations/` — email/calendar sync, ingest, mapping and logs
- `infrastructure/`
  - database schema provisioning, migrations, queues, deployment scaffolding
- `docs/`
  - canonical specs, blueprints, quality, and product IA maps

If you don’t see a directory yet, treat this as the target structure; the docs define the responsibilities and boundaries.

## How to run locally (placeholder)

Local run instructions will be added once the dev environment is stabilized.

Planned local workflow:

1. Install dependencies (root + app-specific).
2. Provision local database (including tenant schema provisioning).
3. Run migrations.
4. Start API + workers.
5. Start Staff App and Client Portal.

When available, this section will include exact commands, required environment variables, and seeded demo data.

## Documentation (start here)

If you are reviewing, critiquing, or contributing, use this path:

1. `DOCS_INDEX.md` (or `docs/README.md`) — documentation table of contents + reader paths  
2. `ARCHITECTURE_OVERVIEW.md` — “two apps + one brain,” tenancy, object graph, eventing  
3. `SYSTEM_SPEC.md` — canonical consolidated spec (normative “must/should/may”)  
4. `DECISION_LOG.md` — ADR-lite decisions (what’s fixed vs open)

Key canonical specifications (source of truth):

- `DOMAIN_MODEL.md` — entities, relationships, state machines, invariants
- `DATA_GOVERNANCE.md` — PII classification, retention/anonymization/erasure, audit rules
- `PERMISSIONS_MODEL.md` — RBAC registry, portal scopes, document permission evaluation
- `PRICING_ENGINE_SPEC.md` — versioned JSON rule schema, evaluation context, trace output
- `RECURRENCE_ENGINE_SPEC.md` — period rules, timezone policy, idempotency/dedupe semantics
- `ORCHESTRATION_ENGINE_SPEC.md` — steps/retries/DLQ, idempotency, compensation boundaries
- `DELIVERY_TEMPLATES_SPEC.md` — template DAG validation + instantiation into WorkItems
- `BILLING_LEDGER_SPEC.md` — invoice/payment/retainer ledger model + reporting outputs
- `DOCUMENTS_AND_STORAGE_SPEC.md` — versioning/locking, signed URLs, malware hooks, access logs
- `EMAIL_INGESTION_SPEC.md` — artifact storage, mapping, confidence scoring, triage, remap audit
- `CALENDAR_SYNC_SPEC.md` — external_event idempotency, sync logs, retries, manual resync tooling

Product surface maps (UI/UX blueprints):

- `STAFF_APP_INFORMATION_ARCHITECTURE.md`
- `CLIENT_PORTAL_INFORMATION_ARCHITECTURE.md`
- `ROLE_BASED_VIEWS.md`

## Core workflows (conceptual)

- **CRM → Engagement**: deals/opportunities become an Engagement with EngagementLines (service lines), which generate WorkItems (execution units).
- **Pricing → QuoteVersion**: pricing rules evaluate to a quote output with trace; snapshots are immutable once accepted.
- **Work execution**: WorkItems move through defined states; orchestration can enforce sequencing, retries, approvals.
- **Documents**: versioned artifacts with locking and access logging; portal visibility is permission-gated.
- **Communications**: native chat threads plus email ingestion; attachments are stored as governed artifacts.
- **Calendar**: booking + sync; external events map via stable IDs with retryable sync logs.
- **Billing/ledger**: invoices, payments, retainers recorded as ledger entries with allocation constraints and audit outputs.

## Design boundaries (non-negotiable)

- Domain packages should not depend on UI frameworks.
- `domain-core` must not call the database directly.
- Permission checks must be enforceable server-side (UI is never the authority).
- Background jobs must be idempotent; retries must be safe by design.
- All money movement must be ledgered; derived reports must be explainable from entries.

## Contributing (placeholder)

When collaborators are added, this repo will include:

- `CONTRIBUTING.md` — branching, PR requirements, spec/ADR change process
- `CODEOWNERS` — owners by folder/domain
- `CHANGELOG.md` — versioned spec and implementation milestones
- `CRITIQUE_PACKET.md` — structured external review format
- `OPEN_QUESTIONS.md` — short list of unresolved decisions with consequences

For now: if you propose a change, also propose the matching spec edit and (when relevant) a decision-log entry.

## Security and privacy

This platform is intended for regulated, audit-sensitive workflows. Treat all client data as sensitive by default. Security requirements and threat model live in `SECURITY_MODEL.md` (when present) and in the governance/permissions specs.

## License (placeholder)

License will be specified once the collaboration and distribution model is finalized.
