# ConsultantPro - Prioritized TODO List

**Last Updated:** December 23, 2025

---

## 🔴 CRITICAL - IMMEDIATE (Blocking Progress)

### 1. Database Migrations
**Priority:** P0 - BLOCKER
**Effort:** 10 minutes
**Blocker For:** All testing, all development

**Tasks:**
- [ ] Run `./migrate.sh` to create and apply migrations for CRM/Clients refactor
- [ ] Verify migrations applied successfully
- [ ] Create superuser for testing

**Why Critical:** All new CRM frontend features cannot be tested without database migrations. This blocks all further development and testing.

**Commands:**
```bash
./migrate.sh
# OR manually:
docker-compose up -d db
docker-compose run --rm web python manage.py makemigrations
docker-compose run --rm web python manage.py migrate
docker-compose run --rm web python manage.py createsuperuser
```

---

## 🟠 HIGH PRIORITY (Core Workflow Validation)

### 2. End-to-End CRM Workflow Testing
**Priority:** P1
**Effort:** 2-3 hours
**Dependencies:** #1 (migrations)

**Test Scenarios:**
- [ ] Create Lead → Convert to Prospect
- [ ] Create Prospect → Create Proposal (prospective_client)
- [ ] Accept Proposal → Verify Client creation
- [ ] Verify Contract created
- [ ] Verify Project auto-creation (if enabled)
- [ ] Verify Portal enablement (if enabled)
- [ ] Test Campaign tracking (new business metrics)
- [ ] Create Client renewal proposal (renewal_client type)
- [ ] Accept renewal → Verify engagement versioning
- [ ] Create Client expansion proposal (update_client type)
- [ ] Pipeline report accuracy

**Expected Outcome:** Full Lead → Client workflow works end-to-end with no errors.

### 3. Backend Signal Enhancements
**Priority:** P1 - COMPLETED ✅
**Effort:** 4-6 hours
**Status:** Completed - Email notifications and project completion workflow implemented

**Tasks:**
- [x] Implement email notifications in `src/modules/crm/signals.py:74,136`
  - Lead conversion notifications
  - Proposal sent/accepted notifications
  - Client creation notifications
- [x] Implement project completion workflow in `src/modules/projects/signals.py:178-180`
  - Generate completion report
  - Calculate final billing
  - Send stakeholder notifications
- [x] Created notification service (`src/modules/core/notifications.py`)
- [ ] Add notification preferences model (User preferences for email/in-app) - FUTURE
- [ ] Create email templates for each notification type - FUTURE

---

## 🟡 MEDIUM PRIORITY (Client Portal Enhancement)

### 4. Client Portal - Work Section
**Priority:** P2 - COMPLETED ✅
**Effort:** 8-12 hours
**Status:** Completed - Full work section with projects, tasks, and comments

**Backend Tasks:**
- [x] Create `ClientComment` model for task comments
- [x] Add API endpoint: `POST /api/clients/comments/`
- [x] Add API endpoint: `GET /api/clients/projects/` (filtered by client)
- [x] Add API endpoint: `GET /api/clients/projects/{id}/tasks/`
- [x] Add permissions: clients can view assigned projects, add comments only
- [x] ClientTaskSerializer and ClientProjectSerializer (read-only)
- [x] Comment mark-as-read functionality for firm users

**Frontend Tasks:**
- [x] Build Work section UI (`src/frontend/src/pages/ClientPortal.tsx`)
- [x] Display client's projects with progress bars
- [x] Show task checklists (read-only for client)
- [x] Comment input for each task
- [x] Real-time comment updates after submission
- [x] Expandable task details with metadata
- [x] Progress visualization (bars and percentages)
- [ ] File attachment upload for tasks - FUTURE

### 5. Client Portal - Chat Section
**Priority:** P2 - COMPLETED ✅
**Effort:** 12-16 hours
**Status:** Completed - REST API with polling (WebSocket upgrade path available)

**Backend Tasks:**
- [x] Create `ClientMessage` model
- [x] Create `ClientChatThread` model (daily threads)
- [x] REST API endpoints for chat (`POST /api/clients/messages/`, `GET /api/clients/chat-threads/active/`)
- [x] Message read status tracking
- [x] Auto-filtering by client for portal users
- [x] Unread message count endpoint
- [ ] Setup Django Channels for WebSocket support - FUTURE UPGRADE
- [ ] Setup Redis for message queueing - FUTURE UPGRADE
- [ ] WebSocket consumer for real-time messaging - FUTURE UPGRADE
- [ ] Daily thread rotation cron job (00:00 UTC) - FUTURE

**Frontend Tasks:**
- [x] Chat UI component (message list, input)
- [x] Auto-refresh every 5 seconds for near real-time updates
- [x] Read receipts (is_read tracking)
- [x] Daily thread indicator
- [x] Sender name display (client vs team)
- [x] Keyboard shortcuts (Enter to send, Shift+Enter for new line)
- [x] Unread message counter in dashboard
- [ ] WebSocket connection management - FUTURE UPGRADE
- [ ] Search archived threads - FUTURE
- [ ] File attachments in chat - FUTURE

### 6. Client Portal - Billing Section
**Priority:** P2 - COMPLETED ✅
**Effort:** 6-8 hours
**Status:** Completed - Full billing with payment link generation

**Backend Tasks:**
- [x] Update Finance API for client-filtered invoices (`GET /api/clients/invoices/`)
- [x] ClientInvoiceSerializer with calculated fields (balance_due, is_overdue, days_until_due)
- [x] Stripe payment link generation endpoint (placeholder)
- [x] Invoice summary endpoint with statistics
- [x] Auto-filtering by client for portal users
- [x] Permission checks (can_view_billing)
- [ ] ACH payment via Plaid integration - FUTURE
- [ ] Payment plan setup endpoints - FUTURE
- [ ] Auto-pay configuration endpoints - FUTURE

**Frontend Tasks:**
- [x] Load invoices from client portal API
- [x] Display invoice list with status badges
- [x] "Pay Now" button → Stripe Checkout (placeholder)
- [x] Invoice summary cards (total billed, paid, outstanding, overdue)
- [x] Expandable invoice details with line items
- [x] Days until due / days overdue indicators
- [x] Payment history display
- [ ] ACH payment option - FUTURE
- [ ] Payment plan display and management - FUTURE
- [ ] Auto-pay toggle - FUTURE

### 7. Client Portal - Engagement Section
**Priority:** P2 - COMPLETED ✅
**Effort:** 6-8 hours
**Status:** Completed - Full engagement management with contracts, proposals, and history

**Backend Tasks:**
- [x] Create endpoints for client-visible contracts (`GET /api/clients/contracts/`)
- [x] Create endpoints for client-visible proposals (`GET /api/clients/proposals/`)
- [x] ClientContractSerializer with calculated fields (is_active, days_remaining)
- [x] ClientProposalSerializer with expiry tracking
- [x] ClientEngagementDetailSerializer with version history
- [x] Contract download endpoint (`GET /api/clients/contracts/{id}/download/`)
- [x] Engagement timeline endpoint
- [x] E-signature placeholder (DocuSign or HelloSign integration pending)
- [ ] E-signature integration (DocuSign or HelloSign) - FUTURE
- [ ] Renewal request workflow endpoint - FUTURE

**Frontend Tasks:**
- [x] Display current contracts with metadata
- [x] Display pending proposals (renewals, expansions)
- [x] Contract download buttons
- [x] E-signature workflow UI (placeholder)
- [x] Engagement history timeline with version badges
- [x] Expiry warnings for contracts and proposals
- [x] Days remaining indicators
- [x] Parent/renewal relationship visualization
- [x] 3-panel sub-navigation (Contracts, Proposals, History)
- [ ] "Request Renewal" button - FUTURE
- [ ] Upcoming renewal alerts (90 days out) - FUTURE

---

## 🟢 LOW PRIORITY (Future Enhancements)

### 8. Email Triage Module
**Priority:** P3
**Effort:** 20-24 hours
**Status:** Not Started

**Backend Tasks:**
- [ ] Create Email models (`Email`, `EmailAccount`, `EmailTag`)
- [ ] OAuth integration for Outlook
- [ ] OAuth integration for Gmail
- [ ] IMAP sync worker (background job)
- [ ] Email assignment API
- [ ] Tag management API
- [ ] Client linking API

**Frontend Tasks:**
- [ ] Unified inbox component
- [ ] Email detail view
- [ ] Assignment dropdown
- [ ] Priority tagging
- [ ] Quick response templates
- [ ] Link to client records
- [ ] Search and filters

### 9. Scheduling Module
**Priority:** P3
**Effort:** 16-20 hours
**Status:** Not Started

**Backend Tasks:**
- [ ] Create Calendar models (`Calendar`, `Event`)
- [ ] OAuth integration for Outlook Calendar
- [ ] OAuth integration for Google Calendar
- [ ] Two-way sync worker (background job)
- [ ] Event CRUD APIs
- [ ] Recurrence rule parsing (RRULE)
- [ ] Client/Project linking

**Frontend Tasks:**
- [ ] Calendar view (month, week, day)
- [ ] Multi-calendar display
- [ ] Event creation modal
- [ ] Team scheduling view
- [ ] Meeting room booking
- [ ] Client meeting links

### 10. Message Board Module
**Priority:** P3
**Effort:** 4-6 hours
**Status:** Not Started

**Backend Tasks:**
- [ ] Create MessageBoard models
- [ ] Post CRUD API
- [ ] Comment API
- [ ] Pin/unpin posts
- [ ] Category filtering

**Frontend Tasks:**
- [ ] Board list view
- [ ] Post creation modal
- [ ] Comment threads
- [ ] Pin indicator
- [ ] Category badges

### 11. Error Tracking Integration
**Priority:** P3
**Effort:** 2-3 hours

**Tasks:**
- [ ] Sign up for Sentry account
- [ ] Install Sentry SDK
- [ ] Configure Sentry DSN in environment
- [ ] Update `src/frontend/src/components/ErrorBoundary.tsx:37` to send errors to Sentry
- [ ] Test error reporting
- [ ] Setup alert rules

### 12. Advanced Client Portal Dashboard
**Priority:** P3
**Effort:** 8-10 hours

**Tasks:**
- [ ] Build analytics widgets
  - Active projects summary
  - Pending tasks count
  - Unread messages badge
  - Outstanding invoices total
  - Recent documents list
  - Upcoming milestones
- [ ] Build charts
  - Project progress (% complete)
  - Budget utilization
  - Time tracking summary
- [ ] Real-time updates via WebSocket
- [ ] Customizable widget layout

---

## 📋 MAINTENANCE & DOCUMENTATION

### 13. Update Documentation
**Priority:** P2
**Effort:** 2-3 hours

**Tasks:**
- [x] Update README.md with CRM refactor details
- [ ] Update API_USAGE.md with new CRM endpoints
  - `/api/crm/leads/`
  - `/api/crm/prospects/`
  - `/api/crm/campaigns/`
  - `/api/clients/`
  - Proposal type documentation
- [ ] Create Client Portal user guide
- [ ] Update DEPLOYMENT.md with new modules
- [ ] Document WebSocket setup (when implemented)

### 14. Code Cleanup
**Priority:** P3
**Effort:** 2-3 hours

**Tasks:**
- [ ] Remove all TODO comments after implementing features
- [ ] Remove deprecated code references
- [ ] Standardize error messages
- [ ] Add JSDoc comments to complex functions
- [ ] Run linting and fix warnings

### 15. Performance Optimization
**Priority:** P3
**Effort:** 4-6 hours

**Tasks:**
- [ ] Add database indexes on frequently queried fields
  - `crm.Lead.status`
  - `crm.Prospect.pipeline_stage`
  - `crm.Campaign.type`
  - `clients.Client.status`
- [ ] Implement query optimization (select_related, prefetch_related)
- [ ] Add API response caching for read-heavy endpoints
- [ ] Frontend lazy loading for large lists
- [ ] Image optimization for uploaded files

---

## 📊 TESTING & QA

### 16. Expand Test Coverage
**Priority:** P2
**Effort:** 6-8 hours

**Tasks:**
- [ ] Write tests for CRM signals
  - Test Lead → Prospect conversion
  - Test Proposal → Client conversion (3 types)
  - Test engagement versioning
- [ ] Write tests for Client endpoints
- [ ] Write tests for Campaign performance calculations
- [ ] Write tests for Pipeline report
- [ ] Frontend integration tests for CRM pages
- [ ] E2E tests with Playwright or Cypress

---

## 🎯 SUCCESS CRITERIA

### Phase 1 Complete When:
- [x] Backend: CRM (Lead, Prospect, Campaign, Proposal with 3 types)
- [x] Backend: Clients (Client, ClientEngagement, ClientPortalUser)
- [x] Frontend: CRM pages (Leads, Prospects, Campaigns, updated Proposals)
- [x] Frontend: Navigation reorganized (sidebar with sections)
- [ ] Migrations: All applied and tested
- [ ] Workflow: Lead → Client tested end-to-end
- [ ] Client Portal: All 6 sections functional
  - [x] Dashboard (basic)
  - [x] Documents (complete)
  - [ ] Work (not started)
  - [ ] Chat (not started)
  - [ ] Billing (partially implemented)
  - [ ] Engagement (not started)

### Ready for Production When:
- [ ] All P0 and P1 tasks complete
- [ ] 70%+ test coverage maintained
- [ ] All workflows tested end-to-end
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Security audit passed
- [ ] Deployment guide validated

---

## 📅 TIMELINE ESTIMATE

**Week 1 (Current):**
- Complete migrations and workflow testing (P0, P1)
- Backend signal enhancements (P1)

**Week 2-3:**
- Client Portal Work section (P2)
- Client Portal Chat section (P2)
- Client Portal Billing section (P2)

**Week 4:**
- Client Portal Engagement section (P2)
- Documentation updates (P2)
- Testing and QA (P2)

**Future (Phase 2):**
- Email Triage (P3)
- Scheduling (P3)
- Message Board (P3)
- Advanced features (P3)

---

## 🚀 NEXT IMMEDIATE ACTIONS

1. **Run database migrations** (`./migrate.sh`)
2. **Test CRM workflow** (Lead → Prospect → Proposal → Client)
3. **Implement email notifications** (signals.py TODOs)
4. **Start Client Portal Work section** (highest value for clients)

---

## 📞 QUESTIONS / DECISIONS NEEDED

1. **Client Portal Chat:** Daily reset at what time zone? (Currently: 00:00 UTC)
2. **Payment Methods:** ACH via Plaid - priority level? Additional costs?
3. **E-Signature:** DocuSign vs. HelloSign vs. other? (Licensing costs)
4. **Email Integration:** Outlook + Gmail sufficient? Need Exchange/IMAP?
5. **Scheduling:** Two-way sync or read-only calendar integration?
6. **Error Tracking:** Sentry approved for error monitoring? (Paid service)
7. **WebSocket Hosting:** Redis hosting solution for production? (AWS ElastiCache, Upstash, etc.)

---

**Status Legend:**
- 🔴 P0 = Critical/Blocker
- 🟠 P1 = High Priority
- 🟡 P2 = Medium Priority
- 🟢 P3 = Low Priority/Future
