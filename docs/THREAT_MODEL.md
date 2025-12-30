# Threat Model - ConsultantPro Platform

**Version:** 1.0
**Created:** December 30, 2025
**Status:** Active
**Review Schedule:** Quarterly (next review: March 30, 2026)

---

## 1. System Overview

### 1.1 Platform Description
ConsultantPro is a multi-tenant SaaS platform for professional services firms, providing:
- Client relationship management (CRM)
- Project and task management
- Financial tracking (invoicing, payments, billing)
- Document management with versioning
- Communications and messaging
- Calendar and scheduling
- Portal for client self-service

### 1.2 Technology Stack
- **Backend:** Django 4.x (Python 3.11+), Django REST Framework
- **Database:** PostgreSQL 14+
- **Frontend:** React 18+ (TypeScript)
- **Storage:** AWS S3 (document storage)
- **Payments:** Stripe integration
- **Notifications:** Twilio (SMS), Email (SMTP)

### 1.3 Deployment Model
- Cloud-hosted (AWS/GCP/Azure)
- Multi-tenant isolation via row-level firm scoping
- HTTPS-only access
- API-driven architecture (REST)

---

## 2. Assets

### 2.1 Critical Assets

**A1: Client Personal Identifiable Information (PII)**
- Contact information (names, emails, phone numbers, addresses)
- Business information (company names, positions, relationships)
- Communication history
- **Sensitivity:** HIGH (GDPR/privacy regulations)

**A2: Financial Data**
- Invoices and payment records
- Credit card information (tokenized via Stripe)
- Retainer balances and billing allocations
- Account receivables
- **Sensitivity:** HIGH (financial fraud risk, PCI DSS scope)

**A3: Documents and Governed Artifacts**
- Signed contracts and agreements
- Client-uploaded documents
- Internal firm documents
- Document versions and checksums
- **Sensitivity:** HIGH (legal evidence, confidentiality)

**A4: Authentication Credentials**
- User passwords (hashed with Argon2)
- API keys and tokens
- Session tokens
- OAuth tokens (Google, Microsoft)
- **Sensitivity:** CRITICAL (access control foundation)

**A5: Business Logic and Configuration**
- Pricing rules and formulas
- Delivery templates (workflow automation)
- Recurrence rules
- Orchestration definitions
- **Sensitivity:** MEDIUM (competitive advantage, IP)

**A6: Audit Logs**
- User actions and data access
- Break-glass events
- Configuration changes
- **Sensitivity:** HIGH (compliance, forensics)

---

## 3. Trust Boundaries

### 3.1 External Boundaries
1. **Internet → Application** (HTTPS endpoint)
2. **Client Portal Users → Staff API** (portal users should never access staff endpoints)
3. **Integration Partners → Webhooks** (Stripe, Twilio, etc.)
4. **Administrator → Production Database** (break-glass access)

### 3.2 Internal Boundaries
1. **Firm A → Firm B** (multi-tenant isolation - CRITICAL)
2. **Staff Roles** (readonly → staff → manager → partner → admin)
3. **Portal Scopes** (message/document/appointment/billing/profile access)
4. **UI → Service → Domain → Infrastructure** (layering boundaries)

---

## 4. Threat Analysis (STRIDE)

### 4.1 Spoofing Identity

#### T-1: Unauthorized Portal Access
**Attack:** Attacker brute-forces or guesses client portal credentials to access another client's data.

**Impact:** HIGH - Data breach, PII exposure, privacy violation

**Likelihood:** MEDIUM (credentials are often weak)

**Mitigation:**
- Rate limiting on portal login endpoints (src/api/portal/throttling.py)
  - 5 attempts per 15 minutes per IP
  - 10 attempts per hour per account
- Strong password requirements (min 12 chars, complexity)
- Optional MFA (2FA via TOTP)
- Account lockout after 10 failed attempts

**Tests:**
- `tests/security/test_portal_rate_limiting.py:50-75`
- `tests/auth/test_password_validation.py`

**Status:** ✅ Implemented

---

#### T-2: API Key Theft and Reuse
**Attack:** Stolen or leaked API key used to access staff endpoints from unauthorized location.

**Impact:** HIGH - Unauthorized data access, data modification

**Likelihood:** MEDIUM (keys in logs, code repos, browser history)

**Mitigation:**
- Token rotation policy (90-day maximum lifetime)
- Token revocation API (src/modules/auth/tokens.py:120-145)
- IP allowlisting for API keys (configurable per firm)
- Audit logging of all API key usage with IP/user-agent

**Tests:**
- `tests/auth/test_token_revocation.py`
- `tests/audit/test_api_key_usage_logging.py`

**Status:** ✅ Implemented

---

#### T-3: Session Hijacking
**Attack:** Attacker intercepts or steals session cookie to impersonate authenticated user.

**Impact:** HIGH - Account takeover

**Likelihood:** LOW (with HTTPS) / HIGH (without)

**Mitigation:**
- HTTPS-only cookies (`SESSION_COOKIE_SECURE=True`)
- HttpOnly flag on session cookies
- SameSite=Strict for CSRF protection
- Session timeout (staff: 8 hours, portal: 4 hours)
- Session binding to IP address (optional, configurable)

**Tests:**
- `tests/auth/test_session_security.py`

**Status:** ✅ Implemented

---

### 4.2 Tampering

#### T-4: Billing Ledger Tampering
**Attack:** Malicious insider or attacker with DB access modifies immutable billing ledger entries to hide fraud.

**Impact:** CRITICAL - Financial fraud, audit trail destruction

**Likelihood:** LOW (requires DB access or admin privileges)

**Mitigation:**
- Immutability enforcement in BillingLedgerEntry model (src/modules/finance/billing_ledger.py:45-60)
  - `save()` override prevents updates
  - `delete()` blocked entirely
- Database-level triggers for append-only enforcement (future)
- Checksum/hash of ledger entry content
- Audit log of all attempts to modify ledger

**Tests:**
- `tests/finance/test_billing_ledger.py:120-145` (immutability)
- `tests/finance/test_billing_ledger.py:200-220` (audit on modify attempts)

**Status:** ✅ Implemented

---

#### T-5: Document Version Manipulation
**Attack:** Modify signed contract PDF after signature to change terms.

**Impact:** HIGH - Evidence tampering, legal fraud

**Likelihood:** LOW (requires storage access)

**Mitigation:**
- Document versioning with SHA-256 checksums (src/modules/documents/models.py:Version)
- Immutable versions once finalized
- Digital signatures stored separately
- S3 object versioning enabled
- Checksum verification on download

**Tests:**
- `tests/documents/test_document_versioning.py:80-100`
- `tests/documents/test_checksum_verification.py`

**Status:** ✅ Implemented

---

#### T-6: Price Manipulation in Quotes
**Attack:** Attacker modifies accepted quote to change pricing after client acceptance.

**Impact:** HIGH - Billing disputes, revenue leakage

**Likelihood:** LOW (application-level controls)

**Mitigation:**
- Immutable QuoteVersion for accepted quotes (src/modules/pricing/models.py:QuoteVersion)
- Checksum verification (docs/PRICING_IMMUTABILITY_IMPLEMENTATION.md)
- Cannot modify QuoteVersion.amount after accepted=True
- Audit log of quote modifications

**Tests:**
- `tests/pricing/test_quote_immutability.py`

**Status:** ✅ Implemented

---

### 4.3 Repudiation

#### T-7: User Denies Performing Sensitive Action
**Attack:** User deletes client data, then denies responsibility.

**Impact:** MEDIUM - Disputes, compliance issues, forensic challenges

**Likelihood:** MEDIUM (insider threat, accidents)

**Mitigation:**
- Comprehensive audit logging (src/modules/firm/audit.py)
  - All sensitive actions logged (create/update/delete/access)
  - Immutable audit log (append-only)
  - Required fields: actor, action, object_type, object_id, timestamp, ip_address, correlation_id
- Audit log retention: 7 years (configurable per firm)
- Audit export API for compliance reviews

**Tests:**
- `tests/audit/test_audit_immutability.py`
- `tests/audit/test_audit_coverage.py` (all sensitive models)

**Status:** ✅ Implemented

---

### 4.4 Information Disclosure

#### T-8: Cross-Tenant Data Leak (IDOR via API)
**Attack:** Firm A user crafts API request to access Firm B's data by guessing object IDs.

**Impact:** CRITICAL - Multi-tenant breach, complete data exposure

**Likelihood:** HIGH (without firm scoping) / LOW (with)

**Mitigation:**
- FirmScopedQuerySet default manager on all models (src/modules/firm/utils.py)
- All ViewSets use `get_queryset()` with firm filtering
- Middleware injects `request.firm` from authenticated user
- Database indexes on (firm_id, ...) for performance

**Tests:**
- `tests/security/test_tenant_isolation.py` (comprehensive cross-tenant tests)
- `tests/security/test_idor_prevention.py`

**Status:** ⚠️ PARTIAL - Models use firm scoping, but **async tasks and signals need audit** (see T-12, ASSESS-S6.2)

---

#### T-9: Portal User Accessing Multiple Accounts
**Attack:** Portal user manipulates `client_id` parameter to view other accounts in same organization.

**Impact:** HIGH - PII leak within organization

**Likelihood:** MEDIUM (if not validated)

**Mitigation:**
- Portal account switcher with explicit membership validation (src/api/portal/views.py:PortalAccountSwitcherViewSet)
- Scope gating: portal users can only access accounts they're linked to
- Session binding to specific `client_id` after account switch
- Audit log of account switches

**Tests:**
- `tests/portal/test_portal_multi_account.py`

**Status:** ✅ Implemented

---

#### T-10: SSRF via Webhook Configuration
**Attack:** Attacker configures webhook URL to internal service (e.g., AWS metadata endpoint, internal admin panel).

**Impact:** HIGH - Access to cloud metadata (credentials), internal services

**Likelihood:** MEDIUM (if URL validation missing)

**Mitigation:**
- URL validation utility (src/modules/core/input_validation.py:validate_safe_url)
- Blocked patterns:
  - localhost, 127.0.0.1, ::1
  - Private IP ranges (10.0.0.0/8, 192.168.0.0/16, 172.16.0.0/12)
  - Cloud metadata endpoints (169.254.169.254)
  - Link-local addresses
- Applied to all user-provided URLs (webhooks, integrations, website fields)

**Tests:**
- `tests/security/test_ssrf_protection.py`

**Status:** ⚠️ PARTIAL - Validator exists, but **not applied to all URL inputs** (see ASSESS-I5.6)

**Action Required:** Audit all URL input fields and apply validator (Priority: Phase 1, Week 2)

---

#### T-11: Sensitive Data in Logs
**Attack:** Attacker gains access to application logs and extracts PII, passwords, or API keys.

**Impact:** MEDIUM - PII leak, credential leak

**Likelihood:** MEDIUM (log aggregation systems, support access)

**Mitigation:**
- No-content logging policy (docs/NO_CONTENT_LOGGING_COMPLIANCE.md)
- Forbidden content fields: body, email_body, document_content, password, card_number
- PII masking in logs (email, phone, SSN redacted)
- Structured JSON logging with required fields (tenant_id, correlation_id, actor)
- Log validator for testing compliance

**Tests:**
- `tests/logging/test_no_content_logging.py`
- `tests/logging/test_pii_redaction.py`

**Status:** ✅ Implemented

---

#### T-12: Cross-Tenant Data Leak via Async Tasks/Signals
**Attack:** Async task or Django signal bypasses firm scoping, allowing Firm A action to affect Firm B data.

**Impact:** CRITICAL - Multi-tenant breach, data corruption

**Likelihood:** MEDIUM (async tasks often miss context)

**Mitigation:**
- All async tasks require `firm_id` parameter (docs/WORKERS_QUEUES_IMPLEMENTATION.md)
- Payload validation enforces tenant_id, correlation_id, idempotency_key
- Signal handlers must use firm-scoped queries
- No `Model.objects.all()` in signals (code audit)

**Tests:**
- `tests/async/test_firm_scoping_in_tasks.py`
- `tests/signals/test_firm_scoping_in_signals.py`

**Status:** ⚠️ PARTIAL - **Async tasks and signals need comprehensive audit** (see ASSESS-S6.2)

**Action Required:** Audit all Celery tasks and signal handlers for firm isolation (Priority: Phase 1, Week 1-2)

---

### 4.5 Denial of Service

#### T-13: Portal Abuse (Automated Requests)
**Attack:** Attacker floods portal endpoints with automated requests to degrade service.

**Impact:** MEDIUM - Service degradation, legitimate users affected

**Likelihood:** HIGH (public-facing portal)

**Mitigation:**
- Strict rate limiting on portal (src/api/portal/throttling.py)
  - Anonymous: 20 req/min
  - Authenticated portal: 60 req/min
  - Staff: 300 req/min
- Per-endpoint limits (e.g., upload: 5/hour)
- IP-based blocking for abuse patterns
- Captcha on signup/login (future)

**Tests:**
- `tests/security/test_portal_rate_limiting.py`

**Status:** ✅ Implemented

---

#### T-14: Expensive Query DoS
**Attack:** Attacker requests unbounded list (e.g., `/api/clients/?page_size=999999`) to overload database.

**Impact:** MEDIUM - Database overload, slow queries

**Likelihood:** MEDIUM (if pagination missing)

**Mitigation:**
- Global pagination enforced (src/config/settings.py:BoundedPageNumberPagination)
  - Default page_size: 50
  - Max page_size: 200 (hard limit)
- No ViewSet can override to allow unbounded queries
- Database query timeout: 30 seconds

**Tests:**
- `tests/api/test_pagination_limits.py`

**Status:** ✅ Implemented (but needs audit - see ASSESS-I5.5)

---

#### T-15: Large File Upload DoS
**Attack:** Attacker uploads extremely large files to exhaust storage or processing resources.

**Impact:** MEDIUM - Storage costs, processing delays

**Likelihood:** MEDIUM

**Mitigation:**
- File size limits (src/modules/core/input_validation.py:validate_file_upload)
  - Portal uploads: 50 MB max
  - Staff uploads: 200 MB max
- Storage quotas per firm (configurable)
- Malware scanning with size limits (100 MB max)

**Tests:**
- `tests/documents/test_file_upload_limits.py`

**Status:** ✅ Implemented

---

### 4.6 Elevation of Privilege

#### T-16: Role Escalation
**Attack:** Staff user modifies own role to grant admin privileges.

**Impact:** HIGH - Unauthorized administrative access

**Likelihood:** LOW (application controls)

**Mitigation:**
- Role changes require higher privilege level
  - Only firm_admin can change roles
  - Cannot self-escalate (user cannot modify own role)
- Audit log of all role changes (actor, target_user, old_role, new_role)
- Permission checks on FirmMembership updates

**Tests:**
- `tests/auth/test_role_change_audit.py`
- `tests/auth/test_self_escalation_prevention.py`

**Status:** ✅ Implemented

---

#### T-17: Privilege Escalation via IDOR
**Attack:** Attacker modifies object ID in request to access admin-only resources.

**Impact:** HIGH - Unauthorized access to sensitive config

**Likelihood:** LOW (with proper authorization)

**Mitigation:**
- Permission classes on all ViewSets (IsStaff, IsManager, IsAdmin)
- Object-level permissions for sensitive resources
- Cannot access objects outside own firm (firm scoping)

**Tests:**
- `tests/api/test_object_level_permissions.py`

**Status:** ✅ Implemented

---

#### T-18: Bypass Tenant Isolation via Direct Query
**Attack:** Code bug allows direct query bypassing FirmScopedQuerySet (e.g., `Model.objects.all()`).

**Impact:** CRITICAL - Multi-tenant breach

**Likelihood:** MEDIUM (developer error)

**Mitigation:**
- FirmScopedQuerySet as default manager on all tenant-scoped models
- Code audit for `Model.objects.all()` usage (forbidden in production code)
- CI check for forbidden patterns (future - import-linter)

**Tests:**
- `tests/safety/test_tenant_isolation.py:256-290` (code audit test)

**Status:** ⚠️ PARTIAL - **Boundary rules enforcement missing** (see CONST-10)

**Action Required:** Add import-linter to CI to prevent forbidden patterns (Priority: Phase 2, Week 3)

---

## 5. External Dependencies and Third-Party Risks

### 5.1 Stripe (Payment Processing)

**Threats:**
- T-19: Webhook spoofing (attacker sends fake payment success events)
- T-20: Idempotency failures (duplicate charges)

**Mitigations:**
- ✅ Webhook signature verification (src/api/finance/webhooks.py:85-100)
  - Validates X-Stripe-Signature header
  - Rejects unsigned requests
- ✅ Idempotency keys on all PaymentIntent creation (src/modules/finance/services.py:180)
- ⚠️ **Reconciliation gap:** Need daily cron to verify Invoice status vs Stripe API (see ASSESS-G18.5)

**Status:** PARTIAL (webhook verification complete, reconciliation pending)

---

### 5.2 Twilio (SMS Notifications)

**Threats:**
- T-21: Webhook spoofing (fake delivery status updates)

**Mitigations:**
- ✅ Webhook signature verification (src/modules/sms/webhooks.py:45-60)
  - Validates X-Twilio-Signature header
  - Uses auth token to compute expected signature
  - Completed in CONST-3 (Dec 30, 2025)

**Status:** ✅ Implemented

---

### 5.3 AWS S3 (Document Storage)

**Threats:**
- T-22: Public bucket exposure
- T-23: Orphaned files (Version records deleted but S3 objects remain)

**Mitigations:**
- ✅ Bucket policy: deny public read access
- ✅ Signed URLs for temporary access (24-hour expiry)
- ⚠️ **Reconciliation gap:** Need periodic job to verify Version records match S3 objects (see ASSESS-G18.5b)
- ✅ Malware scanning interface (src/modules/documents/malware_scan.py)

**Status:** PARTIAL (signed URLs complete, reconciliation pending)

---

## 6. Residual Risks (Requiring Remediation)

| ID | Threat | Mitigation Status | Remediation Plan | Priority | Target |
|----|--------|-------------------|------------------|----------|--------|
| T-8, T-12 | Cross-tenant leak via async/signals | ⚠️ PARTIAL | ASSESS-S6.2: Audit all async tasks and signal handlers for firm isolation | P0 | Week 1-2 |
| T-10 | SSRF via webhooks | ⚠️ PARTIAL | ASSESS-I5.6: Apply validate_safe_url to all URL inputs | P1 | Week 2 |
| T-18 | Bypass tenant isolation via direct query | ⚠️ PARTIAL | CONST-10: Add import-linter to CI for boundary rules | P2 | Week 3 |
| T-19 | Stripe reconciliation gap | ⚠️ PARTIAL | ASSESS-G18.5: Daily cron to cross-check Invoice vs Stripe | P2 | Week 6 |
| T-22 | S3 reconciliation gap | ⚠️ PARTIAL | ASSESS-G18.5b: Periodic job to verify Version vs S3 | P2 | Week 6 |

---

## 7. Assumptions and Constraints

### 7.1 Security Assumptions
1. **Infrastructure Security:** Assumes secure cloud provider (AWS/GCP) with proper VPC, security groups, and IAM policies
2. **TLS Everywhere:** All traffic is HTTPS; no HTTP endpoints exposed
3. **Database Access:** Database is not publicly accessible; admin access is break-glass only
4. **Secrets Management:** All secrets (API keys, DB credentials) stored in environment variables or secrets manager, never in code
5. **No End-to-End Encryption:** E2EE is deferred (infrastructure dependency); data at rest encrypted via provider (AWS KMS)

### 7.2 Trust Assumptions
1. **Firm Admins are Trusted:** Firm admins can access all data within their firm (intentional)
2. **Staff Users:** Staff users are trustworthy but require role-based restrictions
3. **Portal Users:** Portal users are untrusted; strict validation and rate limiting required

### 7.3 Out of Scope
1. **Physical Security:** Data center security is provider's responsibility
2. **DDoS Protection:** Assumes cloud provider DDoS protection (CloudFlare, AWS Shield)
3. **Email Security:** SMTP/email provider handles spam/phishing filtering
4. **Client-Side Security:** Browser security (XSS, CSP) is frontend concern (separate threat model)

---

## 8. Security Controls Summary

### 8.1 Implemented Controls ✅

| Control | Implementation | Test Coverage |
|---------|---------------|---------------|
| Multi-tenant isolation | FirmScopedQuerySet | test_tenant_isolation.py |
| Authentication | Django auth + custom tokens | test_auth.py |
| Authorization | DRF permissions + RBAC | test_permissions.py |
| Rate limiting | DRF throttling | test_rate_limiting.py |
| Audit logging | AuditEvent model | test_audit.py |
| Immutability | Model overrides | test_billing_ledger.py, test_pricing.py |
| Input validation | Custom validators | test_input_validation.py |
| Webhook verification | Signature validation | test_webhooks.py |
| Pagination | BoundedPageNumberPagination | test_pagination.py |
| HTTPS enforcement | Django settings | N/A (infra) |

### 8.2 Partial Controls ⚠️

| Control | Gap | Remediation |
|---------|-----|-------------|
| Async/signal firm scoping | Not audited | ASSESS-S6.2 |
| SSRF protection | Not all URLs validated | ASSESS-I5.6 |
| Boundary rules | No CI enforcement | CONST-10 |
| Reconciliation | No Stripe/S3 reconciliation | ASSESS-G18.5, ASSESS-G18.5b |

### 8.3 Future Controls (Deferred)

- Multi-Factor Authentication (MFA) via TOTP
- SSO/SAML integration
- End-to-End Encryption (E2EE) for documents
- Database-level encryption (TDE)
- Web Application Firewall (WAF) rules

---

## 9. Incident Response

### 9.1 Security Incident Classification

**P0 (Critical):**
- Cross-tenant data breach
- Credential compromise (mass breach)
- Data tampering (ledger, documents)

**P1 (High):**
- Individual account compromise
- Privilege escalation
- SSRF exploitation

**P2 (Medium):**
- Rate limiting bypass
- Audit log gaps
- Webhook spoofing (mitigated by signature verification)

### 9.2 Response Procedures

1. **Detect:** Monitoring alerts, user reports, audit log analysis
2. **Contain:** Revoke compromised credentials, isolate affected tenants
3. **Investigate:** Review audit logs, identify scope of breach
4. **Remediate:** Patch vulnerability, notify affected users (GDPR: 72 hours)
5. **Recover:** Restore from backups if needed, verify integrity
6. **Learn:** Post-mortem, update threat model, add tests

### 9.3 Runbooks

- [Incident Response Runbook](runbooks/README.md)
- [Rollback Procedures](runbooks/ROLLBACK.md)

---

## 10. Review and Maintenance

### 10.1 Review Schedule

- **Quarterly Review:** Review threat model, update mitigations, check residual risks
- **Next Review:** March 30, 2026

### 10.2 Triggers for Ad-Hoc Review

1. **New Integration:** Adding Slack, DocuSign, QuickBooks, etc.
2. **New Data Type:** Handling health records, payment card data (PCI DSS), etc.
3. **Architecture Change:** Migrating to microservices, adding caching layer, etc.
4. **Security Incident:** Any P0/P1 incident
5. **Regulatory Change:** New GDPR requirements, CCPA, etc.

### 10.3 Ownership

- **Document Owner:** Security Lead / CTO
- **Review Participants:** Engineering leads, DevOps, Product
- **Approval:** CTO sign-off required

---

## 11. References

- [Coding Constitution](codingconstitution.md)
- [Constitution Analysis](../CONSTITUTION_ANALYSIS.md)
- [ChatGPT Codebase Assessment](ChatGPT_CODEBASE_ASSESMENT)
- [Strategic Implementation Plan](../STRATEGIC_IMPLEMENTATION_PLAN.md)
- [Security Compliance](SECURITY_COMPLIANCE.md)
- [System Spec Alignment](SYSTEM_SPEC_ALIGNMENT.md)
- [Audit System](../src/modules/firm/audit.py)

---

**Document Version:** 1.0
**Last Updated:** December 30, 2025
**Next Review:** March 30, 2026
