# Site Message System & Builder
**Document Type:** Reference  
**Version:** 1.0.0  
**Last Updated:** 2026-01-08  
**Owner:** Web Personalization  
**Status:** Draft (Ready for implementation)  
**Dependencies:** READMEAI.md; P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md; CODEBASECONSTITUTION.md; docs/03-reference/site-tracking-architecture.md

## Purpose
Defines the server-side model and API support for Web Personalization tasks (PERS-1, PERS-2). Captures message types, targeting rules, builder configuration, and delivery constraints.

## Message Types
- **Modal** — centered overlay with optional dim background.
- **Slide In** — anchored to page edge (bottom-right default).
- **Banner** — horizontal strip (top or bottom of viewport).

## Data Model (Django)
- `SiteMessage` (firm FK, name, message_type, status `draft|published|archived`, targeting_rules JSON, content JSON, personalization_tokens list, form_schema JSON, frequency_cap, active_from, active_until, created_by).
- Indices on `(firm, status)` and `(firm, message_type)` for filtered dashboards.
- Frequency cap expressed as maximum displays per visitor per day.

## Targeting Rules
Rules stored as JSON with keys:
- `segments`: list of segment slugs/ids to include.
- `behaviors`: page URL contains, event name contains, minimum sessions/views.
- `audience`: flags for anonymous vs known contacts.
- `experiments`: optional variant labels for A/B testing alignment.

## Builder & API Contracts
- CRUD endpoints at `/api/v1/tracking/site-messages/` (auth required; firm context + `can_manage_settings`).
- Request schema:
  - `name` (string, required)
  - `message_type` (`modal|slide_in|banner`, required)
  - `status` (`draft|published|archived`, required)
  - `targeting_rules` (object, default `{}`)
  - `content` (object, structured blocks: headline/body/cta/buttons/images)
  - `personalization_tokens` (array of string paths, e.g., `contact.first_name`)
  - `form_schema` (object; fields, validation rules)
  - `frequency_cap` (int, default `1`)
  - `active_from` / `active_until` (datetime, optional)
- Responses include `id`, timestamps, and current status. Published updates preserve existing firm scoping.

## Delivery Considerations
- Messages are scoped per firm; cross-firm access is blocked at the query layer.
- Frontend renderer should enforce `frequency_cap` and `active_*` window locally in addition to server filters.
- Draft messages are not eligible for client delivery; published messages should be synced via SDK configuration or dedicated endpoint.
- Delivery endpoint: `POST /api/v1/tracking/site-messages/display/` (public, keyless). Request includes `firm_slug`, `visitor_id`, `session_id`, `url`, optional `segments` and `contact_id`.
  - Applies targeting: segments intersection, audience flags (anonymous vs known), behavioral rules (`url_contains`, `event_name_contains`, minimum sessions/page views).
  - Enforces frequency caps per visitor/day and honors `active_from` / `active_until` windows.
  - Returns publishable messages with `delivery_id` and resolved variant content for A/B buckets (stable per visitor).
- Manifest endpoint: `POST /api/v1/tracking/site-messages/manifest/` (public, signed). Request includes `firm_slug`, `tracking_key`, optional `tracking_key_id`.
  - Returns active message metadata, a signed manifest payload, and `config_version` for cache busting.
  - SDKs should cache delivery responses keyed by `config_version` + manifest signature and fall back to cached data on network failure.
- Impression endpoint: `POST /api/v1/tracking/site-messages/impressions/` to log `view|click` tied to `delivery_id`.
- Analytics endpoint: `GET /api/v1/tracking/site-messages/analytics/` (auth required; `can_view_reports`).
  - Returns rollups by message + variant with delivered/view/click counts and rate calculations.
- Analytics export: `GET /api/v1/tracking/site-messages/analytics/export/` returns CSV rollups.

## Observability & Auditing
- Track builder actions via standard request logging (user + firm).
- Impressions and clicks recorded in `SiteMessageImpression` with firm + visitor scoping for frequency enforcement.
- Future work: emit audit events on publish/archive, and add impression/click metrics tied to `TrackingEvent`.

## Follow-ups
- PERS-3: Targeting and display logic / impression recording.
- PERS-4: Site message UI with preview and A/B testing controls.
