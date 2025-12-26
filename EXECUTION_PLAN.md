# ConsultantPro - Task Execution Plan

**Created:** December 26, 2025
**Branch:** `claude/plan-open-tasks-VbQLN`

---

## Executive Summary

This plan prioritizes remaining tasks for ConsultantPro by categorizing them into:
- **Quick Wins** (1-4 hours) - High impact, low complexity
- **Medium Tasks** (1-2 days) - Moderate complexity, clear scope
- **Long Tasks** (3-7 days) - Complex, multi-component features

**Current Status:**
- **Tier 0-3:** 100% Complete (Tier 0: 83%, pending break-glass integration)
- **Tier 4:** 63% Complete (5/8 tasks done, 1 partial, 2 documented)
- **Tier 5:** Not Started

---

## 🎯 Priority 1: Quick Wins (1-4 hours each)

### QW-1: Break-Glass Audit Records Integration
**Tier:** 0
**Estimated Time:** 2-3 hours
**Complexity:** Low
**Impact:** High (completes Tier 0 to 100%)

**Description:** Integrate break-glass access tracking with the existing Tier 3 audit system.

**Files to Modify:**
- `src/modules/firm/permissions.py` (break-glass logic exists)
- `src/modules/firm/audit.py` (audit system exists)

**Tasks:**
1. Add `audit.log_access_event()` calls to break-glass permission checks
2. Create test cases in `tests/safety/test_break_glass_audit.py`
3. Verify audit log retention policy includes break-glass events

**Acceptance Criteria:**
- [ ] All break-glass access creates audit events
- [ ] Audit events include: actor, resource, reason, timestamp
- [ ] Tests verify audit trail creation

---

### QW-2: CRM Signal Automation (Project Skeleton)
**Tier:** Post-Tier 4
**Estimated Time:** 2 hours
**Complexity:** Low
**Impact:** Medium (automates manual work)

**Description:** Implement TODOs in `src/modules/crm/signals.py` to auto-create project skeletons when prospects convert to clients.

**Files to Modify:**
- `src/modules/crm/signals.py:145` (TODO: create initial project skeleton)
- `tests/crm/test_signals.py` (add tests)

**Tasks:**
1. Implement `create_project_skeleton()` function
2. Call from `proposal_accepted` signal
3. Test signal creates project with correct firm/client scoping

**Acceptance Criteria:**
- [ ] Accepted proposal → auto-creates project
- [ ] Project has correct firm, client, engagement linkage
- [ ] Tests verify project creation

---

### QW-3: Error Tracking Integration (Frontend)
**Tier:** Post-Tier 5 (Observability)
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Impact:** Medium (improves debugging)

**Description:** Add Sentry/LogRocket integration to ErrorBoundary component.

**Files to Modify:**
- `src/frontend/src/components/ErrorBoundary.tsx:37` (TODO: error tracking)
- `src/frontend/package.json` (add Sentry SDK)

**Tasks:**
1. Install `@sentry/react` package
2. Initialize Sentry in `ErrorBoundary.componentDidCatch()`
3. Add environment-based configuration
4. Test error capture in development

**Acceptance Criteria:**
- [ ] Errors sent to Sentry in production
- [ ] Development errors logged to console only
- [ ] User context included in error reports

---

### QW-4: Invoice Status UI Updates
**Tier:** 4
**Estimated Time:** 1 hour
**Complexity:** Low
**Impact:** Low (visual polish)

**Description:** Add UI support for new invoice statuses (`failed`, `disputed`, `refunded`, `charged_back`).

**Files to Modify:**
- `src/frontend/src/pages/Invoices.tsx` (status badge rendering)
- `src/frontend/src/api/finance.ts` (TypeScript types)

**Tasks:**
1. Add status badge colors for new statuses
2. Update TypeScript `InvoiceStatus` type
3. Test rendering in invoice list

**Acceptance Criteria:**
- [ ] All invoice statuses display correctly
- [ ] Colors match payment state severity
- [ ] TypeScript types match backend choices

---

## 🔧 Priority 2: Medium Tasks (1-2 days each)

### MT-1: Package Fee Invoicing (Complete Implementation)
**Tier:** 4.2
**Estimated Time:** 1-2 days
**Complexity:** Medium
**Impact:** High (core billing feature)

**Status:** DOCUMENTED - Implementation in progress

**Description:** Complete package fee invoicing system with auto-generation and scheduling.

**Files to Modify:**
- `src/modules/finance/billing.py` (partially implemented)
- `src/modules/finance/management/commands/generate_package_invoices.py` (exists)
- `src/modules/finance/models.py` (Invoice model ready)
- `tests/finance/test_billing.py` (add package invoice tests)

**Tasks:**
1. ✅ Add `period_start`, `period_end` to Invoice model (DONE)
2. ✅ Implement `get_package_billing_period()` helper (DONE)
3. ✅ Implement `should_generate_package_invoice()` guard (DONE)
4. ✅ Implement `create_package_invoice()` function (DONE)
5. [ ] Create management command `generate_package_invoices`
6. [ ] Add cron/Celery task for scheduled generation
7. [ ] Test monthly/quarterly/annual schedules
8. [ ] Test renewal boundary handling
9. [ ] Add admin notifications for generated invoices

**Acceptance Criteria:**
- [ ] Package invoices auto-generate on schedule
- [ ] No duplicate invoices for same period
- [ ] Invoices respect engagement renewal boundaries
- [ ] Tests cover all schedule types (monthly, quarterly, annual)
- [ ] Management command runs idempotently

**Estimated Breakdown:**
- Management command: 4 hours
- Celery task integration: 3 hours
- Testing (unit + integration): 4 hours
- Documentation: 1 hour

---

### MT-2: Recurring Payments/Autopay Workflow
**Tier:** 4.6
**Estimated Time:** 1.5 days
**Complexity:** Medium
**Impact:** High (reduces manual payment collection)

**Status:** PARTIAL - Models ready, workflow needed

**Description:** Complete autopay workflow with Stripe payment method storage and automatic charging.

**Files Modified (Partial):**
- ✅ `src/modules/clients/models.py` (autopay fields added)
- ✅ `src/modules/finance/models.py` (autopay tracking fields added)
- ✅ `src/modules/finance/management/commands/process_recurring_charges.py` (exists)

**Remaining Tasks:**
1. [ ] Implement Stripe payment method setup flow in `src/modules/clients/views.py:477`
2. [ ] Create Stripe SetupIntent for payment method collection
3. [ ] Store `payment_method_id` securely in Client model
4. [ ] Implement `process_autopay_invoice()` in `src/modules/finance/services.py`
5. [ ] Create management command wrapper for cron/Celery
6. [ ] Handle autopay failures (retry logic)
7. [ ] Add customer notifications (payment success/failure)
8. [ ] Test Stripe webhook integration
9. [ ] Add admin controls to enable/disable autopay per client

**Acceptance Criteria:**
- [ ] Clients can save payment methods via Stripe Checkout
- [ ] Invoices auto-charge when `autopay_enabled=True`
- [ ] Payment failures trigger retry workflow
- [ ] Customers receive email notifications
- [ ] Admin can enable/disable autopay per client
- [ ] Tests verify Stripe integration (test mode)

**Estimated Breakdown:**
- Stripe SetupIntent flow: 4 hours
- Auto-charge logic: 3 hours
- Webhook handlers: 2 hours
- Testing (unit + integration): 3 hours

---

### MT-3: Payment Failure Handling (Core Implementation)
**Tier:** 4.7
**Estimated Time:** 1.5 days
**Complexity:** Medium
**Impact:** High (financial integrity)

**Status:** DOCUMENTED - Full implementation needed

**Description:** Implement payment failure tracking, retry logic, and admin notifications.

**Reference:** `/home/user/OS/docs/tier4/PAYMENT_FAILURE_HANDLING.md`

**Tasks:**
1. [ ] Add payment failure fields to Invoice model (migration)
2. [ ] Implement `handle_payment_failure()` function
3. [ ] Implement `schedule_payment_retry()` function
4. [ ] Create Stripe webhook handlers for payment failures
5. [ ] Add retry logic (3, 7, 14 day schedule)
6. [ ] Create audit events for payment failures
7. [ ] Add admin notification system
8. [ ] Add customer notification templates
9. [ ] Test retry workflow end-to-end

**Acceptance Criteria:**
- [ ] Failed payments update invoice status to 'failed'
- [ ] Payment failure reason/code stored from Stripe
- [ ] Automatic retry on 3/7/14 day schedule
- [ ] After 3 failures, invoice marked 'overdue'
- [ ] Audit log captures all payment failures
- [ ] Admins notified of payment failures
- [ ] Customers notified of failures with retry info

**Estimated Breakdown:**
- Model migration: 1 hour
- Failure handling logic: 3 hours
- Retry scheduling (Celery): 3 hours
- Webhook integration: 2 hours
- Notifications: 2 hours
- Testing: 3 hours

---

### MT-4: Dispute & Chargeback Tracking
**Tier:** 4.7
**Estimated Time:** 2 days
**Complexity:** Medium-High
**Impact:** Medium (financial risk management)

**Status:** DOCUMENTED - Full implementation needed

**Reference:** `/home/user/OS/docs/tier4/PAYMENT_FAILURE_HANDLING.md` (PaymentDispute model)

**Tasks:**
1. [ ] Create `PaymentDispute` model (migration)
2. [ ] Implement `handle_dispute_opened()` webhook handler
3. [ ] Implement `handle_dispute_closed()` webhook handler
4. [ ] Implement `submit_dispute_evidence()` function
5. [ ] Create dispute admin dashboard UI
6. [ ] Add evidence submission workflow
7. [ ] Test dispute lifecycle (Stripe test mode)
8. [ ] Add reporting queries for disputes

**Acceptance Criteria:**
- [ ] Disputes tracked with metadata only (no customer data)
- [ ] Stripe webhooks create PaymentDispute records
- [ ] Admin can submit evidence via platform
- [ ] Dispute resolution updates invoice status
- [ ] Audit log captures all dispute events
- [ ] Admin dashboard shows open disputes
- [ ] Tests verify dispute workflow

**Estimated Breakdown:**
- Model + migration: 2 hours
- Webhook handlers: 4 hours
- Evidence submission: 3 hours
- Admin UI: 4 hours
- Testing: 3 hours

---

### MT-5: CRM Billing Schedule Automation
**Tier:** Post-Tier 4
**Estimated Time:** 1 day
**Complexity:** Medium
**Impact:** Medium (automates manual setup)

**Description:** Implement TODO in `src/modules/crm/signals.py` to auto-create billing schedules when proposals are accepted.

**Files to Modify:**
- `src/modules/crm/signals.py:145` (TODO: set up billing schedule)
- `src/modules/clients/models.py` (ClientEngagement model)
- `tests/crm/test_signals.py` (add tests)

**Tasks:**
1. [ ] Extract pricing info from accepted Proposal
2. [ ] Create ClientEngagement with pricing_mode, package_fee, hourly_rate
3. [ ] Set package_fee_schedule based on proposal terms
4. [ ] Test signal creates engagement correctly
5. [ ] Verify first package invoice scheduled correctly

**Acceptance Criteria:**
- [ ] Accepted proposal → auto-creates ClientEngagement
- [ ] Engagement has correct pricing_mode from proposal
- [ ] Package fees match proposal pricing
- [ ] First invoice scheduled based on engagement start date
- [ ] Tests verify engagement creation

**Estimated Breakdown:**
- Signal implementation: 4 hours
- Engagement setup logic: 3 hours
- Testing: 3 hours

---

## 🏗️ Priority 3: Long Tasks (3-7 days each)

### LT-1: Hero Workflow Integration Tests
**Tier:** 5.1
**Estimated Time:** 3-5 days
**Complexity:** High
**Impact:** High (ensures end-to-end correctness)

**Description:** Create comprehensive integration tests for critical user journeys (sales-to-cash, project-to-invoice, etc.).

**Reference:** Partial implementation exists in `tests/e2e/test_sales_to_cash_flow.py`

**Workflows to Test:**
1. Sales-to-Cash (Lead → Proposal → Client → Project → Invoice → Payment)
2. Time-to-Invoice (TimeEntry → Approval → Invoice → Payment)
3. Mixed Billing (Package + Hourly in same engagement)
4. Renewal & Churn (Engagement renewal, client offboarding)
5. Portal Journey (Client login → View invoices → Pay invoice)

**Tasks:**
1. [ ] Expand `test_sales_to_cash_flow.py` to cover all states
2. [ ] Create `test_time_to_invoice.py` for T&M billing
3. [ ] Create `test_mixed_billing.py` for package + hourly
4. [ ] Create `test_renewal_flow.py` for engagement renewals
5. [ ] Create `test_portal_journey.py` for client portal
6. [ ] Add performance assertions (query count, response time)
7. [ ] Document test scenarios and expected outcomes

**Acceptance Criteria:**
- [ ] All critical user journeys have integration tests
- [ ] Tests run in CI with realistic data volumes
- [ ] Tests verify firm scoping at every step
- [ ] Tests verify audit log creation
- [ ] Performance regressions detected

**Estimated Breakdown:**
- Test scenario design: 8 hours
- Implementation (5 workflows): 20 hours
- Performance tuning: 6 hours
- Documentation: 2 hours

---

### LT-2: Performance Safeguards (Tenant-Safe at Scale)
**Tier:** 5.2
**Estimated Time:** 4-5 days
**Complexity:** High
**Impact:** High (prevents performance regressions)

**Description:** Add performance indexes, query optimization, and monitoring for multi-tenant queries.

**Reference:** Partial index audit in `docs/tier5/PERFORMANCE_INDEXES_AUDIT.md`

**Tasks:**
1. [ ] Audit all querysets for N+1 queries
2. [ ] Add `select_related()` / `prefetch_related()` where needed
3. [ ] Create performance regression tests
4. [ ] Add database indexes for common query patterns
5. [ ] Implement query count assertions in tests
6. [ ] Add slow query logging (Django Debug Toolbar)
7. [ ] Create performance monitoring dashboard
8. [ ] Document optimization strategies

**Acceptance Criteria:**
- [ ] All list views have < 10 queries (regardless of result count)
- [ ] All firm-scoped queries use indexes
- [ ] Performance tests fail on regressions
- [ ] Slow queries logged and monitored
- [ ] Documentation includes optimization guide

**Estimated Breakdown:**
- Query audit: 8 hours
- Index creation + migration: 6 hours
- Performance tests: 8 hours
- Monitoring setup: 4 hours
- Documentation: 2 hours

---

### LT-3: Firm Offboarding + Data Exit Flows
**Tier:** 5.3
**Estimated Time:** 5-7 days
**Complexity:** High
**Impact:** High (compliance requirement)

**Description:** Implement secure firm data export and deletion workflows with audit trails.

**Tasks:**
1. [ ] Design data export format (JSON, CSV, or both)
2. [ ] Implement `export_firm_data()` management command
3. [ ] Include all firm-scoped data (clients, projects, invoices, etc.)
4. [ ] Exclude sensitive credentials (hash storage only)
5. [ ] Implement `delete_firm_data()` with tombstones
6. [ ] Add confirmation workflow (email verification)
7. [ ] Create audit events for export/deletion
8. [ ] Add admin UI for data export
9. [ ] Test export/import roundtrip
10. [ ] Document data exit process

**Acceptance Criteria:**
- [ ] Firm admin can export all firm data
- [ ] Export includes all business records
- [ ] Export excludes system credentials
- [ ] Deletion requires explicit confirmation
- [ ] Deletion creates tombstones (metadata retained)
- [ ] Audit log captures export and deletion events
- [ ] Tests verify data completeness

**Estimated Breakdown:**
- Export design: 6 hours
- Export implementation: 12 hours
- Deletion workflow: 8 hours
- Admin UI: 6 hours
- Testing: 8 hours
- Documentation: 2 hours

---

### LT-4: Configuration Change Safety
**Tier:** 5.4
**Estimated Time:** 3-4 days
**Complexity:** Medium-High
**Impact:** Medium (prevents configuration errors)

**Description:** Add validation, rollback, and audit for critical configuration changes (pricing modes, autopay settings, etc.).

**Tasks:**
1. [ ] Identify critical configuration fields
2. [ ] Add pre-save validation hooks
3. [ ] Implement configuration change audit log
4. [ ] Add confirmation dialogs in admin UI
5. [ ] Implement rollback mechanism
6. [ ] Add tests for dangerous config changes
7. [ ] Document safe configuration practices

**Critical Fields:**
- Engagement `pricing_mode` changes
- Invoice `engagement` overrides
- Client `autopay_enabled` toggles
- Firm-level feature flags

**Acceptance Criteria:**
- [ ] Dangerous config changes require confirmation
- [ ] All config changes create audit events
- [ ] Admins can rollback recent changes
- [ ] Tests prevent unsafe configuration states
- [ ] Documentation includes safe practices

**Estimated Breakdown:**
- Field identification: 4 hours
- Validation hooks: 8 hours
- Audit logging: 4 hours
- Admin UI: 6 hours
- Testing: 6 hours

---

### LT-5: Operational Observability (Metadata-Only)
**Tier:** 5.5
**Estimated Time:** 4-5 days
**Complexity:** High
**Impact:** Medium (improves operations)

**Description:** Add metrics, logging, and dashboards for system health without exposing customer content.

**Tasks:**
1. [ ] Set up metrics collection (Prometheus/StatsD)
2. [ ] Add business metrics (invoices/day, payments/day, etc.)
3. [ ] Add system metrics (query time, error rate, etc.)
4. [ ] Create Grafana dashboards
5. [ ] Set up alerting (PagerDuty/Slack)
6. [ ] Add structured logging (JSON format)
7. [ ] Implement log aggregation (ELK/CloudWatch)
8. [ ] Document observability architecture

**Metrics to Track:**
- Invoice generation rate
- Payment success/failure rate
- API response times
- Database query performance
- Error rates by endpoint
- User login frequency

**Acceptance Criteria:**
- [ ] All metrics collected without customer content
- [ ] Dashboards show system health
- [ ] Alerts trigger on anomalies
- [ ] Logs aggregated and searchable
- [ ] Documentation includes runbooks

**Estimated Breakdown:**
- Metrics setup: 8 hours
- Dashboard creation: 6 hours
- Alerting configuration: 4 hours
- Logging setup: 6 hours
- Testing: 4 hours
- Documentation: 2 hours

---

## 🔍 Priority 4: Code TODOs (Low Priority)

### TODO-1: WebSocket Message Sending
**File:** `src/frontend/src/pages/Communications.tsx:62`
**Estimated Time:** 3-4 hours
**Complexity:** Medium
**Impact:** Low (nice-to-have feature)

**Description:** Implement WebSocket-based real-time messaging in Communications page.

**Tasks:**
- [ ] Set up WebSocket server (Django Channels)
- [ ] Implement message sending in frontend
- [ ] Add connection management
- [ ] Test real-time updates

---

### TODO-2: Slack Integration
**File:** `src/modules/core/notifications.py:366`
**Estimated Time:** 2-3 hours
**Complexity:** Low
**Impact:** Low (nice-to-have)

**Description:** Add Slack webhook integration for notifications.

**Tasks:**
- [ ] Add Slack webhook URL to firm settings
- [ ] Implement `send_slack_notification()` function
- [ ] Add admin UI for Slack configuration
- [ ] Test notification delivery

---

### TODO-3: SMS Integration
**File:** `src/modules/core/notifications.py:388`
**Estimated Time:** 2-3 hours
**Complexity:** Low
**Impact:** Low (nice-to-have)

**Description:** Add Twilio SMS integration for notifications.

**Tasks:**
- [ ] Add Twilio credentials to settings
- [ ] Implement `send_sms_notification()` function
- [ ] Add phone number validation
- [ ] Test SMS delivery

---

### TODO-4: E-Signature Workflow
**File:** `src/modules/clients/views.py:764`
**Estimated Time:** 1-2 days
**Complexity:** Medium
**Impact:** Medium (useful feature)

**Description:** Integrate DocuSign/HelloSign for contract e-signatures.

**Tasks:**
- [ ] Choose e-signature provider (DocuSign/HelloSign)
- [ ] Implement signature request workflow
- [ ] Add webhook handlers for signature completion
- [ ] Store signed documents in S3
- [ ] Add UI for signature status tracking

---

## 📊 Execution Roadmap

### Phase 1: Complete Tier 4 (1-2 weeks)
**Priority:** Critical
**Goal:** Finish billing & monetization to 100%

1. **Week 1:**
   - MT-1: Package Fee Invoicing (2 days)
   - MT-2: Recurring Payments/Autopay (1.5 days)
   - MT-3: Payment Failure Handling (1.5 days)

2. **Week 2:**
   - MT-4: Dispute & Chargeback Tracking (2 days)
   - QW-1: Break-Glass Audit Integration (0.5 day)
   - QW-4: Invoice Status UI (0.5 day)

**Deliverables:**
- [ ] Tier 4 at 100%
- [ ] Tier 0 at 100%
- [ ] All billing features production-ready

---

### Phase 2: Quick Wins & Polish (3-5 days)
**Priority:** High
**Goal:** Clean up TODOs, improve automation

1. QW-2: CRM Signal Automation (2 hours)
2. MT-5: CRM Billing Schedule Automation (1 day)
3. QW-3: Error Tracking Integration (2 hours)
4. TODO-4: E-Signature Workflow (2 days) [OPTIONAL]

**Deliverables:**
- [ ] CRM automation complete
- [ ] Error tracking operational
- [ ] Code TODOs reduced

---

### Phase 3: Tier 5 Foundation (2-3 weeks)
**Priority:** Medium
**Goal:** Establish durability, scale, and exit capabilities

1. **Week 1:**
   - LT-1: Hero Workflow Integration Tests (5 days)

2. **Week 2:**
   - LT-2: Performance Safeguards (5 days)

3. **Week 3:**
   - LT-3: Firm Offboarding + Data Exit (5 days) [Start]

**Deliverables:**
- [ ] Integration tests for critical journeys
- [ ] Performance regression prevention
- [ ] Data export/deletion workflows

---

### Phase 4: Operational Maturity (1-2 weeks)
**Priority:** Low
**Goal:** Production-grade observability and safety

1. LT-4: Configuration Change Safety (4 days)
2. LT-5: Operational Observability (5 days)

**Deliverables:**
- [ ] Safe configuration management
- [ ] Production monitoring and alerting
- [ ] Tier 5 at 100%

---

## 🎯 Success Metrics

### Tier Completion
- [ ] Tier 0: 100% (currently 83%)
- [ ] Tier 1: 100% ✅
- [ ] Tier 2: 100% ✅
- [ ] Tier 3: 100% ✅
- [ ] Tier 4: 100% (currently 63%)
- [ ] Tier 5: 100% (currently 0%)

### Code Quality
- [ ] All TODOs addressed or documented
- [ ] Test coverage > 80%
- [ ] CI passing on all checks
- [ ] No N+1 queries in critical paths

### Production Readiness
- [ ] All critical user journeys tested
- [ ] Performance benchmarks established
- [ ] Monitoring and alerting operational
- [ ] Data exit process documented and tested

---

## 📝 Notes

### Dependencies
- **Stripe:** Payment processing, autopay, disputes
- **Celery:** Scheduled tasks (invoice generation, payment retry)
- **Redis:** Celery broker, caching
- **S3:** Document storage, data exports
- **Sentry:** Error tracking (frontend)

### Risk Mitigation
1. **Payment Failures:** Implement retry logic before autopay to prevent revenue loss
2. **Performance:** Add indexes and query optimization before scaling to 100+ firms
3. **Data Exit:** Critical for GDPR compliance, prioritize in Tier 5

### Deferred Work
- SSO/OAuth (Post-Tier 5)
- Advanced RBAC (Post-Tier 5)
- Webhook platform (Post-Tier 5)
- Custom dashboards (Post-Tier 5)

---

## 🚀 Getting Started

### Immediate Next Steps (Today)
1. **Review this plan** with stakeholders
2. **Start MT-1: Package Fee Invoicing** (highest priority, partially complete)
3. **Set up task tracking** in GitHub Projects or Linear
4. **Create feature branch** for Tier 4 completion

### Daily Workflow
1. Pick task from current phase
2. Create feature branch: `claude/task-name-{sessionId}`
3. Implement with tests
4. Update TODO.md with progress
5. Push and create PR
6. Merge and move to next task

---

## 📚 References

- [TODO.md](TODO.md) - Current work status
- [Tier System](docs/03-reference/tier-system.md) - Tier definitions
- [Platform Capabilities](docs/03-reference/platform-capabilities.md) - Feature inventory
- [Billing Architecture](docs/tier4/BILLING_INVARIANTS_AND_ARCHITECTURE.md) - Tier 4 design
- [Payment Failure Handling](docs/tier4/PAYMENT_FAILURE_HANDLING.md) - Tier 4.7 spec
- [Contributing Guide](CONTRIBUTING.md) - Development workflow

---

**Next Update:** After Phase 1 completion (Tier 4 at 100%)
