# API Module Coverage Inventory

**Last Updated:** 2026-01-21  
**Source of Truth:** `docs/scripts/inventory_api_coverage.py`

This inventory tracks whether each module exposes API endpoints through
module-level `urls.py`/`views.py` or through the shared `src/api/` package.
It exists to make API coverage gaps explicit and to link missing coverage to
tracked follow-up tasks.

## How this inventory is generated

Run:

```bash
python docs/scripts/inventory_api_coverage.py
```

The script scans:
- `src/modules/<module>/urls.py` and `src/modules/<module>/views.py`
- `src/api/<module>/urls.py` and `src/api/<module>/views.py`

## Coverage matrix

| Module | Module URLs | Module Views | API URLs | API Views | Coverage | Follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| accounting_integrations | ✅ | ✅ | — | — | module | — |
| ad_sync | ✅ | ✅ | — | — | module | — |
| assets | — | — | ✅ | ✅ | api | — |
| auth | ✅ | ✅ | — | — | module | — |
| automation | ✅ | ✅ | — | — | module | — |
| calendar | ✅ | ✅ | — | — | module | — |
| clients | ✅ | ✅ | ✅ | — | module | API urls without api views (module handles views). |
| communications | ✅ | ✅ | — | — | module | — |
| core | — | — | — | — | internal-only | Core is shared infrastructure utilities; no external API surface by design. |
| crm | ✅ | ✅ | ✅ | ✅ | module | — |
| delivery | — | — | — | — | missing | **T-113** (delivery scheduling APIs). |
| documents | — | — | ✅ | ✅ | api | — |
| email_ingestion | ✅ | ✅ | — | — | module | — |
| esignature | ✅ | ✅ | — | — | module | — |
| finance | — | — | ✅ | ✅ | api | — |
| firm | ✅ | ✅ | — | — | module | — |
| integrations | ✅ | ✅ | — | — | module | — |
| jobs | — | — | — | — | missing | **T-103** (job lifecycle APIs). |
| knowledge | ✅ | ✅ | — | — | module | — |
| marketing | ✅ | ✅ | — | — | module | — |
| onboarding | ✅ | ✅ | — | — | module | — |
| orchestration | — | — | — | — | missing | **T-104** (orchestration workflow APIs). |
| pricing | ✅ | ✅ | — | — | module | — |
| projects | — | — | ✅ | ✅ | api | — |
| recurrence | — | — | — | — | missing | **T-116** (recurrence APIs). |
| sms | ✅ | ✅ | — | — | module | — |
| snippets | ✅ | ✅ | — | — | module | — |
| support | ✅ | ✅ | — | — | module | — |
| tracking | ✅ | ✅ | — | — | module | — |
| webhooks | — | — | ✅ | ✅ | api | — |

## Coverage gaps

Modules without module-level or `src/api/` endpoints:
- `delivery` (tracked in **T-113**)
- `jobs` (tracked in **T-103**)
- `orchestration` (tracked in **T-104**)
- `recurrence` (tracked in **T-116**)

## Core module API decision

The `core` module is intentionally internal-only. It provides shared infrastructure
(encryption, retention, logging utilities, middleware, and safety helpers) that are
consumed by other modules and not exposed as standalone API endpoints. This keeps
the tenant boundary and authorization logic centralized in module-specific APIs,
while allowing `core` to remain focused on cross-cutting implementation details.

If a module intentionally has no API surface, document the rationale here and
ensure the decision is backed by a TODO task.
