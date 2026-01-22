# Critique Packet (CRITIQUE_PACKET)

Purpose: help external reviewers critique the platform coherently.

## What to evaluate
1. Core object graph correctness (Account/Contact/Engagement/EngagementLine/WorkItem)
2. Tenancy isolation and governance sufficiency
3. Permission model (staff RBAC + portal scopes) correctness and failure modes
4. Pricing determinism + auditability (rules + trace + quote snapshot)
5. Recurrence dedupe and DST correctness
6. Orchestration retry safety + DLQ + compensation boundaries
7. Documents governance (versioning/locking/access logs) and portal visibility rules
8. Billing ledger explainability and idempotency

## Known open questions
See OPEN_QUESTIONS.md.

## How to submit critique
Provide:
- impacted spec section(s)
- what invariant you believe is missing/incorrect
- a concrete failure scenario
- suggested alternative with tradeoffs

---
