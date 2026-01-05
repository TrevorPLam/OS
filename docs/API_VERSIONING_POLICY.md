# API Versioning Policy

**Status:** Active  
**Version:** v1 (Current)  
**Last Updated:** December 2025

## Overview

All API endpoints are versioned using the `/api/v1/` prefix to enable future API evolution while maintaining backward compatibility.

## Version Support Policy

### Current Version: v1

- **Status:** Stable and actively maintained
- **URL Prefix:** `/api/v1/`
- **Support Duration:** Indefinite (until v2 is released)
- **Breaking Changes:** Not allowed without version increment

### Version Lifecycle

1. **Active Development:** New features and bug fixes
2. **Stable:** Production-ready, fully supported
3. **Deprecated:** Still supported but new features not added (1 version cycle minimum)
4. **Retired:** No longer supported, endpoints removed

## Versioning Rules

### Breaking Changes Require New Version

The following changes require a new API version:
- Removing or renaming fields
- Changing field types (e.g., string → integer)
- Removing endpoints
- Changing authentication/authorization requirements
- Changing response structure significantly

### Non-Breaking Changes (Allowed in Current Version)

- Adding new fields (optional)
- Adding new endpoints
- Adding new query parameters
- Improving error messages
- Performance optimizations

## Migration Strategy

### Legacy Endpoints

Legacy endpoints (without `/v1/` prefix) have been removed after frontend migration.
All clients must use `/api/v1/` routes.

**Deprecation Timeline:**
- Legacy endpoints were removed after frontend migration
- Minimum 1 version cycle (3-6 months) notice was provided before removal

### Client Migration

1. Update all API calls to use `/api/v1/` prefix
2. Test thoroughly in staging
3. Deploy frontend update
4. Monitor for legacy endpoint usage
5. Remove legacy redirects after 3-6 months

## Version Header

Clients can optionally specify API version via header:
```
X-API-Version: v1
```

If not specified, defaults to v1.

## Future Versions

### v2 (Planned)

When v2 is released:
- v1 remains supported for minimum 1 year
- v2 introduces breaking changes with migration guide
- Both versions supported simultaneously
- Deprecation notices sent 6 months before v1 retirement

## Examples

### Current (v1)
```
GET /api/v1/clients/
GET /api/v1/crm/prospects/
POST /api/v1/finance/invoices/
```

### Legacy (Redirects to v1)
```
GET /api/clients/ → 301 → /api/v1/clients/
GET /api/crm/prospects/ → 301 → /api/v1/crm/prospects/
```

## Documentation

- API Documentation: `/api/docs/` (Swagger UI)
- ReDoc: `/api/redoc/`
- Schema: `/api/schema/`

## See Also

- [API Deprecation Policy](./API_DEPRECATION_POLICY.md) - How deprecated fields/endpoints are managed
- [API Documentation](../03-reference/api/) - Complete API reference
- [Error Handling](../config/error_handlers.py) - Structured error responses

## References

- **ASSESS-I5.1:** API versioning implementation
- **ASSESS-I5.9:** Deprecation policy (1 version cycle support)
