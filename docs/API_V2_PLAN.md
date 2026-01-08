# API v2 Plan

**Status:** Draft
**Owner:** AGENT
**Purpose:** Define the scope, timeline, and migration plan for API v2 while maintaining stability for existing v1 consumers.

## Objectives
- Outline the breaking changes required for v2.
- Set a deprecation and migration timeline for v1 consumers.
- Provide a migration guide and dual-run strategy.
- Identify v1 endpoints that will be replaced and define the `/api/v2/` URL structure.

## Breaking changes planned for v2
- **Stronger boundary between staff and portal APIs.** v1 routes place portal endpoints inside the main version namespace (`/api/v1/portal/`). v2 will isolate portal routes under `/api/v2/portal/` with portal-specific auth, rate limits, and CSRF/cookie defaults to prevent accidental cross-surface access.
- **Normalize routing through the API layer.** Several v1 routes include `modules.*.urls` directly instead of the `api.*` layer (e.g., pricing, calendar, email ingestion). v2 will expose all domains through `api.<domain>.urls` wrappers to enforce consistent serializers, permissions, and audit logging.
- **Consistent payload and error envelopes.** v2 responses will adopt a uniform envelope (`{"data": ..., "meta": ...}`) with typed error codes; clients must update deserialization accordingly.
- **Version negotiation rules.** v2 will require explicit `X-API-Version: v2` or `/api/v2/` path usage; silent fallback to v1 will be removed to avoid mismatched expectations.
- **Webhooks separation.** New v2-specific webhook URLs will be added under `/api/v2/webhooks/` with signed timestamp validation; legacy webhook paths will be deprecated after integrations are migrated.

## Deprecation timeline
- **Month 0 (v2 beta):** Publish `/api/v2/` docs and enable opt-in header-based usage alongside `/api/v2/` URLs. Start emitting `Deprecation` headers on targeted v1 endpoints.
- **Month 2 (general availability):** Mark v1 endpoints as deprecated in OpenAPI schema. Enable logging/alerts for v1 traffic.
- **Month 6:** Disable new feature rollout on v1; require exception to add new fields. Continue serving v1 with stability fixes only.
- **Month 12:** Retire targeted v1 endpoints after traffic is drained. Maintain `/api/v1/` portal read-only access for an additional 60 days to ensure stragglers can migrate.

## Policy compliance check (API_VERSIONING_POLICY.md)
- **Minimum support window:** v1 remains supported for at least 12 months after v2 GA (matches policy).
- **Deprecation notice:** v1 consumers receive at least 6 months notice before endpoint retirement (matches policy + API_DEPRECATION_POLICY.md).
- **Version identification:** v2 requires explicit `/api/v2/` path or `X-API-Version: v2` header; v1 remains the default for any unversioned traffic.
- **Parallel support:** v1 and v2 run concurrently with separate OpenAPI schemas until retirement.

## Migration guide
1. **Discover usage:** Inventory client calls to `/api/v1/` and `/api/public/` using access logs and API keys.
2. **Adopt new URLs:** Switch client base paths to `/api/v2/` (portal clients use `/api/v2/portal/`).
3. **Update authentication:** Use cookie-based or token-based auth flows defined for v2; remove assumptions about localStorage tokens.
4. **Normalize payload handling:** Expect the v2 response envelope and updated error codes; adjust pagination parsing accordingly.
5. **Re-test webhooks:** Re-register webhook endpoints against `/api/v2/webhooks/...` URLs and verify signature validation.
6. **Roll out gradually:** Enable v2 per client or per feature flag, monitor logs/metrics, then remove v1 usage.

## Parallel running strategy
- **Dual routers:** Keep `/api/v1/` and `/api/v2/` mounted simultaneously. Shared business logic lives in modules; serializers/adapters keep contract differences isolated.
- **Traffic gating:** Allow per-client or per-key routing to v2 to contain blast radius. Use feature flags for risky operations (payments, document uploads).
- **Observability:** Maintain separate metrics/alerts for v1 vs v2 latency, error rates, and webhook failures to inform deprecation readiness.
- **Schema publication:** Host v1 and v2 OpenAPI schemas at `/api/schema?v=1` and `/api/schema?v=2` (or distinct routes) so consumers can pin versions.

## Candidate v1 endpoints for deprecation
These endpoints will keep serving during the migration window but are planned to be superseded by `/api/v2/` equivalents:
- `/api/v1/portal/*` — replaced by isolated portal surface with cookie defaults and stricter rate limits.
- `/api/v1/pricing/*`, `/api/v1/calendar/*`, `/api/v1/email-ingestion/*`, `/api/v1/communications/*`, `/api/v1/knowledge/*`, `/api/v1/support/*`, `/api/v1/onboarding/*`, `/api/v1/marketing/*`, `/api/v1/automation/*`, `/api/v1/snippets/*`, `/api/v1/sms/*`, `/api/v1/tracking/*`, `/api/v1/accounting/*`, `/api/v1/esignature/*`, `/api/v1/ad-sync/*`, `/api/v1/integrations/*` — refactored to route through `api.<domain>.urls` wrappers with consistent auth/serialization instead of direct module exposure.
- `/api/public/*` — re-homed to `/api/v2/public/*` with CSRF protection and download/upload rate limits; v1 path marked deprecated.
- Webhooks under `/webhooks/stripe/` and `/webhooks/docusign/` — moved to `/api/v2/webhooks/{provider}/` with signed timestamp enforcement.

## `/api/v2/` URL structure
- **Base:** `/api/v2/`
- **Staff:** `/api/v2/{domain}/` (CRM, clients, projects, finance, documents, assets, etc.)
- **Portal:** `/api/v2/portal/{resource}/`
- **Public:** `/api/v2/public/{resource}/` (file requests, shares, opt-in, unsubscribe)
- **Webhooks:** `/api/v2/webhooks/{provider}/`
- **Docs:** `/api/docs/v2/`, `/api/redoc/v2/`, `/api/schema?v=2`
