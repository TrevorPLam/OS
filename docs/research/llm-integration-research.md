# LLM Integration Research (Meeting Prep & Content Generation)

**Status:** Research Complete
**Last Updated:** January 5, 2026
**Owner:** AI/Automation
**Canonical Status:** Supporting
**Related Tasks:** LLM Integration (Research), LLM-1, LLM-2
**Priority:** MEDIUM

## Objectives

- Identify a safe and cost-aware path for integrating GPT-4 class models for meeting preparation and content generation.
- Define guardrails for data handling, prompt safety, and tenant isolation.
- Recommend delivery patterns that balance latency with auditability.

## Findings

1. **Model Access:** GPT-4 Turbo with structured output (JSON schema) is available via OpenAI API; Azure OpenAI provides private networking for enterprise tenants.
2. **Content Boundaries:** Meeting prep should limit context to firm-scoped CRM, calendar, and document summaries; redact PII where not strictly required.
3. **Prompt Safety:** Use system prompts enforcing role, tone, and banned topics; apply input/output filters for secrets, PHI, and customer-specific blocklists.
4. **Caching:** Response caching is valuable for agenda summaries and follow-ups; cache keys must include firm, meeting ID, and semantic hash of inputs.
5. **Cost Controls:** Token quotas per firm with soft/hard limits; meter usage by feature flag and surface in admin billing reports.

## Recommended Architecture

- **Service Layer:** Create `src/modules/ai/services/llm_client.py` wrapping OpenAI/Azure OpenAI with retry/backoff, timeouts, and audit logging.
- **Task Orchestration:** Use Celery/async jobs for long-form content; synchronous path only for short suggestions to avoid UI blocking.
- **Safety Filters:** Add pre- and post-processors (PII redaction, profanity/offensive content filter) and a deterministic `safe_response` schema.
- **Observability:** Log prompt templates (hashed), token counts, latency, and model version; emit structured metrics for cost dashboards.
- **Fallbacks:** If LLM is unavailable, return cached result or deterministic template to prevent UI dead-ends.

## Risks & Mitigations

- **Data Leakage:** Mitigate with firm-scoped context builders, explicit allowlist of fields, and zero retention setting on API calls.
- **Hallucination:** Require evidence-linked bullet points; include citation slots in schema and validate presence before returning.
- **Cost Spikes:** Enforce rate limits per firm and per-user; background jobs can queue rather than fail fast when budgets are reached.
- **Latency:** Use streaming for UI suggestions; background job results delivered via notifications/webhooks to avoid blocking flows.

## Acceptance Criteria

- Documented integration path with safety, cost, and observability guardrails.
- Clear module location (`src/modules/ai/`) and API surface expectations defined.
- Risks, mitigations, and fallbacks enumerated to inform implementation tasks.
