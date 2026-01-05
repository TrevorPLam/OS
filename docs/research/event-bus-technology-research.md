# Event Bus Technology Research (Kafka vs RabbitMQ vs EventBridge)

**Status:** Research Complete
**Last Updated:** January 5, 2026
**Owner:** Platform Engineering
**Canonical Status:** Supporting
**Related Tasks:** Event Bus Technology (Research), INFRA-2
**Priority:** LOW

## Objectives

- Evaluate Kafka, RabbitMQ, and AWS EventBridge for ConsultantPro's event-driven architecture.
- Recommend a default event bus for internal workflows with a migration path if requirements evolve.

## Findings

1. **Kafka:** Strong ordering, partitioning, and replay support. Operationally heavy (ZooKeeper/KRaft) but excels at high-throughput streams and long retention. Ecosystem support for schema registry and exactly-once semantics (with care).
2. **RabbitMQ:** Simpler operations, supports complex routing via exchanges/bindings, and suits task-style workloads. Limited replay and retention; best for short-lived work queues.
3. **AWS EventBridge:** Fully managed with SaaS/event bus integrations; good for cross-account fan-out. Lacks on-prem parity and introduces cloud lock-in; latency higher than Kafka/RabbitMQ.
4. **Operational Fit:** Current stack already uses Celery/Redis. Kafka adds operational overhead but enables audit-friendly retention and event sourcing; RabbitMQ would simplify queue semantics but still requires management.

## Recommendation

- Start with **Kafka** for event sourcing and integration durability; pair with schema registry (e.g., Apicurio or Confluent) to enforce contracts.
- Keep **RabbitMQ** as an optional adapter for low-latency worker queues if Celery/Redis proves insufficient.
- Use **EventBridge** only for cloud-specific integrations where managed fan-out outweighs lock-in (documented per integration).

## Implementation Notes

- Standardize event envelope: `event_id`, `event_type`, `occurred_at`, `firm_id`, `actor`, `payload`, `schema_version`.
- Provide producer/consumer libraries under `src/modules/orchestration/events/` with idempotency keys and retry policies.
- Maintain topic naming convention (`firm.<id>.<domain>.<event>`); enforce retention and compaction policies per domain.

## Risks & Mitigations

- **Operational Overhead:** Mitigate with IaC templates and runbooks for scaling/partition rebalancing.
- **Schema Drift:** Enforce schema registry validation; contract tests per integration.
- **Backpressure:** Configure consumer lag alerts and DLQs; cap producer rates per tenant.

## Acceptance Criteria

- Comparative analysis with recommended default (Kafka) and fallback options recorded.
- Envelope, topic conventions, and client library expectations defined.
- Risks captured with mitigation guidance to inform INFRA-2 planning.
