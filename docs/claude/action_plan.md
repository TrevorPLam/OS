# ConsultantPro Action Plan
**Execution-Readiness Roadmap**
**Date:** December 23, 2025
**Status:** Ready for Approval

---

## Overview

This action plan provides a prioritized, time-boxed roadmap to take ConsultantPro from **execution-blocked** (current state) to **production-ready** (target state) in approximately **60 days**.

**Current State:** 6.5/10 - Good foundation, but 2 critical blockers prevent execution
**Target State:** 9/10 - Production-ready, tested, deployed SaaS platform
**Timeline:** 60 days with 2 engineers (or 120 days with 1 engineer)

---

## Sprint 0: Immediate Unblocking (Week 1 - Days 1-5)

**Objective:** Fix critical blockers and enable development

### Priority 0: Critical Blockers (Day 1 - 2 hours)

| # | Task | File | Effort | Owner |
|---|------|------|--------|-------|
| 1.1 | Add `label = 'custom_auth'` to AuthConfig | `src/modules/auth/apps.py` | 5 min | Dev |
| 1.2 | Fix LoadingSpinner import in ClientPortal.tsx | `src/frontend/src/pages/ClientPortal.tsx` | 2 min | Dev |
| 1.3 | Fix LoadingSpinner import in AssetManagement.tsx | `src/frontend/src/pages/AssetManagement.tsx` | 2 min | Dev |
| 1.4 | Run Django check to verify no errors | Terminal | 1 min | Dev |
| 1.5 | Run frontend build to verify success | Terminal | 5 min | Dev |
| 1.6 | Create missing migrations for clients module | Terminal | 30 min | Dev |
| 1.7 | Apply migrations to database | Terminal | 5 min | Dev |
| 1.8 | Commit and push fixes | Git | 10 min | Dev |

**Deliverable:** Application can compile and run
**Dependencies:** None
**Success Criteria:**
- ✅ `python manage.py check` passes
- ✅ `npm run build` succeeds
- ✅ All migrations applied

---

### Priority 1: TypeScript Type Safety (Days 2-3 - 8 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 2.1 | Install @types/node | 5 min | Dev |
| 2.2 | Update tsconfig.json to include node types | 10 min | Dev |
| 2.3 | Replace `process.env` with `import.meta.env` | 30 min | Dev |
| 2.4 | Add `getClients()` method to crmApi or update imports | 1 hr | Dev |
| 2.5 | Fix `listDocuments` → `getDocuments` in ClientPortal | 10 min | Dev |
| 2.6 | Export `Client` type from crm.ts or clients.ts | 15 min | Dev |
| 2.7 | Fix contract download response type error | 30 min | Dev |
| 2.8 | Remove all unused imports and variables | 1 hr | Dev |
| 2.9 | Run `tsc --noEmit` and verify 0 errors | 5 min | Dev |
| 2.10 | Commit TypeScript fixes | 10 min | Dev |

**Deliverable:** 0 TypeScript compilation errors
**Dependencies:** 1.1-1.8 (blockers fixed)
**Success Criteria:**
- ✅ `tsc --noEmit` reports 0 errors
- ✅ All pages compile without warnings

---

### Priority 2: Critical Tests (Days 3-5 - 16 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 3.1 | Write view tests for ClientProjectViewSet | 2 hrs | Dev |
| 3.2 | Write view tests for ClientCommentViewSet | 2 hrs | Dev |
| 3.3 | Write view tests for ClientInvoiceViewSet | 2 hrs | Dev |
| 3.4 | Write view tests for ClientMessageViewSet | 2 hrs | Dev |
| 3.5 | Write model tests for ClientComment | 2 hrs | Dev |
| 3.6 | Write model tests for ClientChatThread | 1 hr | Dev |
| 3.7 | Write model tests for ClientMessage | 1 hr | Dev |
| 3.8 | Write integration test for proposal → client conversion | 4 hrs | Dev |
| 3.9 | Run pytest and achieve >30% coverage | 30 min | Dev |
| 3.10 | Document failing tests (if any) | 30 min | Dev |

**Deliverable:** Core Client Portal tested, >30% coverage
**Dependencies:** 1.1-1.8 (Django must run)
**Success Criteria:**
- ✅ All new tests pass
- ✅ Coverage report shows >30% (measured by pytest-cov)
- ✅ CI pipeline green

---

### Priority 3: Development Environment Setup (Day 5 - 4 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 4.1 | Set up Sentry project for error tracking | 1 hr | DevOps |
| 4.2 | Add Sentry SDK to backend (Django) | 30 min | Dev |
| 4.3 | Add Sentry SDK to frontend (React) | 30 min | Dev |
| 4.4 | Configure SMTP using SendGrid or AWS SES | 1 hr | DevOps |
| 4.5 | Test email notifications (send test email) | 30 min | Dev |
| 4.6 | Document environment variables in .env.example | 30 min | Dev |

**Deliverable:** Error tracking and email notifications working
**Dependencies:** None (parallel work)
**Success Criteria:**
- ✅ Sentry receives test error from backend and frontend
- ✅ Email notification successfully sent

---

**Sprint 0 Deliverables:**
- ✅ Application runs without errors
- ✅ TypeScript type-safe
- ✅ >30% test coverage
- ✅ Error tracking configured
- ✅ Email notifications working

**Sprint 0 Total:** 30 hours (1 week with 2 devs, or 1.5 weeks with 1 dev)

---

## Sprint 1: Production Infrastructure (Week 2-3 - 40 hours)

**Objective:** Set up production environment and deploy to staging

### Production Environment Setup (20 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 5.1 | Create AWS account and set up IAM users | 2 hrs | DevOps |
| 5.2 | Provision RDS PostgreSQL (Multi-AZ) | 2 hrs | DevOps |
| 5.3 | Create S3 buckets (documents, static assets) | 1 hr | DevOps |
| 5.4 | Set up ECS Fargate cluster | 3 hrs | DevOps |
| 5.5 | Configure Application Load Balancer | 2 hrs | DevOps |
| 5.6 | Create ECR repository for Docker images | 1 hr | DevOps |
| 5.7 | Set up AWS Secrets Manager for secrets | 2 hrs | DevOps |
| 5.8 | Configure CloudWatch logging | 2 hrs | DevOps |
| 5.9 | Set up Route 53 for DNS | 1 hr | DevOps |
| 5.10 | Configure SSL/TLS certificates (ACM) | 2 hrs | DevOps |
| 5.11 | Create deployment scripts | 2 hrs | DevOps |

**Dependencies:** Sprint 0 complete

---

### CI/CD Pipeline (10 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 6.1 | Update GitHub Actions for staging deployment | 3 hrs | DevOps |
| 6.2 | Add Docker build and push to ECR | 2 hrs | DevOps |
| 6.3 | Add ECS task definition deployment | 2 hrs | DevOps |
| 6.4 | Add smoke tests after deployment | 2 hrs | Dev |
| 6.5 | Test full CI/CD pipeline end-to-end | 1 hr | DevOps |

**Dependencies:** 5.1-5.11 (infrastructure ready)

---

### Monitoring & Alerting (10 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 7.1 | Set up Datadog or New Relic account | 1 hr | DevOps |
| 7.2 | Install APM agent in Django | 1 hr | Dev |
| 7.3 | Configure custom metrics (API latency, DB queries) | 2 hrs | Dev |
| 7.4 | Set up CloudWatch alarms (CPU, memory, errors) | 2 hrs | DevOps |
| 7.5 | Configure PagerDuty or Slack alerts | 1 hr | DevOps |
| 7.6 | Create monitoring dashboard | 2 hrs | DevOps |
| 7.7 | Write runbook for common incidents | 1 hr | DevOps |

**Dependencies:** 5.1-5.11 (infrastructure ready)

---

**Sprint 1 Deliverables:**
- ✅ Production AWS environment provisioned
- ✅ CI/CD pipeline deploying to staging
- ✅ Monitoring and alerting configured
- ✅ Runbook for common ops tasks

**Sprint 1 Total:** 40 hours (2 weeks with 2 devs)

---

## Sprint 2: Feature Completion (Week 4-5 - 48 hours)

**Objective:** Complete missing features and replace polling

### Document Upload UI (16 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 8.1 | Design upload UI component (drag-and-drop) | 2 hrs | Dev |
| 8.2 | Implement file upload to S3 (signed URLs) | 4 hrs | Dev |
| 8.3 | Add upload progress indicator | 2 hrs | Dev |
| 8.4 | Add file type validation | 1 hr | Dev |
| 8.5 | Add file size limits (10MB) | 1 hr | Dev |
| 8.6 | Implement bulk upload (multiple files) | 3 hrs | Dev |
| 8.7 | Add success/error notifications | 1 hr | Dev |
| 8.8 | Write upload tests | 2 hrs | Dev |

---

### WebSocket Support (24 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 9.1 | Install Django Channels and Redis | 2 hrs | Dev |
| 9.2 | Configure ASGI and Channels layers | 3 hrs | Dev |
| 9.3 | Create WebSocket consumer for chat | 4 hrs | Dev |
| 9.4 | Update frontend to use WebSocket | 4 hrs | Dev |
| 9.5 | Add reconnection logic | 2 hrs | Dev |
| 9.6 | Add typing indicators | 2 hrs | Dev |
| 9.7 | Add online/offline status | 2 hrs | Dev |
| 9.8 | Test WebSocket connection stability | 2 hrs | Dev |
| 9.9 | Update deployment for WebSocket support | 3 hrs | DevOps |

**Note:** Replace 5-second polling with real-time WebSocket connections

---

### E-Signature Integration (8 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 10.1 | Set up DocuSign developer account | 1 hr | Dev |
| 10.2 | Install DocuSign Python SDK | 30 min | Dev |
| 10.3 | Implement proposal signing flow | 3 hrs | Dev |
| 10.4 | Add signature webhook handler | 2 hrs | Dev |
| 10.5 | Update frontend to trigger e-signature | 1 hr | Dev |
| 10.6 | Test end-to-end signing flow | 30 min | Dev |

---

**Sprint 2 Deliverables:**
- ✅ Document upload fully functional
- ✅ Real-time messaging via WebSockets
- ✅ E-signature integrated (DocuSign)

**Sprint 2 Total:** 48 hours (2 weeks with 2 devs)

---

## Sprint 3: Quality & Testing (Week 6-8 - 80 hours)

**Objective:** Achieve 70% test coverage

### Backend Test Coverage (40 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 11.1 | Write view tests for CRM module | 8 hrs | Dev |
| 11.2 | Write view tests for Finance module | 8 hrs | Dev |
| 11.3 | Write view tests for Projects module | 8 hrs | Dev |
| 11.4 | Write view tests for Documents module | 4 hrs | Dev |
| 11.5 | Write model tests for all business logic | 8 hrs | Dev |
| 11.6 | Write signal tests (proposal acceptance, etc.) | 4 hrs | Dev |

**Target:** 70% coverage on modules/, api/, config/

---

### Frontend Testing (40 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 12.1 | Set up Vitest test framework | 2 hrs | Dev |
| 12.2 | Configure test environment and mocks | 2 hrs | Dev |
| 12.3 | Write component tests for Client Portal | 12 hrs | Dev |
| 12.4 | Write component tests for CRM pages | 8 hrs | Dev |
| 12.5 | Write integration tests for API calls | 8 hrs | Dev |
| 12.6 | Set up Playwright for E2E tests | 4 hrs | Dev |
| 12.7 | Write E2E tests for critical flows | 4 hrs | Dev |

**Target:** >50% frontend coverage

---

**Sprint 3 Deliverables:**
- ✅ 70% backend test coverage
- ✅ >50% frontend test coverage
- ✅ E2E tests for critical flows

**Sprint 3 Total:** 80 hours (3 weeks with 2 devs)

---

## Sprint 4: Polish & Launch Prep (Week 9-10 - 32 hours)

**Objective:** Final polish and production launch

### Analytics Dashboard (16 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 13.1 | Design dashboard layout (wireframes) | 2 hrs | Dev |
| 13.2 | Implement KPI cards (MRR, active clients, etc.) | 4 hrs | Dev |
| 13.3 | Add revenue forecast chart (Chart.js) | 3 hrs | Dev |
| 13.4 | Add project profitability analysis | 3 hrs | Dev |
| 13.5 | Add utilization tracking visualization | 2 hrs | Dev |
| 13.6 | Add export to CSV functionality | 2 hrs | Dev |

---

### Mobile Responsiveness (8 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 14.1 | Audit all pages for mobile breakpoints | 2 hrs | Dev |
| 14.2 | Fix layout issues on tablet (768px) | 2 hrs | Dev |
| 14.3 | Fix layout issues on mobile (375px) | 3 hrs | Dev |
| 14.4 | Test on real devices (iOS, Android) | 1 hr | Dev |

---

### Production Checklist (8 hours)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 15.1 | Security audit (OWASP checklist) | 2 hrs | Dev |
| 15.2 | Performance testing (Locust) | 2 hrs | Dev |
| 15.3 | Load test to 100 concurrent users | 1 hr | DevOps |
| 15.4 | Database backup and restore test | 1 hr | DevOps |
| 15.5 | Disaster recovery drill | 1 hr | DevOps |
| 15.6 | Update all documentation | 1 hr | Dev |

---

**Sprint 4 Deliverables:**
- ✅ Analytics dashboard live
- ✅ Mobile-responsive design
- ✅ Production launch checklist complete

**Sprint 4 Total:** 32 hours (1 week with 2 devs)

---

## Production Launch (Week 11)

### Launch Activities

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 16.1 | Deploy to production | 2 hrs | DevOps |
| 16.2 | Smoke test all critical flows | 2 hrs | Dev |
| 16.3 | Monitor errors in Sentry for 24 hours | Ongoing | DevOps |
| 16.4 | Set up on-call rotation | 1 hr | DevOps |
| 16.5 | Create customer support runbook | 2 hrs | Dev |
| 16.6 | Announce launch to stakeholders | 1 hr | PM |

---

## Summary Timeline

| Sprint | Duration | Focus | Effort |
|--------|----------|-------|--------|
| **Sprint 0** | Week 1 | Unblock & Stabilize | 30 hrs |
| **Sprint 1** | Week 2-3 | Production Setup | 40 hrs |
| **Sprint 2** | Week 4-5 | Feature Completion | 48 hrs |
| **Sprint 3** | Week 6-8 | Quality & Testing | 80 hrs |
| **Sprint 4** | Week 9-10 | Polish & Launch Prep | 32 hrs |
| **Launch** | Week 11 | Production Deployment | 8 hrs |
| **TOTAL** | **11 weeks** | **End-to-End** | **238 hours** |

---

## Resource Planning

### With 2 Engineers:
- **Timeline:** 60 days (11 weeks)
- **Cost:** 238 hours × 2 = 476 person-hours
- **Recommendation:** 1 Backend-focused + 1 Frontend-focused

### With 1 Engineer:
- **Timeline:** 120 days (5 months)
- **Cost:** 238 hours
- **Recommendation:** Full-stack engineer with DevOps skills

---

## Dependencies & Blockers

### Critical Path:
```
Sprint 0 → Sprint 1 → Sprint 2 → Sprint 3 → Sprint 4 → Launch
(Block)   (Infra)   (Feature)  (Quality) (Polish)  (Deploy)
```

### Parallel Work Opportunities:
- Sprint 0: Tasks 1-2 (blockers) must complete before task 3 (tests)
- Sprint 1: Infrastructure (5.x), CI/CD (6.x), Monitoring (7.x) can run in parallel
- Sprint 2: Document upload (8.x) and WebSockets (9.x) can run in parallel
- Sprint 3: Backend tests (11.x) and Frontend tests (12.x) can run in parallel

---

## Success Metrics

### Week 1 (Sprint 0):
- ✅ Application compiles and runs
- ✅ 0 TypeScript errors
- ✅ >30% test coverage
- ✅ Email notifications working

### Week 3 (Sprint 1):
- ✅ Staging environment live
- ✅ CI/CD pipeline green
- ✅ Monitoring dashboard active

### Week 5 (Sprint 2):
- ✅ Document upload functional
- ✅ Real-time messaging working
- ✅ E-signature integrated

### Week 8 (Sprint 3):
- ✅ 70% backend test coverage
- ✅ >50% frontend test coverage
- ✅ E2E tests passing

### Week 10 (Sprint 4):
- ✅ Analytics dashboard live
- ✅ Mobile-responsive
- ✅ Production checklist complete

### Week 11 (Launch):
- ✅ Production deployment successful
- ✅ 0 critical errors in first 24 hours
- ✅ First paying customer onboarded

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Developer leaves mid-project | Pair programming, comprehensive documentation |
| AWS costs exceed budget | Set billing alerts at $500, $1000 thresholds |
| Security vulnerability discovered | Weekly security scans, rapid patch process |
| Performance issues | Load test weekly, optimize proactively |
| Third-party API downtime | Implement circuit breakers, fallback UIs |

---

## Post-Launch Roadmap (Month 3-6)

### Month 3:
- Calendar integration (Google, Outlook)
- Accounting export (QuickBooks)
- Advanced reporting (P&L, forecasts)

### Month 4-5:
- RBAC and approval workflows
- Document full-text search
- Client feedback & NPS

### Month 6:
- AI-powered features (proposal generation)
- Mobile app (React Native)
- Marketplace integrations (Zapier)

---

## Budget Estimate

### Development Costs:
- **Engineering:** 238 hours × $100/hr = $23,800
- **DevOps:** 40 hours × $120/hr = $4,800
- **Total Development:** $28,600

### Infrastructure Costs (Monthly):
- **AWS:** ~$500/month (ECS, RDS, S3, CloudWatch)
- **SaaS Tools:** ~$300/month (Sentry, Datadog, SendGrid)
- **Total Monthly:** ~$800/month

### First-Year Total:
- Development: $28,600 (one-time)
- Infrastructure: $9,600 (12 months)
- **Total Year 1:** $38,200

---

## Approval & Sign-off

**Prepared by:** Claude (Principal Engineer + Staff Architect)
**Date:** December 23, 2025

**Recommended for Approval:** ✅ YES - Plan is realistic, well-scoped, and achievable

**Next Steps:**
1. Review and approve action plan
2. Assign engineers to Sprint 0
3. Begin work on critical blockers (Day 1)
4. Daily standups to track progress
5. Weekly demos to stakeholders

**Questions or Concerns:**
- Contact: [Engineering Lead]
- Escalation: [CTO/VP Engineering]

---

## Appendix: Quick Reference

### Week 1 Priorities:
1. Fix auth label bug (5 min)
2. Fix LoadingSpinner imports (5 min)
3. Create migrations (30 min)
4. Fix TypeScript errors (8 hrs)
5. Write critical tests (16 hrs)

### Commands to Run:
```bash
# Fix blockers
# (Make code changes first)
python manage.py check
npm run build

# Create migrations
python manage.py makemigrations clients
python manage.py migrate

# Run tests
pytest --cov=modules --cov-report=term

# TypeScript check
cd src/frontend && npx tsc --noEmit
```

### Files to Modify (Week 1):
- `src/modules/auth/apps.py` (add label)
- `src/frontend/src/pages/ClientPortal.tsx` (fix import)
- `src/frontend/src/pages/AssetManagement.tsx` (fix import)
- `src/frontend/package.json` (add @types/node)
- Various TypeScript files (fix errors)

---

**Action Plan Complete - Ready for Execution**
