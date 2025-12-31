# Hidden Assumptions Documentation (ASSESS-R1.3)

**Status:** Active  
**Last Updated:** December 2025

## Overview

This document clarifies hidden assumptions and design decisions that may not be obvious from the code or standard documentation.

## Data Model Assumptions

### Company Name Uniqueness

**Assumption:** Company names are unique per firm, not globally.

**Implementation:**
- `Client.company_name`: `unique_together('firm', 'company_name')`
- `Prospect.company_name`: `unique_together('firm', 'company_name')`
- **Rationale:** Multiple firms may have clients with the same company name
- **Migration:** Changed from global `unique=True` to firm-scoped uniqueness (ASSESS-D4.4b)

### Contact Model

**Assumption:** There is no separate `Contact` model. Contact information is stored on:
- `Client.primary_contact_*` fields
- `Prospect.primary_contact_*` fields
- `Lead.contact_*` fields

**Rationale:** Simplified model for MVP; can be refactored to separate Contact model later if needed.

### EngagementLine Model

**Assumption:** There is no separate `EngagementLine` model. Engagement details are tracked via:
- `ClientEngagement` model
- Related `Project` models
- Related `Invoice` models

**Rationale:** Current implementation uses ClientEngagement as the primary engagement entity.

## Database Assumptions

### SQLite vs Postgres

**Assumption:** Production and tests use Postgres, not SQLite.

**Implementation:**
- Production: Always Postgres
- Tests: Enforced via `conftest.py` (ASSESS-C3.10)
- SQLite: Only for local development if explicitly enabled
- **Rationale:** Postgres provides better features (JSON fields, full-text search, better concurrency)

### Foreign Key Constraints

**Assumption:** Foreign key constraints are always enabled.

**Implementation:**
- Postgres: Always enabled
- SQLite: Enabled via `PRAGMA foreign_keys = ON` in conftest.py
- **Rationale:** Data integrity requires foreign key constraints

## API Assumptions

### API Versioning

**Assumption:** All API endpoints use `/api/v1/` prefix.

**Implementation:**
- Current version: v1
- Legacy endpoints redirect to v1 (temporary)
- Breaking changes require new version
- **Rationale:** Enables future API evolution while maintaining backward compatibility

### Pagination

**Assumption:** All list endpoints are paginated.

**Implementation:**
- Global DRF pagination: `BoundedPageNumberPagination`
- Default page size: 50
- Max page size: 200
- **Rationale:** Prevents large result sets and improves performance

### Error Responses

**Assumption:** All errors follow structured format with error codes.

**Implementation:**
- Format: `{"detail": "...", "error_code": "XXX_XXX", "error_type": "..."}`
- Error codes: Defined in `error_handlers.py`
- **Rationale:** Consistent error handling for API consumers

## Security Assumptions

### Tenant Isolation

**Assumption:** All data queries are firm-scoped.

**Implementation:**
- `FirmScopedQuerySet` used for all multi-tenant models
- Signal handlers filter by firm
- Background jobs require firm context
- **Rationale:** Prevents cross-tenant data access (IDOR vulnerabilities)

### SSRF Protection

**Assumption:** All URL inputs are validated to prevent SSRF.

**Implementation:**
- `InputValidator.validate_url()` blocks internal IPs/localhost
- `validate_safe_url()` validator on URLField models
- **Rationale:** Prevents Server-Side Request Forgery attacks

## Data Volume Assumptions

### Maximum File Size

**Assumption:** Maximum file upload size is 50MB.

**Implementation:**
- `InputValidator.MAX_FILE_SIZE = 50 * 1024 * 1024`
- **Rationale:** Balance between usability and storage costs

### Maximum JSON Depth

**Assumption:** Maximum JSON nesting depth is 10 levels.

**Implementation:**
- `InputValidator.validate_json_field()` enforces max_depth=10
- **Rationale:** Prevents DoS attacks via deeply nested JSON

## Business Logic Assumptions

### Currency Precision

**Assumption:** All currency values use Decimal, not float.

**Implementation:**
- All financial models use `DecimalField`
- JSON serialization converts Decimal to string
- **Rationale:** Prevents floating-point precision errors (ASSESS-C3.1b)

### Idempotency

**Assumption:** Payment operations are idempotent.

**Implementation:**
- Stripe PaymentIntent calls include `idempotency_key`
- Webhook events tracked to prevent duplicate processing
- **Rationale:** Prevents duplicate charges (ASSESS-D4.4)

## Integration Assumptions

### Stripe Webhooks

**Assumption:** Stripe webhook events are processed idempotently.

**Implementation:**
- `StripeWebhookEvent` model tracks processed events
- Duplicate events are skipped
- **Rationale:** Stripe may send duplicate webhooks

### Email Validation

**Assumption:** Email addresses are validated but not verified.

**Implementation:**
- Django `EmailField` validation
- No email verification required
- **Rationale:** Reduces friction in signup/lead capture

## Compliance Assumptions

### GDPR Consent

**Assumption:** Consent is tracked but opt-in is not required by default.

**Implementation:**
- `marketing_opt_in` field defaults to `False`
- Consent timestamp and source tracked
- **Rationale:** GDPR requires explicit consent tracking

### Data Retention

**Assumption:** Data retention policies are configurable per firm.

**Implementation:**
- `RetentionPolicy` model allows per-firm configuration
- Default policies recommended but not enforced
- **Rationale:** Different firms may have different retention requirements

## Performance Assumptions

### Query Optimization

**Assumption:** All frequently-queried fields have indexes.

**Implementation:**
- Indexes on `(firm, status)`, `(firm, created_at)`, etc.
- **Rationale:** Ensures good query performance at scale

### Caching

**Assumption:** No application-level caching currently implemented.

**Implementation:**
- Database query optimization via indexes
- Future: Redis caching for frequently accessed data
- **Rationale:** Simplicity for MVP; caching can be added as needed

## Deployment Assumptions

### Environment Variables

**Assumption:** All configuration via environment variables.

**Implementation:**
- No hardcoded secrets
- `DJANGO_SECRET_KEY` required (no fallback)
- **Rationale:** Security best practice

### Database Migrations

**Assumption:** Migrations are always forward-compatible.

**Implementation:**
- Migrations tested for rollback
- No data loss in migrations
- **Rationale:** Enables safe deployments

## References

- **ASSESS-R1.3:** Hidden assumptions documentation
- [System Spec Alignment](./SYSTEM_SPEC_ALIGNMENT.md)
- [API Versioning Policy](./API_VERSIONING_POLICY.md)