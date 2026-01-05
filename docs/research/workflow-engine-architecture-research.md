# Workflow Engine Architecture Research (Event-Driven vs Polling)

**Status:** Research Complete
**Last Updated:** January 5, 2026
**Owner:** Automation Platform
**Canonical Status:** Supporting
**Related Tasks:** Workflow Engine Architecture (Research), future ORCH-* implementation tasks
**Priority:** MEDIUM

## Objectives

- Compare event-driven and polling-based workflow execution models for ConsultantPro automations.
- Recommend a scalable orchestration approach that aligns with multi-tenant isolation and auditability.

## Findings

1. **Event-Driven Model:** Works best with durable queues (e.g., Redis Streams/Celery or Kafka). Provides near-real-time triggers and natural backpressure. Requires idempotent handlers and explicit retry policies.
2. **Polling Model:** Simpler to bootstrap but wastes resources and introduces latency; prone to duplicate execution without strict leases.
3. **Determinism:** Workflows should be defined as declarative DAGs with versioned steps; store execution history for replay and audit.
4. **Isolation:** Tenants must be isolated at queue/topic level; per-tenant concurrency limits prevent noisy neighbors.
5. **State Management:** Use a durable state store (PostgreSQL) with explicit run states (`pending`, `running`, `retrying`, `failed`, `succeeded`) and correlation IDs for traceability.

## Recommendation

- Adopt an **event-driven** orchestrator backed by Celery + Redis (short-term) with abstraction layer to support Kafka migration later.
- Define workflows as YAML/JSON definitions stored in `src/modules/orchestration/models.py` with schema validation and signed versions.
- Implement deterministic runners that hydrate context from firm-scoped data, emit structured events, and persist checkpoints every step.
- Provide a replay API that re-queues failed steps with idempotency keys and bounded retries.

## Operational Controls

- **Observability:** Emit metrics for queue depth, handler latency, retry counts, and DLQ volume; expose dashboards per tenant.
- **Safety:** Enforce rate limits per tenant; guardrails for external API calls (timeouts, circuit breakers) within task handlers.
- **Extensibility:** Plugin interface for new triggers/actions; enforce permission checks before executing firm data mutations.

## Acceptance Criteria

- Documented comparison and chosen approach (event-driven with Celery abstraction).
- Persistence, isolation, and observability strategies defined for implementation.
- Replay, rate limiting, and plugin model captured to inform backlog tasks.
