# API Deprecation Policy

**Status:** Active  
**Last Updated:** December 2025  
**Reference:** ASSESS-I5.9

## Overview

This policy defines how API changes are managed, including deprecation of fields and endpoints. All deprecated fields and endpoints are supported for a minimum of 1 version cycle before removal.

## Deprecation Timeline

### Minimum Support Period

- **Deprecated fields/endpoints:** Supported for minimum 1 version cycle (3-6 months)
- **Breaking changes:** Require new API version (see [API_VERSIONING_POLICY.md](./API_VERSIONING_POLICY.md))
- **Notice period:** 3-6 months before removal

## Deprecation Process

### 1. Announcement

When a field or endpoint is deprecated:
- Add `deprecated: true` flag to API schema
- Include deprecation notice in API documentation
- Add `X-Deprecated` header to responses
- Log deprecation warnings in API responses

### 2. Support Period

During the support period:
- Deprecated fields continue to work
- Deprecated endpoints return 301 redirects or continue functioning
- New features not added to deprecated endpoints
- Bug fixes still applied for security/critical issues

### 3. Removal

After support period:
- Deprecated fields removed from responses
- Deprecated endpoints return 410 Gone
- Migration guide provided for affected clients

## Deprecation Indicators

### Schema Annotations

```json
{
  "field_name": {
    "type": "string",
    "deprecated": true,
    "deprecation_notice": "Use 'new_field_name' instead. Will be removed in v2.",
    "removal_date": "2025-07-01"
  }
}
```

### Response Headers

```
X-Deprecated: field_name
X-Deprecation-Notice: Use 'new_field_name' instead. Will be removed in v2.
X-Deprecation-Removal-Date: 2025-07-01
```

### API Documentation

- Deprecated fields marked with ⚠️ icon
- Deprecation notices in field descriptions
- Migration examples provided

## Examples

### Field Deprecation

**Before (v1):**
```json
{
  "client_name": "Acme Corp",  // deprecated
  "company_name": "Acme Corp"  // new field
}
```

**After deprecation period (v2):**
```json
{
  "company_name": "Acme Corp"  // only new field
}
```

### Endpoint Deprecation

**During support period:**
```
GET /api/v1/legacy-endpoint/
→ 301 Redirect to /api/v1/new-endpoint/
→ X-Deprecated header included
```

**After support period:**
```
GET /api/v1/legacy-endpoint/
→ 410 Gone
→ Error message with migration guide
```

## Migration Guidelines

### For API Consumers

1. **Monitor deprecation notices:**
   - Check API documentation regularly
   - Subscribe to API changelog
   - Monitor `X-Deprecated` headers

2. **Plan migration:**
   - Identify all deprecated fields/endpoints in use
   - Update code to use new fields/endpoints
   - Test thoroughly in staging

3. **Execute migration:**
   - Deploy updated client code
   - Verify functionality
   - Remove old field references

### For API Maintainers

1. **Before deprecating:**
   - Ensure replacement exists and is stable
   - Document migration path
   - Provide examples

2. **During deprecation:**
   - Monitor usage metrics
   - Provide support for migration
   - Extend support if needed

3. **After removal:**
   - Update documentation
   - Remove deprecated code
   - Archive migration guides

## Version Cycle Support

### Current Version (v1)

- **Status:** Active development
- **Deprecations:** Supported until v2 release + 3-6 months
- **Breaking changes:** Not allowed

### Future Versions

When v2 is released:
- v1 deprecated fields supported for 1 version cycle
- v2 introduces new fields/endpoints
- Both versions supported simultaneously
- v1 retirement after minimum support period

## Communication

### Deprecation Announcements

- **Email:** Sent to registered API consumers
- **Documentation:** Updated immediately
- **Changelog:** Entry with migration guide
- **Status page:** Deprecation timeline posted

### Support

- **Migration assistance:** Available during support period
- **Extended support:** May be granted for enterprise clients
- **FAQ:** Common migration questions answered

## Exceptions

### Security Issues

Deprecated fields/endpoints may be removed immediately if:
- Security vulnerability discovered
- Compliance requirement changes
- Critical bug cannot be fixed

In such cases:
- Emergency notice sent (minimum 30 days)
- Migration guide provided
- Support available for urgent migrations

## References

- [API Versioning Policy](./API_VERSIONING_POLICY.md)
- [API Documentation](../api/docs/)
- [Changelog](../CHANGELOG.md)