# Event Bus Architecture Design

**Status:** Complete (Design)  
**Last Updated:** January 5, 2026  
**Owner:** Platform Architecture  
**Canonical Status:** Supporting  
**Related Tasks:** EVENT-1 (Design unified event bus architecture), EVENT-2 through EVENT-5  
**Dependencies:** Django settings, src/modules/core/ event hooks, deployment infrastructure

## Purpose

Define a pragmatic event bus architecture that supports cross-module publishing and subscribing without breaking existing Django boundaries. This design delivers the CONTRACT for EVENT-1 and seeds implementation tasks for EVENT-2 through EVENT-5.

## Design Principles

1. **Boundary Safety** — UI and domain layers publish domain events; infrastructure adapters handle transport details.  
2. **Tenant Isolation** — Every event is scoped to a firm_id with guardrails that prevent cross-tenant leakage.  
3. **Contract-First** — Event schemas live in `spec/contracts/` and are versioned; breaking changes require explicit version bumps.  
4. **At-Least-Once Delivery** — Retry with idempotency keys at the consumer boundary to avoid duplicates.  
5. **Operational Observability** — Correlation IDs, metrics (publish rate, DLQ depth), and structured logs are mandatory.

## Target Topology

- **Broker:** Kafka (preferred) with a single `consultantpro` cluster and per-domain topics (e.g., `crm.deal.updated`, `projects.task.completed`). RabbitMQ is an acceptable interim if Kafka is unavailable; topic naming remains the same to preserve compatibility.  
- **Publisher Adapter:** Django signal hooks (or domain service emitters) call a lightweight publisher service in `src/modules/core/events/publisher.py` that:
  - Validates payload against contract schema.
  - Enriches with metadata: `event_id`, `firm_id`, `occurred_at` (UTC), `trace_id`, `schema_version`.
  - Writes to broker with retries + exponential backoff.
- **Subscriber Adapter:** Workers in `src/modules/core/events/consumer.py` consume topic groups aligned to modules (e.g., `crm-service`, `projects-service`) and:
  - Enforce idempotency via `(event_id, consumer_group)` keys.
  - Apply permission scoping before invoking application handlers.
  - Route to handler registry `src/modules/<module>/event_handlers.py`.
- **DLQ:** Per-topic dead-letter queues (`<topic>.dlq`) with retention and alerting on error thresholds.

## Event Schema & Versioning

- Authoritative schemas stored in `spec/contracts/events/<domain>/<event>.yaml` with:
  - `name`, `version`, `idempotency_key`, `firm_id`, `actor`, `payload`, `occurred_at`, `source`.  
  - Validation rules (required fields, enums, numeric ranges).  
- Version policy: breaking changes → new `version` and topic suffix (e.g., `crm.deal.updated.v2`); consumers must opt in explicitly.

## Security & Privacy Controls

- **Isolation:** Firm ID required for all events; consumer rejects missing/invalid firm scopes.  
- **PII Minimization:** Only include IDs and necessary metadata; content fields must be redacted or encrypted where feasible.  
- **AuthZ for Outbound Integrations:** When forwarding events externally, use signed webhooks with HMAC (align with webhook platform).  
- **Access Control:** Broker credentials are per-environment and rotated; ACLs restrict consumer groups to authorized topics.

## Operations & Monitoring

- Metrics: publish/consume throughput, latency percentiles, retry counts, DLQ depth, schema validation failures.  
- Alerts: DLQ growth, consecutive handler failures, broker connectivity loss, schema validation error rate >1%.  
- Runbooks: add entries to `docs/runbooks/` for broker outage, DLQ replay, and schema rollout.

## Phased Rollout

1. **Phase 0 (This Design):** Contracts defined, topic taxonomy approved.  
2. **Phase 1 (Pilot):** Enable publisher + consumer for a single domain (CRM deal events) using Kafka or RabbitMQ.  
3. **Phase 2 (Platform Adoption):** Expand to projects, documents, and automation triggers; enable DLQ dashboards.  
4. **Phase 3 (External Integrations):** Expose curated topics to webhook platform with HMAC + rate limiting.

## Acceptance Criteria (EVENT-1)

- Documented broker choice, topic naming, and schema/versioning strategy.  
- Publisher and consumer responsibilities scoped with firm-aware isolation.  
- Operational guardrails (DLQ, metrics, alerts) defined for later implementation.
