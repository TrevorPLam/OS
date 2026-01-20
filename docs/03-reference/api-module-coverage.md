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
| core | — | — | — | — | missing | **T-144** (determine whether core should expose API endpoints). |
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
- `core` (tracked in **T-144**)
- `delivery` (tracked in **T-113**)
- `jobs` (tracked in **T-103**)
- `orchestration` (tracked in **T-104**)
- `recurrence` (tracked in **T-116**)

If a module intentionally has no API surface, document the rationale here and
ensure the decision is backed by a TODO task.
