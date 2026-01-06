# PRE-LAUNCH CHECKLIST

**Document Type:** Release Gate  
**Last Updated:** 2026-01-06  
**Owner:** Engineering + Security + Operations  
**Purpose:** Formal checklist that must be completed before production deployment

---

## Overview

This checklist ensures the platform meets **Diamond Standard (95/100)** quality criteria before launch. All P0/P1 tasks must be resolved, and all sections must be signed off by relevant owners.

**Deployment is BLOCKED until all items are checked.**

---

## Phase 1: Production Blockers (P0)

### Deployment Documentation
- [ ] **T-042**: Deployment platform documented (Trevor)
  - [ ] Deployment target identified (Vercel/K8s/ECS/Railway/Fly.io/Render)
  - [ ] DNS configuration documented
  - [ ] SSL/TLS certificate management documented
  - [ ] Environment variable secrets storage documented
  - [ ] Rollback procedures tested

### Pre-Launch Checklist & Dashboard
- [ ] **T-062**: Pre-launch checklist created (this document)
- [ ] **T-063**: Automated diamond standard dashboard operational

**Sign-off Required:** Trevor (deployment owner)  
**Status:** ⚠️ BLOCKED

---

## Phase 2: Security Hardening (P1)

### Webhook Security
- [ ] **SEC-6**: Webhook signature verification enforced
  - [ ] DocuSign webhooks reject unsigned requests
  - [ ] Twilio webhooks reject unsigned requests
  - [ ] Environment validation reports missing secrets

### Authentication Security
- [ ] **SEC-7**: Auth tokens moved to HttpOnly cookies
  - [ ] Access/refresh tokens stored in cookies (not localStorage)
  - [ ] Frontend no longer uses localStorage for tokens
  - [ ] Auth refresh and logout flows tested
  - [ ] XSS vulnerability mitigated

### Release Essentials
- [ ] **T-043**: Custom error pages created (404, 500, 503)
- [ ] **T-044**: Environment variable validation at startup
- [ ] **T-045**: Sentry monitoring hooks for critical flows
  - [ ] Payment processing instrumented
  - [ ] Webhook handlers instrumented
  - [ ] Email ingestion instrumented
  - [ ] Break-glass access instrumented

**Sign-off Required:** Security Team  
**Status:** ⚠️ PENDING

---

## Phase 3: Dependency Health (P1)

### Production Dependencies
- [ ] **T-033**: psycopg2 (not psycopg2-binary) in requirements.txt
- [ ] **T-034**: boto3 upgraded to latest stable version
- [ ] **T-031**: Unused dev dependencies removed
- [ ] **T-032**: pytest-cov/coverage consolidated
- [ ] No known CVEs in production dependencies
- [ ] DEPENDENCYAUDIT.md shows healthy state

**Sign-off Required:** Engineering  
**Status:** ⚠️ PENDING

---

## Phase 4: Test Coverage (P1)

### Backend Testing
- [ ] **T-025**: Authentication flow unit tests added
  - [ ] Login, logout, registration, token refresh tested
  - [ ] Firm scoping verified in tests
- [ ] Overall backend coverage: ≥80%
- [ ] Critical path coverage: ≥95%
- [ ] Security-sensitive code coverage: 100%

### Frontend Testing
- [ ] **T-048**: Frontend unit tests implemented
  - [ ] React Testing Library + Vitest configured
  - [ ] AuthContext, API client, forms tested
  - [ ] Frontend coverage: ≥60%
- [ ] **T-049**: E2E tests for critical paths
  - [ ] Playwright configured
  - [ ] Auth, payments, core workflows tested

**Sign-off Required:** Engineering  
**Status:** ⚠️ PENDING

---

## Phase 5: Operations Maturity (P1)

### Monitoring & Alerting
- [ ] **T-046**: Monitoring/alerting requirements documented
  - [ ] SLO targets defined (uptime, latency, error rate)
  - [ ] Alert thresholds configured
  - [ ] On-call rotation defined
- [ ] **T-051**: Uptime monitoring configured
  - [ ] External monitoring service active
  - [ ] Health endpoints monitored
  - [ ] Alerts delivered to on-call

### Incident Response
- [ ] **T-050**: Incident response runbooks created
  - [ ] Service degradation runbook
  - [ ] Database issues runbook
  - [ ] Payment failures runbook
  - [ ] Security incidents runbook
- [ ] Post-mortem template exists
- [ ] Escalation paths documented

### Build & Deployment
- [ ] **T-047**: Frontend build verified in CI
- [ ] `make verify` passes (backend + frontend + docs + OpenAPI)
- [ ] Docker Compose build succeeds
- [ ] Database migrations tested (forward + rollback)

**Sign-off Required:** Operations Team  
**Status:** ⚠️ PENDING

---

## Phase 6: Documentation Completeness

### Reference Documentation
- [ ] **T-022**: Environment variables documented
- [ ] **T-023**: Management commands documented
- [ ] **T-024**: Tier system documented or links removed
- [ ] **T-038**: Dependency documentation created

### Operations Documentation
- [ ] README.md accurate and complete
- [ ] DEPLOYMENT.md reflects actual deployment process
- [ ] OBSERVABILITY.md includes monitoring setup
- [ ] SECURITY.md reflects current security posture

**Sign-off Required:** Technical Writing / Engineering  
**Status:** ⚠️ PENDING

---

## Phase 7: Performance Validation (P2 - Recommended)

### Performance Benchmarks
- [ ] **T-056**: Performance benchmarks established
  - [ ] API endpoints: p95 <200ms, p99 <500ms
  - [ ] Frontend: FCP <1.5s, TTI <3.5s
  - [ ] Load testing completed (Locust)

### Query Optimization
- [ ] **T-057**: Slow query logging configured
- [ ] **T-059**: Query optimization tests added
- [ ] **T-058**: Core Web Vitals tracking implemented

**Sign-off Required:** Engineering (Optional but Recommended)  
**Status:** ⚠️ PENDING

---

## Audit Compliance

### Recent Audit Results
- [ ] **CODEAUDIT.md**: No P0/P1 findings
- [ ] **SECURITYAUDIT.md**: No P0/P1 findings (SEC-6, SEC-7 resolved)
- [ ] **DEPENDENCYAUDIT.md**: No P0/P1 findings
- [ ] **DOCSAUDIT.md**: No critical contradictions
- [ ] **RELEASEAUDIT.md**: All P0/P1 findings resolved

---

## Smoke Test Verification (Manual)

### Authentication & Authorization
- [ ] User can register new account
- [ ] User can login with email/password
- [ ] Token refresh works automatically
- [ ] MFA enrollment and verification works
- [ ] OAuth (Google/Microsoft) login succeeds
- [ ] Logout invalidates tokens

### Core Business Operations
- [ ] Firm creation succeeds with tenant isolation
- [ ] Client creation scoped to firm
- [ ] Project creation works
- [ ] Invoice creation and payment (Stripe test mode)
- [ ] Document upload to S3 works
- [ ] Email ingestion maps to firm/client

### Admin Functions
- [ ] User management (invite, remove)
- [ ] Role assignment works
- [ ] Break-glass access logs properly
- [ ] Audit log review functional

### Health & Monitoring
- [ ] `/health/` returns 200 OK
- [ ] `/ready/` database + cache checks pass
- [ ] Sentry receives test error
- [ ] Uptime monitoring alerts deliver

**Sign-off Required:** QA / Engineering  
**Status:** ⚠️ PENDING

---

## Security Verification

### Penetration Testing
- [ ] External security review completed (optional but recommended)
- [ ] Findings remediated or accepted risk documented

### Compliance
- [ ] GDPR: Data export and erasure tested
- [ ] Audit logging: All privileged actions logged
- [ ] Encryption: Data at rest and in transit

**Sign-off Required:** Security Team  
**Status:** ⚠️ PENDING

---

## Disaster Recovery

### Backup & Restore
- [ ] Database backup strategy documented
- [ ] Backup restoration tested
- [ ] RTO (Recovery Time Objective) defined
- [ ] RPO (Recovery Point Objective) defined

### Rollback Testing
- [ ] Application rollback tested
- [ ] Database migration rollback tested
- [ ] DNS/SSL rollback plan documented

**Sign-off Required:** Operations Team  
**Status:** ⚠️ PENDING

---

## Final Approval

### Engineering Sign-off
- **Name:** _______________________
- **Date:** _______________________
- **Signature:** _______________________

### Security Sign-off
- **Name:** _______________________
- **Date:** _______________________
- **Signature:** _______________________

### Operations Sign-off
- **Name:** _______________________
- **Date:** _______________________
- **Signature:** _______________________

### Executive Sponsor Sign-off
- **Name:** Trevor
- **Date:** _______________________
- **Signature:** _______________________

---

## Launch Decision

**GO / NO-GO:** ___________

**Launch Date:** ___________

**Launch Time:** ___________

**Rollback Plan Activated:** ___________

---

## Post-Launch Monitoring (First 48 Hours)

- [ ] Error rate <1%
- [ ] P95 latency <200ms
- [ ] No security incidents
- [ ] No data integrity issues
- [ ] Customer onboarding successful
- [ ] Payment processing functional

**Post-Launch Retrospective Scheduled:** ___________

---

## Notes

- This checklist is binding. All items must be checked before production deployment.
- Any deviations require executive approval with documented risk acceptance.
- Checklist must be updated as new critical requirements are identified.
- Post-launch, this becomes the baseline for future releases.

**Current Diamond Standard Score:** 78/100 (B+)  
**Target Score:** 95/100 (A+)  
**Estimated Timeline:** 3-4 months with systematic execution
