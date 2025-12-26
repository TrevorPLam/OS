# API Guide (Tier A)

This guide summarizes cross-cutting API conventions. For the full contract, see `openapi.yaml`.

## Base URL

- REST endpoints are served under `/api/`.
- OpenAPI schema: `/api/schema/` (served by drf-spectacular).

## Authentication & firm context

- Authentication uses JWT (SimpleJWT).
- Obtain tokens via:
  - `POST /api/auth/register/`
  - `POST /api/auth/login/`
  - `POST /api/auth/token/refresh/`
- Pass the access token as `Authorization: Bearer <token>`.
- Firm context is required for non-public endpoints. It is resolved via:
  - Subdomain (preferred), or
  - `firm_id` claim in the JWT, or
  - Session `active_firm_id` for web sessions.
- Requests without firm context are rejected with `403`.

## Pagination

List endpoints use DRF `PageNumberPagination` with a default page size of `50` and a max page size of `200`. Use:

- `?page=<number>` to select a page.
- `?page_size=<number>` to request smaller pages (capped at 200).

## Filtering, search, ordering

Many list endpoints enable DjangoFilterBackend, SearchFilter, and OrderingFilter. When enabled, these are typically available:

- `?search=<term>` for full-text search over configured fields.
- Search terms are limited to 100 characters (longer requests return 400).
- `?ordering=<field>` for ordering (prefix with `-` for descending).
- Filter fields are endpoint-specific (see OpenAPI for the allowed fields).
- On PostgreSQL, list/report queries enforce a 3s statement timeout.

Examples:

```
GET /api/clients/clients/?search=acme&ordering=-client_since
GET /api/projects/projects/?status=active&ordering=-created_at
```

## Error envelope

Errors are normalized by `config.exceptions.custom_exception_handler`:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Validation failed",
    "details": {
      "field": ["error details"]
    },
    "code": "VALIDATION_ERROR"
  }
}
```

## Tier A endpoints (high-risk)

These endpoints have additional scrutiny and must remain synced between OpenAPI and this guide:

- POST /api/auth/login/
- POST /api/auth/logout/
- POST /api/auth/token/refresh/
- POST /api/auth/register/
- GET /api/firm/break-glass/status/
- POST /api/firm/break-glass/end-session/
- GET /api/portal/projects/
- GET /api/portal/invoices/
- POST /api/finance/invoices/
- POST /api/finance/payment/create_payment_intent/
- POST /api/finance/payment/confirm_payment/
- POST /api/finance/payment/send_invoice/
- POST /api/documents/documents/upload/
- GET /api/documents/documents/{id}/download/
- GET /api/documents/versions/{id}/download/
