# ENDPOINTS.md — API Reference
Document Type: Reference
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Active
Canonical Status: Canonical
Dependencies: ARCHITECTURE.md

## API Documentation

The ConsultantPro API is fully documented using OpenAPI/Swagger.

### Interactive Documentation

When running the development server, access the interactive API documentation:

- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/schema/

### API Versioning

- Current version: `/api/v1/`
- Version in URL path (not headers)
- Deprecation policy: 6-month minimum notice
- See [API Versioning Policy](../../docs/03-reference/policies/api-versioning.md) for details

### Authentication

All endpoints require authentication unless explicitly marked as public.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Token Endpoints:**
- `POST /api/v1/auth/token/` - Obtain access + refresh tokens
- `POST /api/v1/auth/token/refresh/` - Refresh access token
- `POST /api/v1/auth/token/logout/` - Blacklist tokens

### Base URL Structure

```
/api/v1/
  ├── auth/          # Authentication
  ├── firms/         # Firm management
  ├── users/         # User management
  ├── crm/           # CRM (leads, prospects, proposals)
  ├── clients/       # Client management
  ├── projects/      # Projects and tasks
  ├── finance/       # Invoices, payments
  ├── calendar/      # Calendar and scheduling
  ├── documents/     # Document management
  ├── communications/  # Messages and conversations
  └── integrations/  # External integrations
```

### Response Format

**Success Response:**
```json
{
  "id": 123,
  "name": "Example",
  "created_at": "2026-01-03T12:00:00Z",
  ...
}
```

**List Response (Paginated):**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/resource/?page=2",
  "previous": null,
  "results": [
    { ... },
    { ... }
  ]
}
```

**Error Response:**
```json
{
  "detail": "Error message"
}
```

**Validation Error:**
```json
{
  "field_name": ["Error message for this field"],
  "another_field": ["Another error message"]
}
```

### Common Query Parameters

- `?page=2` - Pagination
- `?page_size=50` - Items per page (default: 25, max: 100)
- `?ordering=-created_at` - Sort order (prefix `-` for descending)
- `?search=keyword` - Full-text search
- `?filter_field=value` - Filter by field

### Rate Limiting

- **Authentication:** 5 attempts per minute
- **API endpoints:** 100 requests per minute per user
- **Public endpoints:** 10 requests per minute per IP

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1735819200
```

### Error Codes

- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

### Module-Specific Endpoints

For detailed endpoint documentation, see:
- Interactive docs at `/api/docs/`
- Module-specific documentation in `src/modules/<module_name>/README.md`
- API usage guide: [docs/03-reference/api-usage.md](../../docs/03-reference/api-usage.md)

### Webhook Endpoints

External services send webhooks to:
- `POST /api/v1/webhooks/<provider>/` - Inbound webhooks

All webhook requests must include signature verification headers.

### Health Checks

- `GET /health/` - Health check (always returns 200)
- `GET /ready/` - Readiness check (database connectivity)

## Next Steps

1. Start the development server: `python manage.py runserver`
2. Visit http://localhost:8000/api/docs/
3. Obtain an access token via `/api/v1/auth/token/`
4. Use the token in Authorization header for subsequent requests
