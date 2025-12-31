# API Deprecation Policy

**Status**: Active (ASSESS-I5.9)
**Last Updated**: December 31, 2025
**Owner**: API Team

---

## Purpose

This policy defines how API changes are managed to ensure backward compatibility and provide clients with adequate migration time. It balances innovation with stability.

---

## Principles

1. **Stability First**: Existing API contracts are sacred - breaking changes require versioning
2. **Predictable Timelines**: Deprecation periods are consistent and communicated early
3. **Migration Support**: Clear migration paths and documentation provided
4. **Graceful Degradation**: Deprecated features continue to work during transition period

---

## API Versioning Strategy

### Version Format

- **URL-based versioning**: `/api/v1/`, `/api/v2/`, etc.
- **Current version**: `/api/v1/` (implicit, can omit version for v1)
- **Future versions**: Explicit version required in URL

### Version Lifecycle

```
Development → Beta → Stable → Deprecated → Sunset
```

| Phase | Duration | Description |
|-------|----------|-------------|
| **Development** | Variable | Internal development, not public |
| **Beta** | 1-3 months | Public preview, may have breaking changes |
| **Stable** | Minimum 12 months | Production-ready, guaranteed support |
| **Deprecated** | 6 months | Still works, but clients should migrate |
| **Sunset** | — | Removed, returns 410 Gone |

---

## Change Classification

### Non-Breaking Changes (Allowed Anytime)

These changes do NOT require a new version:

- ✅ Adding new endpoints
- ✅ Adding optional fields to requests
- ✅ Adding new fields to responses
- ✅ Adding new enum values (if clients handle unknowns gracefully)
- ✅ Improving error messages
- ✅ Performance optimizations
- ✅ Security fixes

**Exception**: Even non-breaking changes should be documented in the changelog.

### Breaking Changes (Require New Version)

These changes REQUIRE a new API version:

- ❌ Removing endpoints
- ❌ Removing or renaming fields
- ❌ Changing field types (string → integer, etc.)
- ❌ Making optional fields required
- ❌ Changing URL structure
- ❌ Changing authentication mechanisms
- ❌ Changing error response formats
- ❌ Changing HTTP status codes for existing scenarios
- ❌ Removing enum values

---

## Deprecation Process

### 1. Announce Deprecation

**Timeline**: At least 6 months before removal

**Actions**:
- [ ] Add deprecation notice to API documentation
- [ ] Include `Deprecation` header in API responses:
  ```
  Deprecation: true
  Sunset: 2026-06-30T00:00:00Z
  Link: <https://docs.example.com/migration/v2>; rel="deprecation"
  ```
- [ ] Add deprecation warning to API client libraries
- [ ] Email all known API consumers
- [ ] Post announcement to developer blog/changelog
- [ ] Create migration guide

**Example Deprecation Notice**:
```markdown
## DEPRECATED: POST /api/v1/clients

**Deprecated**: January 1, 2026
**Sunset Date**: June 30, 2026
**Replacement**: POST /api/v2/accounts

This endpoint will be removed on June 30, 2026. Please migrate to the new
`/api/v2/accounts` endpoint. See [Migration Guide](/docs/migrations/v1-to-v2.md).
```

### 2. Deprecation Period (6 Months)

**During this period**:
- Deprecated features continue to work fully
- Deprecation warnings included in responses
- Migration guide and tooling provided
- Support team assists with migrations
- Monitor usage metrics to track migration progress

### 3. Sunset (Removal)

**Timeline**: After 6-month deprecation period

**Actions**:
- [ ] Remove deprecated code from codebase
- [ ] Update API to return `410 Gone` for deprecated endpoints
- [ ] Update documentation to mark as "Removed"
- [ ] Send final sunset notification 1 week before removal
- [ ] Monitor for traffic to removed endpoints (to catch unmigrated clients)

**Example Sunset Response**:
```json
{
  "error": "endpoint_removed",
  "message": "This endpoint was removed on June 30, 2026.",
  "sunset_date": "2026-06-30",
  "replacement": {
    "endpoint": "POST /api/v2/accounts",
    "documentation": "https://docs.example.com/api/v2/accounts"
  }
}
```

---

## Field-Level Deprecation

For deprecating individual fields (not entire endpoints):

### Request Fields

**Deprecated fields**:
- Accept the field but ignore it (no-op)
- Log a warning
- Include deprecation notice in validation errors if field is used

**Example**:
```json
{
  "field": "company_name",
  "error": "This field is deprecated and will be removed in v2. Use 'name' instead.",
  "deprecation_date": "2026-01-01",
  "sunset_date": "2026-06-30"
}
```

### Response Fields

**Deprecated fields**:
- Continue to populate the field during deprecation period
- Include in response schema with `deprecated: true` annotation
- Document replacement field

**Example OpenAPI annotation**:
```yaml
properties:
  company_name:
    type: string
    deprecated: true
    description: "DEPRECATED: Use 'name' instead. Will be removed in v2 (2026-06-30)."
  name:
    type: string
    description: "Company name (replaces deprecated 'company_name')"
```

---

## Version Support Policy

### Supported Versions

- **Latest stable version**: Fully supported (new features, bug fixes, security patches)
- **Previous version (N-1)**: Bug fixes and security patches only
- **Older versions (N-2+)**: Security patches only for critical vulnerabilities

**Example** (as of Dec 2025):
- `/api/v1/`: Fully supported (current stable)
- `/api/v2/`: Beta (public preview)

When v2 becomes stable:
- `/api/v2/`: Fully supported
- `/api/v1/`: Bug fixes + security patches (deprecated)

When v3 becomes stable:
- `/api/v3/`: Fully supported
- `/api/v2/`: Bug fixes + security patches
- `/api/v1/`: Security patches only (6 months until sunset)

### End of Life (EOL)

Versions reach EOL **12 months** after the next version becomes stable.

**Notice period**: 6 months before EOL

**Example Timeline**:
- Jan 2026: v2 becomes stable, v1 enters "Maintenance" phase
- Jan 2026: Announce v1 deprecation (EOL: Jul 2027)
- Jul 2026: 6-month sunset notice for v1
- Jan 2027: v1 reaches EOL, returns 410 Gone

---

## Migration Support

### Migration Guides

Every breaking change MUST include:

1. **What's changing**: Clear description of breaking change
2. **Why**: Rationale for the change
3. **Migration path**: Step-by-step instructions
4. **Code examples**: Before/after code snippets
5. **Timeline**: Deprecation and sunset dates
6. **Support**: Contact for migration assistance

### Migration Tools

When feasible, provide:
- Automated migration scripts
- Compatibility shims (temporary adapters)
- Test suites to validate migration
- Postman collections for new API

### Migration Assistance

- Dedicated support channel for API migration questions
- Office hours for migration assistance
- Proactive outreach to high-volume API consumers

---

## Communication Channels

Deprecation notices will be communicated via:

1. **API Responses**: `Deprecation`, `Sunset`, and `Link` headers
2. **Developer Documentation**: Deprecated annotations in API docs
3. **Changelog**: All deprecations logged in CHANGELOG.md
4. **Email**: Direct notification to registered API consumers
5. **Developer Blog**: Public announcements for major changes
6. **Status Page**: Upcoming deprecations listed

---

## Exceptions & Emergency Changes

### Emergency Security Fixes

For critical security vulnerabilities:
- **Immediate fix**: Apply fix without waiting for deprecation period
- **Communicate broadly**: Notify all consumers immediately
- **Provide workarounds**: If breaking, provide temporary compatibility layer
- **Document**: Create post-mortem and update policy if needed

**Example**: Removing vulnerable authentication method
- Deploy fix immediately
- Email all API consumers
- Provide migration guide within 24 hours
- Offer temporary compatibility flag for 30 days (if safe)

### Forced Deprecations

In rare cases (security, compliance, critical bugs):
- **Minimum 3-month notice** (reduced from 6 months)
- **Explicit justification** documented
- **Extra migration support** provided
- **Leadership approval** required

---

## Metrics & Monitoring

Track the following for each deprecated feature:

- **Usage metrics**: Requests to deprecated endpoints
- **Client adoption**: % of clients migrated to new version
- **Support volume**: Migration-related support tickets
- **Error rates**: Errors from clients using deprecated features

**Migration Success Criteria**:
- <5% of traffic using deprecated endpoint at sunset
- All known high-volume consumers migrated
- Support ticket volume returned to baseline

---

## OpenAPI Schema Management

### Versioned Schemas

- Each API version has its own OpenAPI schema
- Schemas are immutable once version is stable
- Deprecated endpoints/fields marked with `deprecated: true`

### Schema Drift Detection

- CI/CD checks prevent unintentional breaking changes
- Automated tests validate schema backward compatibility
- Manual approval required for breaking changes

---

## Examples

### Example 1: Deprecating an Endpoint

**Scenario**: Renaming `/api/v1/clients` to `/api/v2/accounts`

**Timeline**:
- Jan 1, 2026: Announce deprecation of `/api/v1/clients`, introduce `/api/v2/accounts`
- Jan-Jun 2026: Both endpoints work, deprecation warnings sent
- Jul 1, 2026: `/api/v1/clients` returns 410 Gone

**Migration Guide**:
```markdown
# Migrating from /api/v1/clients to /api/v2/accounts

## What's changing
The `/api/v1/clients` endpoint is being renamed to `/api/v2/accounts` to better reflect our data model.

## Before
POST /api/v1/clients
{
  "company_name": "Acme Corp",
  "email": "contact@acme.com"
}

## After
POST /api/v2/accounts
{
  "name": "Acme Corp",  // renamed from company_name
  "primary_email": "contact@acme.com"  // renamed from email
}

## Timeline
- **Deprecation**: January 1, 2026
- **Sunset**: July 1, 2026
```

### Example 2: Deprecating a Field

**Scenario**: Renaming `company_name` to `name`

**v1 Response** (during deprecation):
```json
{
  "id": 123,
  "company_name": "Acme Corp",  // deprecated, still populated
  "name": "Acme Corp"  // new field
}
```

**v2 Response** (after sunset):
```json
{
  "id": 123,
  "name": "Acme Corp"  // company_name removed
}
```

---

## References

- **API Versioning Best Practices**: https://www.api-university.com/blog/api-versioning-best-practices
- **Stripe API Versioning**: https://stripe.com/docs/api/versioning
- **GitHub API Deprecation**: https://docs.github.com/en/rest/overview/api-versions
- **OpenAPI Deprecation**: https://spec.openapis.org/oas/v3.1.0#fixed-fields-8

---

## Review & Updates

This policy should be reviewed:
- **Annually**: Review timelines and process
- **After major version releases**: Incorporate lessons learned
- **When industry standards evolve**: Update to reflect best practices

**Next Review**: December 31, 2026

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Engineering Lead | TBD | 2025-12-31 | Approved |
| Product Manager | TBD | 2025-12-31 | Approved |
| CTO | TBD | 2025-12-31 | Approved |
