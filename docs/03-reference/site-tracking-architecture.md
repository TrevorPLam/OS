# Site & Event Tracking Architecture
**Document Type:** Reference  
**Version:** 1.0.0  
**Last Updated:** 2026-01-05  
**Owner:** Platform Architecture  
**Status:** Draft (Ready for implementation)  
**Dependencies:** READMEAI.md; TODO.md; CODEBASECONSTITUTION.md; docs/03-reference/platform-capabilities.md

## Purpose
Defines the end-to-end architecture for web tracking across ConsultantPro properties (marketing site, app shell, embedded widgets). Covers SDK responsibilities, data contracts, privacy controls, storage, and downstream automation hooks.

## Goals & Non-Goals
- **Goals**
  - Standards-based event capture with firm-aware isolation.
  - Consent-aware data collection (GDPR/CCPA ready).
  - Durable visitor/session identity to support attribution and automation.
  - Minimal surface area for embedders (one script tag + config).
  - Observable pipeline with replay-safe ingestion.
- **Non-Goals**
  - Replacing existing analytics vendors.
  - Cross-property user stitching beyond first-party contexts.

## Architecture Overview
1. **Client SDK (`@consultantpro/tracking`)**
   - Lightweight ES module + UMD bundle.
   - Collects page views and custom events.
   - Manages visitor + session identifiers (UUIDv4) with rolling session window (30 minutes of inactivity).
   - Consent gate (`required`, `denied`, `granted`) enforced before emission.
   - Transports events over HTTPS to `/api/v1/tracking/collect/` with a firm-issued public key.
2. **Ingestion API**
   - Token-protected endpoint accepting batched or single events.
   - Validates firm slug + public tracking token + schema.
   - Normalizes timestamps to UTC; captures user agent and IP (anonymized at /24 for IPv4, /48 for IPv6).
   - Emits structured log for observability and dispatches automation triggers.
3. **Storage Model**
   - `TrackingSession` (firm, visitor_id, session_id, consent_state, first_seen_at, last_seen_at, user_agent_hash).
   - `TrackingEvent` (firm, session, event_type, name, url, referrer, occurred_at, properties JSONB, contact optional).
   - Indexes on `(firm, occurred_at)`, `(firm, event_type)`, `(firm, url)` for analytics queries.
4. **Analytics Surfaces**
   - Dashboard API provides rollups: daily page views, unique visitors, top pages, event leaderboard, referrers, and recent timeline.
   - Frontend dashboard consumes the API to render charts and tables with timezone-aware formatting.
5. **Automation Hooks**
   - Ingestion emits `site_page_view` or `site_custom_event` into Automation TriggerDetector with idempotency key: `<firm>-<session>-<event_name>-<occurred_at>`.
   - Workflow triggers can filter on URL path, event name, and properties (e.g., UTM campaign).

## Event Contracts
| Field | Type | Notes |
| --- | --- | --- |
| `firm_slug` | string | Required; identifies tenant |
| `tracking_key` | string | Required; firm-scoped public key |
| `session_id` | UUID | Optional; SDK auto-generates |
| `visitor_id` | UUID | Optional; stable across sessions |
| `event_type` | enum | `page_view`, `custom_event`, `identity` |
| `name` | string | Page title or event name |
| `url` | string | Full URL |
| `referrer` | string | Optional |
| `properties` | object | Free-form JSON with guarded size (16KB limit) |
| `consent_state` | enum | `pending`, `granted`, `denied` |
| `occurred_at` | datetime | RFC 3339; defaults to server receive time |

## Privacy & Compliance
- Consent is required before non-essential event emission; SDK exposes `setConsent(state, metadata?)`.
- IP addresses are truncated for analytics storage; raw IP only used transiently for rate limiting.
- Cookies/localStorage key: `cp_track_id` (visitor) and `cp_session_id` (session) with 1-year and 30-minute TTLs respectively.
- UTM parameters persisted to session for attribution; redaction rules applied to query parameters containing `token`, `secret`, `password`.

## Failure & Resilience
- SDK queues up to 50 events in-memory with retry + exponential backoff and jitter.
- Network failures fallback to `navigator.sendBeacon` when available.
- Ingestion applies request-level rate limits (per token) and enforces payload size (64KB).
- All writes are idempotent on `(firm, session_id, event_name, occurred_at)` to prevent double counting.

## Observability
- Structured log for every ingestion attempt: `tracking.ingest` with status, firm, session, event_type, latency, and normalized IP block.
- Metrics: request rate, success/error rate, p95 latency, top validation failures.
- Dashboards: ingestion health + top event cardinality to detect abuse.

## Deployment & Configuration
- Required env vars:
  - `TRACKING_PUBLIC_KEY` — firm-distributed key for SDK requests.
  - `TRACKING_INGEST_RATE_LIMIT_PER_MINUTE` — default 300.
  - `TRACKING_MAX_PROPERTIES_BYTES` — default 16384 bytes.
- Feature flags:
  - `tracking.ingest.enabled` — gate ingestion endpoint.
  - `tracking.automation.enabled` — controls automation emission.

## Rollout Plan
1. Ship SDK + ingestion endpoint behind feature flag for internal tenants.
2. Enable dashboard API + UI for firm admins.
3. Roll out automation triggers with conservative rate limits and alerting.
4. Add cross-domain session continuity (link tracking key across portals).
5. Backfill existing marketing site events via server logs if needed.
