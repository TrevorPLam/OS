# Site Message System & Builder
**Document Type:** Reference  
**Version:** 1.0.0  
**Last Updated:** 2026-01-06  
**Owner:** Web Personalization  
**Status:** Draft (Ready for implementation)  
**Dependencies:** READMEAI.md; TODO.md; CODEBASECONSTITUTION.md; docs/03-reference/site-tracking-architecture.md

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
- Draft messages are not eligible for client delivery; published messages should be synced via SDK configuration or dedicated endpoint (future PERS-3).

## Observability & Auditing
- Track builder actions via standard request logging (user + firm).
- Future work: emit audit events on publish/archive, and add impression/click metrics tied to `TrackingEvent`.

## Follow-ups
- PERS-3: Targeting and display logic / impression recording.
- PERS-4: Site message UI with preview and A/B testing controls.
