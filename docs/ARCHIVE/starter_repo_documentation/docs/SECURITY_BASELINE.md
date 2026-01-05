# SECURITY_BASELINE.md — Security Requirements
Document Type: Reference
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Active
Dependencies: CODEBASECONSTITUTION.md

## Security Principles

1. **Defense in Depth** - Multiple layers of security
2. **Least Privilege** - Minimum necessary permissions
3. **Secure by Default** - Security built-in, not optional
4. **Privacy by Design** - Data protection from the start
5. **Audit Everything** - Comprehensive logging and monitoring

## Authentication & Authorization

### Requirements
- Strong password policies (minimum 12 characters, complexity)
- MFA support (TOTP) for all users
- OAuth/SAML for enterprise SSO
- JWT tokens with short expiration (15 minutes access, 7 days refresh)
- Token blacklisting on logout
- Rate limiting on authentication endpoints (5 attempts per minute)

### Implementation
- `django-rest-framework-simplejwt` for JWT
- `django-allauth` for OAuth/SAML
- `django-otp` for MFA
- `django-ratelimit` for rate limiting

## Multi-Tenant Isolation

### Database Level (PostgreSQL RLS)
```sql
-- All tenant-scoped tables must have RLS enabled
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;

-- Policy enforces firm_id matching
CREATE POLICY tenant_isolation ON table_name
  USING (firm_id = current_setting('app.current_firm_id')::integer);
```

### Application Level
- Middleware sets `firm_id` in database session
- QuerySet filtering in views as defense-in-depth
- Permission classes verify firm membership
- Break-glass access audited with alerts

## Data Protection

### At Rest
- Database encryption (managed by hosting provider)
- S3 bucket encryption for documents
- Secrets in environment variables (never in code)
- Sensitive fields encrypted at application level (future: django-fernet-fields)

### In Transit
- HTTPS/TLS 1.2+ required in production
- Certificate management via Let's Encrypt or similar
- HSTS headers enforced
- Secure cookies (HttpOnly, Secure, SameSite)

### Privacy
- No content in audit logs (metadata only)
- GDPR compliance (data export, deletion)
- Configurable data retention policies
- Break-glass access requires justification and expires

## API Security

### Input Validation
- All inputs validated via DRF serializers
- SQL injection prevented by ORM (no raw SQL without justification)
- XSS prevented by Django template escaping
- CSRF protection enabled

### Rate Limiting
- Authentication: 5 attempts per minute
- API endpoints: 100 requests per minute per user
- Public endpoints: 10 requests per minute per IP

### Webhook Security
- Signature verification (HMAC-SHA256)
- Replay attack prevention (timestamp validation)
- IP allowlisting (where supported by provider)

## Secrets Management

### Development
- `.env` file (never committed)
- `.env.example` template with dummy values
- `django-environ` for loading environment variables

### Production
- Environment variables from orchestration platform
- Secrets manager (AWS Secrets Manager, Google Secret Manager, etc.)
- Rotate secrets quarterly
- Separate secrets per environment

## Audit Logging

### What to Log
- Authentication attempts (success/failure)
- Authorization failures
- Data access (break-glass, sensitive operations)
- Configuration changes
- Integration actions (API calls, webhooks)

### What NOT to Log
- Passwords or tokens
- Customer content (documents, messages, etc.)
- PII unless necessary for audit (use IDs instead)

### Log Format
```json
{
  "timestamp": "2026-01-03T12:00:00Z",
  "user_id": 123,
  "firm_id": 456,
  "action": "document.delete",
  "resource_type": "Document",
  "resource_id": 789,
  "ip_address": "203.0.113.1",
  "user_agent": "Mozilla/5.0...",
  "result": "success"
}
```

## Dependency Management

### Requirements
- Regular dependency updates (monthly)
- Security vulnerability scanning (Dependabot, Snyk)
- Pin exact versions in production
- Review changelogs before updating

### CI/CD
- Automated security scanning in pipeline
- Block PRs with known vulnerabilities
- Docker image scanning

## Incident Response

### Detection
- Sentry for error tracking
- Structured logging for audit trail
- Anomaly detection (future)

### Response
1. Identify and contain
2. Assess impact (which firms affected?)
3. Notify affected parties if required
4. Remediate and document
5. Post-mortem and prevention

### Reporting
- Security issues: See [SECURITY.md](../../SECURITY.md)
- Internal incidents: Document in `docs/incidents/`

## Compliance

### GDPR
- Data export API
- Data deletion with anonymization
- Consent management
- Data processing agreements

### SOC 2 (Future)
- Access controls documented
- Audit logging comprehensive
- Incident response procedures
- Regular security reviews

## Security Checklist (Pre-Deployment)

- [ ] All secrets in environment variables
- [ ] RLS enabled on tenant-scoped tables
- [ ] HTTPS enforced
- [ ] HSTS headers enabled
- [ ] CSRF protection enabled
- [ ] XSS protection enabled
- [ ] SQL injection prevention verified
- [ ] Rate limiting configured
- [ ] Webhook signature verification implemented
- [ ] Audit logging comprehensive
- [ ] Error messages don't leak sensitive info
- [ ] Dependencies up to date and scanned
- [ ] Backups configured and tested
- [ ] Monitoring and alerting configured

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [DRF Security](https://www.django-rest-framework.org/topics/security/)
