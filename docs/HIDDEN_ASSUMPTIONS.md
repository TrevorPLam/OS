# Hidden Assumptions & Design Decisions

**Status**: Active (ASSESS-R1.3)
**Last Updated**: December 31, 2025
**Owner**: Architecture Team

---

## Purpose

This document makes explicit the hidden assumptions and design decisions that may not be obvious from the code or documentation. Understanding these assumptions is critical for developers, operators, and stakeholders.

**Why this matters**: Implicit assumptions can lead to bugs, performance issues, and misaligned expectations. By documenting them, we reduce risk and improve maintainability.

---

## Core System Assumptions

### 1. Tenancy Model: Row-Level, Not Schema-Per-Tenant

**Assumption**: All data uses row-level multi-tenancy with `firm_id` foreign key, NOT schema-per-tenant or database-per-tenant.

**Implications**:
- ✅ **Advantage**: Simpler migrations, shared infrastructure, easier backups
- ⚠️ **Risk**: Requires strict firm-scoping on ALL queries (no global access)
- ⚠️ **Risk**: Noisy neighbor problem (one tenant can impact others' performance)
- ⚠️ **Risk**: Cross-tenant data leakage if queries are not properly scoped

**Enforcement**:
- All models inherit `FirmScopedQuerySet` (src/modules/firm/utils.py)
- Middleware sets `request.firm` on all authenticated requests
- Tests verify tenant isolation (src/tests/security/test_tenant_isolation.py)

**Decision Rationale**: Documented in [docs/4 - ADR-0010](./docs/4/ADR-0010-row-level-tenancy.md)

**References**:
- TODO.md Line 196: "DOC-04.1 Resolve tenancy contradiction"
- [CANONICAL_GRAPH_MAPPING.md](./CANONICAL_GRAPH_MAPPING.md)

---

### 2. Database: PostgreSQL in Production, SQLite Optional for Tests

**Assumption**: Production ALWAYS uses PostgreSQL 15+. SQLite is ONLY for local development/testing (opt-in via `USE_SQLITE_FOR_TESTS=True`).

**Implications**:
- ✅ **Advantage**: PostgreSQL ensures ACID compliance, proper foreign keys, full-text search
- ⚠️ **Risk**: SQLite tests may not catch Postgres-specific issues (e.g., transaction isolation, concurrent writes)
- ⚠️ **Risk**: SQLite disables foreign keys by default (now fixed via signal in config/__init__.py)
- ❌ **Not Supported**: Running production on SQLite (missing features, performance issues)

**Configuration**:
- Default: PostgreSQL (config/settings.py:117-128)
- SQLite override: Set `USE_SQLITE_FOR_TESTS=True` (settings.py:130-139)
- Foreign keys: Auto-enabled for SQLite via `connection_created` signal (config/__init__.py)

**Best Practice**: Run tests against PostgreSQL to match production environment

**References**:
- TODO.md Line 128: "ASSESS-C3.10 Eliminate test non-determinism"
- config/settings.py:130-139
- pytest.ini:2-3 (comment about PostgreSQL preference)

---

### 3. Company Names: Unique Per Firm, Not Globally

**Assumption**: `Client.company_name` must be unique within a firm, but different firms CAN have clients with the same company name.

**Implications**:
- ✅ **Advantage**: Allows different firms to have clients named "Acme Corp"
- ⚠️ **Risk**: Global search by company name must include firm context
- ⚠️ **Risk**: Migration required to change from global unique to firm-scoped unique

**Enforcement**:
- Model: `unique_together = [["firm", "company_name"]]` (clients/models.py:240)
- Removed: `unique=True` on `company_name` field (was globally unique, now removed)
- Migration: 0008_remove_company_name_global_unique.py

**References**:
- TODO.md Line 127: "ASSESS-D4.4b Fix company_name uniqueness scope"
- clients/models.py:138-240

---

### 4. Data Volume Limits

**Assumption**: The system is designed for small-to-medium professional services firms with the following scale limits:

| Metric | Expected Range | Stress Tested | Hard Limit |
|--------|----------------|---------------|------------|
| Firms (tenants) | 10-1,000 | 10,000 | None (row-level tenancy) |
| Clients per firm | 10-5,000 | 50,000 | None (pagination required) |
| Users per firm | 1-100 | 1,000 | None (RBAC scales) |
| Active engagements per firm | 5-500 | 5,000 | None (status filtering) |
| Documents per engagement | 10-1,000 | 10,000 | 50MB per file, 10GB per firm |
| API requests per firm/day | 1K-100K | 1M | Rate limited (see below) |

**Implications**:
- ✅ **Performance**: Queries optimized for <10K records per firm
- ⚠️ **Risk**: Firms with >10K clients may need custom indexes
- ⚠️ **Risk**: Document storage costs scale linearly with firm count
- ❌ **Not Supported**: Enterprise firms with 100K+ clients (would need sharding)

**Rate Limits** (per docs/24 - SECURITY_MODEL):
- **Portal API**: 100 requests/hour per user (src/api/portal/throttling.py)
- **Staff API**: 1,000 requests/hour per user (default DRF throttle)
- **Webhook endpoints**: 10 requests/minute per IP (to prevent abuse)

**References**:
- [docs/24 - SECURITY_MODEL.md](./docs/24)
- src/api/portal/throttling.py

---

### 5. Idempotency Keys: Optional for Most Operations

**Assumption**: Idempotency keys are REQUIRED for:
- Billing ledger entries (unique per firm)
- Stripe PaymentIntent calls
- Webhook event processing
- Background job deduplication

But NOT required for:
- Standard CRUD operations (GET, PUT, DELETE)
- Search/list endpoints

**Implications**:
- ✅ **Advantage**: Prevents duplicate charges, double-posting to ledger
- ⚠️ **Risk**: Client must generate and store idempotency keys
- ⚠️ **Risk**: Duplicate POST requests without idempotency key may create duplicates

**Enforcement**:
- Billing ledger: `unique_together = [["firm", "entry_type", "idempotency_key"]]`
- Workers: `unique_together = [["firm", "idempotency_key"]]`
- Stripe: `idempotency_key` parameter on all PaymentIntent calls (TODO: ASSESS-D4.4)

**References**:
- TODO.md Line 124: "ASSESS-D4.4 Fix idempotency gaps"
- [docs/13 - BILLING_LEDGER_IMPLEMENTATION.md](./BILLING_LEDGER_IMPLEMENTATION.md)
- [docs/20 - WORKERS_QUEUES_IMPLEMENTATION.md](./WORKERS_QUEUES_IMPLEMENTATION.md)

---

### 6. Email Addresses: May Be Shared Across Multiple Accounts

**Assumption**: A single email address (e.g., info@company.com) may be associated with multiple `Account` or `Contact` records, even within the same firm.

**Implications**:
- ✅ **Advantage**: Supports shared inboxes, multi-account users
- ⚠️ **Risk**: Email ingestion must handle multi-account mapping (see docs/15)
- ⚠️ **Risk**: Login by email may be ambiguous (requires account selection)
- ⚠️ **Risk**: Marketing emails may be duplicated if sent per-account

**Enforcement**:
- Email ingestion: Confidence scoring for multi-account contacts (modules/email_ingestion/mapping.py)
- Portal login: Account switcher for multi-account users (api/portal/views.py)
- Marketing: Dedupe by email before sending campaigns

**References**:
- [docs/15 - EMAIL_INGESTION_IMPLEMENTATION.md](./docs/15)
- [docs/23 - EDGE_CASES_CATALOG.md](./docs/23) (shared email edge case)

---

### 7. Session Duration: 24 Hours for Staff, 1 Hour for Portal

**Assumption**:
- **Staff sessions**: 24 hours (extended for productivity)
- **Portal sessions**: 1 hour (shorter for security, higher risk)
- **API tokens**: No expiration (revocable)

**Implications**:
- ✅ **Advantage**: Staff don't re-authenticate constantly
- ⚠️ **Risk**: Stolen staff session token valid for 24 hours
- ⚠️ **Risk**: Portal users must re-login more frequently

**Enforcement**:
- Session middleware: src/middleware/session.py (custom session expiry)
- Portal throttling: src/api/portal/throttling.py (stricter limits)

**Mitigation**:
- Session revocation on password change
- IP address tracking (log, don't enforce)
- Optional 2FA for staff (TODO: ASSESS-4.3)

**References**:
- [docs/24 - SECURITY_MODEL.md](./docs/24) (session requirements)

---

### 8. Audit Logs: Append-Only, 7-Year Retention

**Assumption**: Audit events (AuditEvent model) are immutable and retained for 7 years minimum.

**Implications**:
- ✅ **Advantage**: Forensic trail for compliance, security investigations
- ⚠️ **Risk**: Storage cost grows unbounded (but compressed/archived)
- ⚠️ **Risk**: Cannot delete audit logs even for GDPR right-to-delete
- ❌ **Not Supported**: Editing or deleting audit logs (append-only)

**Enforcement**:
- Model `save()` override prevents updates (modules/core/audit.py)
- Model `delete()` blocked (raises exception)
- Database trigger prevents UPDATE/DELETE on `audit_event` table (TODO: add trigger)

**Exceptions**:
- Audit logs may be anonymized (replace user_id with anonymous ID) if GDPR requires
- Archived to cold storage after 2 years (queried infrequently)

**References**:
- [docs/7 - DATA_GOVERNANCE.md](./docs/7)
- [DATA_RETENTION_POLICY.md](./DATA_RETENTION_POLICY.md)

---

### 9. Pricing: Deterministic, Cached for 30 Days

**Assumption**: Quote calculations are deterministic (same inputs = same output) and cached for 30 days.

**Implications**:
- ✅ **Advantage**: Performance (don't recalculate every time)
- ⚠️ **Risk**: Pricing rules changes require cache invalidation
- ⚠️ **Risk**: Non-determinism breaks caching (no random, no date-dependent logic in rules)

**Enforcement**:
- Pricing engine: Deterministic evaluation (modules/pricing/evaluator.py)
- Ruleset immutability: Published rulesets cannot be edited (modules/pricing/models.py)
- Cache: 30-day TTL on QuoteVersion records

**References**:
- [docs/9 - PRICING_IMMUTABILITY_IMPLEMENTATION.md](./docs/9)
- [docs/22 - Contract Tests](./src/tests/contract_tests.py) (pricing determinism tests)

---

### 10. File Uploads: Virus Scanning Required for Portal, Optional for Staff

**Assumption**:
- **Portal uploads**: MUST pass virus scan before download allowed
- **Staff uploads**: Virus scan recommended but not enforced
- **Malware detected**: File quarantined, critical audit event logged

**Implications**:
- ✅ **Advantage**: Protects staff from malicious client uploads
- ⚠️ **Risk**: Scan delays file availability (async scan)
- ⚠️ **Risk**: False positives may block legitimate files

**Enforcement**:
- DownloadPolicy: Configurable per firm (block/warn/allow) (modules/documents/malware_scan.py)
- Default: BLOCK portal downloads if scan pending or flagged
- Staff: WARN but allow download (staff assumed trusted)

**References**:
- [docs/14 - MALWARE_SCAN_IMPLEMENTATION.md](./docs/14)

---

### 11. Background Jobs: At-Most-Once Delivery, Manual DLQ Retry

**Assumption**: Background jobs (async tasks, scheduled jobs) are:
- **Idempotent**: Can be safely retried
- **At-most-once**: Job executed once (or not at all if fails)
- **DLQ for failures**: Manual intervention required for non-retryable errors

**Implications**:
- ✅ **Advantage**: No duplicate job execution (via idempotency keys)
- ⚠️ **Risk**: Job may fail and not retry (if max attempts reached)
- ⚠️ **Risk**: DLQ requires manual monitoring and reprocessing

**Enforcement**:
- JobQueue: SELECT FOR UPDATE SKIP LOCKED (src/modules/workers/models.py)
- Idempotency: `unique_together = [["firm", "idempotency_key"]]`
- DLQ reprocessing: Admin API endpoints (src/modules/workers/views.py)

**References**:
- [docs/20 - WORKERS_QUEUES_IMPLEMENTATION.md](./docs/20)
- [docs/11 - ORCHESTRATION_COMPENSATION_IMPLEMENTATION.md](./docs/11)

---

### 12. Time Zones: UTC Internally, User TZ for Display

**Assumption**: All timestamps stored in UTC; converted to user's timezone for display only.

**Implications**:
- ✅ **Advantage**: No ambiguity, DST handled correctly
- ⚠️ **Risk**: Developers must use timezone-aware datetimes (not naive)
- ⚠️ **Risk**: Frontend must convert to user timezone for display

**Enforcement**:
- Django setting: `USE_TZ = True` (config/settings.py)
- Model fields: `DateTimeField(auto_now_add=True)` stores UTC
- Recurrence engine: DST-aware period calculation (modules/recurrence/generator.py)

**References**:
- [docs/10 - RECURRENCE_PAUSE_RESUME_IMPLEMENTATION.md](./docs/10)
- [docs/23 - EDGE_CASES_CATALOG.md](./docs/23) (DST edge cases)

---

### 13. API Pagination: Default 50, Max 200 Records Per Page

**Assumption**: All list endpoints are paginated with:
- Default: 50 records per page
- Maximum: 200 records per page
- No unlimited/unpaginated requests

**Implications**:
- ✅ **Advantage**: Prevents memory exhaustion, denial of service
- ⚠️ **Risk**: Clients must handle pagination (cursor or page-based)
- ⚠️ **Risk**: Large datasets require multiple requests

**Enforcement**:
- DRF config: `BoundedPageNumberPagination` (config/settings.py)
- ViewSets: All list actions use pagination
- Tests: Contract tests verify pagination (src/tests/contract_tests.py)

**References**:
- TODO.md Line 53: "CONST-11 Verify/fix pagination on ViewSets"
- [docs/compliance/PAGINATION_VERIFICATION.md](./compliance/PAGINATION_VERIFICATION.md)

---

### 14. Secrets Management: Environment Variables, Not Hardcoded

**Assumption**: All secrets (API keys, database passwords, etc.) are stored in environment variables or secret manager, NEVER hardcoded.

**Implications**:
- ✅ **Advantage**: Secrets not in source control, rotatable
- ⚠️ **Risk**: Deployment requires secret provisioning
- ⚠️ **Risk**: Local development requires `.env` file (gitignored)

**Enforcement**:
- Environment validator: Startup check for required env vars (src/config/env_validator.py)
- `.env.example`: Template for required variables
- CI/CD: Secrets injected via GitHub Actions secrets

**References**:
- [docs/24 - SECURITY_COMPLIANCE.md](./SECURITY_COMPLIANCE.md)
- .env.example

---

### 15. Breaking Changes Require API Versioning

**Assumption**: Any breaking change to the API requires a new version (`/api/v2/`, etc.), not a change to existing endpoints.

**Implications**:
- ✅ **Advantage**: Clients have time to migrate, no surprise breakage
- ⚠️ **Risk**: Must maintain multiple API versions simultaneously
- ⚠️ **Risk**: Deprecated versions require 6-month notice before removal

**Enforcement**:
- API versioning policy: [API_DEPRECATION_POLICY.md](./API_DEPRECATION_POLICY.md)
- OpenAPI schema: Versioned schemas per API version (TODO: ASSESS-I5.1)
- Deprecation headers: `Deprecation`, `Sunset`, `Link` headers

**References**:
- TODO.md Line 133: "ASSESS-I5.1 Implement API versioning"
- [API_DEPRECATION_POLICY.md](./API_DEPRECATION_POLICY.md)

---

## Frequently Asked Questions

### Q: Can I use SQLite in production?
**A**: No. PostgreSQL is required for production. SQLite is missing critical features (proper concurrency, full-text search, advanced indexes) and will cause data integrity issues.

### Q: Can different firms have clients with the same company name?
**A**: Yes. `company_name` is unique per firm, not globally. This allows Firm A and Firm B to both have a client named "Acme Corp".

### Q: How long are audit logs retained?
**A**: 7 years minimum. Audit logs are immutable and cannot be deleted (even for GDPR). They may be anonymized if legally required.

### Q: What happens if a background job fails?
**A**: Jobs are retried (with exponential backoff) up to 5 times. If still failing, they're routed to the Dead Letter Queue (DLQ) for manual review and reprocessing.

### Q: Are API requests rate limited?
**A**: Yes. Portal users: 100 req/hour. Staff: 1,000 req/hour. Webhooks: 10 req/minute. Custom limits can be configured per firm.

### Q: Can I store credit card numbers?
**A**: No. Credit cards are tokenized via Stripe. We never store raw card numbers (PCI DSS compliance).

### Q: How are time zones handled?
**A**: All timestamps stored in UTC. User timezone preference applied for display only. Developers must use timezone-aware datetimes.

---

## Review & Updates

This document should be updated:
- **When new assumptions are discovered**: Add immediately
- **When assumptions change**: Update with migration plan
- **Quarterly**: Review for accuracy and completeness

**Next Review**: March 31, 2026

---

## References

- [TODO.md](../TODO.md) - Source of many documented assumptions
- [CANONICAL_GRAPH_MAPPING.md](./CANONICAL_GRAPH_MAPPING.md) - Data model decisions
- [DATA_RETENTION_POLICY.md](./DATA_RETENTION_POLICY.md) - Retention assumptions
- [API_DEPRECATION_POLICY.md](./API_DEPRECATION_POLICY.md) - API change assumptions
- [docs/4 - ADR-0010](./docs/4/ADR-0010-row-level-tenancy.md) - Tenancy decision
