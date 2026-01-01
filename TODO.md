# ConsultantPro - Task List

**Last Updated:** January 1, 2026

---

## Sprint-Ready Tasks (Broken Down for Implementation)

### Sprint 1: Authentication & Security (High Priority)

**Status:** Ready to Start  
**Total Estimated Time:** 44-64 hours  
**Prerequisites:**
- Current basic JWT authentication (see `src/modules/auth/views.py`)
- Django REST Framework with Simple JWT installed
- Access to Google Cloud Console and Azure AD for OAuth setup

**Documentation References:**
- [Security Model Requirements](docs/SECURITY_MODEL.md) - Section on authentication
- [Security Compliance](docs/SECURITY_COMPLIANCE.md) - Current security implementation
- [Current Authentication Implementation](src/modules/auth/views.py) - Basic JWT auth

#### SSO/OAuth Authentication (Google/Microsoft) - 16-24 hours
- [ ] **Sprint 1.1** Research and select OAuth library (django-allauth or python-social-auth) - 2-4 hours
- [ ] **Sprint 1.2** Implement Google OAuth provider integration - 4-6 hours
  - Configure Google Cloud Console credentials
  - Create OAuth callback endpoints
  - Map Google user data to User model
- [ ] **Sprint 1.3** Implement Microsoft OAuth provider integration - 4-6 hours
  - Configure Azure AD app registration
  - Create OAuth callback endpoints
  - Map Microsoft user data to User model
- [ ] **Sprint 1.4** Add SSO user account linking/creation logic - 3-4 hours
- [ ] **Sprint 1.5** Create admin UI for OAuth provider configuration - 3-4 hours

#### SAML Support for Enterprise SSO - 16-24 hours
- [ ] **Sprint 1.6** Research and select SAML library (python3-saml or djangosaml2) - 2-4 hours
- [ ] **Sprint 1.7** Implement SAML Service Provider configuration - 6-8 hours
  - Configure SAML metadata endpoints
  - Implement ACS (Assertion Consumer Service)
  - Create SLO (Single Logout) endpoints
- [ ] **Sprint 1.8** Add SAML IdP metadata management UI - 4-6 hours
- [ ] **Sprint 1.9** Implement SAML attribute mapping configuration - 4-6 hours

#### Multi-Factor Authentication (MFA) - 12-16 hours
- [ ] **Sprint 1.10** Select MFA library (django-otp or django-two-factor-auth) - 2-3 hours
- [ ] **Sprint 1.11** Implement TOTP (Time-based OTP) authentication - 4-5 hours
- [ ] **Sprint 1.12** Add SMS-based OTP as backup method - 4-5 hours
  - Leverage existing SMS infrastructure (see `src/modules/sms/`)
- [ ] **Sprint 1.13** Create MFA enrollment and management UI - 2-3 hours

**Notes:**
- SMS-based OTP (Sprint 1.12) can utilize existing Twilio integration in `src/modules/sms/`
- Ensure all new authentication methods maintain firm-level tenant isolation
- All authentication endpoints must implement rate limiting (see existing implementation in `src/modules/auth/views.py`)
- Follow security guidelines in [Security Model](docs/SECURITY_MODEL.md)

### Sprint 2: Calendar Integration Completion (High Priority)

#### Complete Calendar Sync Integration - 20-32 hours
- [ ] **Sprint 2.1** Implement Google Calendar API sync service - 8-12 hours
  - Create event pull/push operations
  - Handle recurring events
  - Implement conflict resolution
- [ ] **Sprint 2.2** Implement Outlook Calendar API sync service - 8-12 hours
  - Create event pull/push operations
  - Handle recurring events
  - Implement conflict resolution
- [ ] **Sprint 2.3** Add sync configuration UI - 2-4 hours
- [ ] **Sprint 2.4** Implement sync status monitoring and error handling - 2-4 hours

### Sprint 3: Accounting Integrations (Medium Priority)

#### QuickBooks Online Integration - 24-32 hours
- [ ] **Sprint 3.1** Research QuickBooks Online API and OAuth 2.0 requirements - 2-4 hours
- [ ] **Sprint 3.2** Implement QuickBooks OAuth authentication flow - 4-6 hours
- [ ] **Sprint 3.3** Create invoice sync (push invoices to QuickBooks) - 6-8 hours
- [ ] **Sprint 3.4** Create payment sync (pull payment data from QuickBooks) - 6-8 hours
- [ ] **Sprint 3.5** Add customer sync (bidirectional sync) - 4-6 hours
- [ ] **Sprint 3.6** Create admin UI for QuickBooks configuration - 2-4 hours

#### Xero Accounting Integration - 24-32 hours
- [ ] **Sprint 3.7** Research Xero API and OAuth 2.0 requirements - 2-4 hours
- [ ] **Sprint 3.8** Implement Xero OAuth authentication flow - 4-6 hours
- [ ] **Sprint 3.9** Create invoice sync (push invoices to Xero) - 6-8 hours
- [ ] **Sprint 3.10** Create payment sync (pull payment data from Xero) - 6-8 hours
- [ ] **Sprint 3.11** Add contact sync (bidirectional sync) - 4-6 hours
- [ ] **Sprint 3.12** Create admin UI for Xero configuration - 2-4 hours

### Sprint 4: E-signature Integration (Medium Priority)

#### DocuSign/HelloSign Integration - 20-28 hours
- [ ] **Sprint 4.1** Select e-signature provider and research API - 2-4 hours
- [ ] **Sprint 4.2** Implement e-signature provider OAuth/API authentication - 4-6 hours
- [ ] **Sprint 4.3** Create envelope creation and send workflow - 6-8 hours
- [ ] **Sprint 4.4** Implement webhook handlers for signature status updates - 4-6 hours
- [ ] **Sprint 4.5** Add signature request UI and status tracking - 4-6 hours

### Sprint 5: Performance & Reporting (Low-Medium Priority)

#### Materialized Views for Reporting Performance - 12-16 hours
- [ ] **Sprint 5.1** Identify slow report queries requiring materialized views - 2-3 hours
- [ ] **Sprint 5.2** Create materialized views for revenue reporting - 3-4 hours
- [ ] **Sprint 5.3** Create materialized views for utilization reporting - 3-4 hours
- [ ] **Sprint 5.4** Implement refresh strategy (periodic vs on-demand) - 2-3 hours
- [ ] **Sprint 5.5** Add monitoring for materialized view freshness - 2-2 hours

---

## Large Features (Requires Further Breakdown)

### Document Co-authoring with Real-Time Collaboration - Very High Complexity (32-48 hours)
**Status:** Requires additional research and architectural planning before sprint breakdown

**Preliminary breakdown:**
- [ ] Research collaboration technologies (Operational Transform vs CRDT)
- [ ] Select real-time communication technology (WebSockets, Server-Sent Events)
- [ ] Design collaborative editing architecture
- [ ] Implement presence detection and cursor tracking
- [ ] Create conflict resolution strategy
- [ ] Implement version control integration
- [ ] Add permission model for collaborative documents
- [ ] Build UI components for real-time editing

**Note:** This feature requires significant architectural decisions and should be broken down further after initial research phase.

---

## Deferred Items (Low Priority)

- [ ] Slack API integration - Placeholder implemented in src/modules/core/notifications.py
- [ ] E-signature workflow expansion - Basic placeholder implemented in src/modules/clients/views.py

---

## Sprint 6-10: Platform Transformation Tasks (Low Priority)

### Sprint 6: Event-Driven Architecture - 16-24 hours
- [ ] **Sprint 6.1** Design unified event bus architecture - 3-4 hours
- [ ] **Sprint 6.2** Implement event publisher service - 4-6 hours
- [ ] **Sprint 6.3** Create event subscriber/handler framework - 4-6 hours
- [ ] **Sprint 6.4** Add event routing and filtering logic - 3-4 hours
- [ ] **Sprint 6.5** Create event monitoring and debugging tools - 2-4 hours

### Sprint 7: SCIM Provisioning - 16-24 hours
- [ ] **Sprint 7.1** Research SCIM 2.0 specification - 2-4 hours
- [ ] **Sprint 7.2** Implement SCIM user provisioning endpoints - 6-8 hours
- [ ] **Sprint 7.3** Implement SCIM group provisioning endpoints - 4-6 hours
- [ ] **Sprint 7.4** Add SCIM authentication and authorization - 2-4 hours
- [ ] **Sprint 7.5** Create SCIM configuration UI - 2-4 hours

### Sprint 8: Audit Review UI - 12-16 hours
- [ ] **Sprint 8.1** Design audit review dashboard wireframes - 2-3 hours
- [ ] **Sprint 8.2** Implement audit log query and filter backend - 4-6 hours
- [ ] **Sprint 8.3** Create audit review UI components - 4-5 hours
- [ ] **Sprint 8.4** Add audit export functionality (CSV/JSON) - 2-2 hours

### Sprint 9: Integration Marketplace - 20-28 hours
- [ ] **Sprint 9.1** Design integration marketplace architecture - 3-4 hours
- [ ] **Sprint 9.2** Create integration registry model - 4-6 hours
- [ ] **Sprint 9.3** Implement integration installation workflow - 6-8 hours
- [ ] **Sprint 9.4** Add integration configuration UI - 4-6 hours
- [ ] **Sprint 9.5** Create integration marketplace catalog UI - 3-4 hours

### Sprint 10: Records Management System - 16-24 hours
- [ ] **Sprint 10.1** Design immutable records architecture - 3-4 hours
- [ ] **Sprint 10.2** Implement record versioning with immutability - 6-8 hours
- [ ] **Sprint 10.3** Add record retention policies - 4-6 hours
- [ ] **Sprint 10.4** Create records audit trail - 3-6 hours

### Sprint 11: Custom Dashboard Builder - 20-28 hours
- [ ] **Sprint 11.1** Design widget system architecture - 3-4 hours
- [ ] **Sprint 11.2** Implement core widget framework - 6-8 hours
- [ ] **Sprint 11.3** Create 5-7 initial widget types - 6-8 hours
- [ ] **Sprint 11.4** Build drag-and-drop dashboard builder UI - 5-8 hours

### Sprint 12: ERP Connectors - 24-32 hours per connector
- [ ] **Sprint 12.1** Research target ERP systems (SAP, Oracle, NetSuite) - 2-4 hours
- [ ] **Sprint 12.2** Design ERP connector framework - 4-6 hours
- [ ] **Sprint 12.3** Implement first ERP connector (e.g., NetSuite) - 12-16 hours
- [ ] **Sprint 12.4** Create ERP sync monitoring and error handling - 4-6 hours
- [ ] **Sprint 12.5** Build ERP configuration UI - 2-4 hours

### Sprint 13: AI-Powered Lead Scoring - 16-24 hours
- [ ] **Sprint 13.1** Research ML frameworks (scikit-learn, TensorFlow) - 2-4 hours
- [ ] **Sprint 13.2** Collect and prepare training data - 4-6 hours
- [ ] **Sprint 13.3** Train lead scoring model - 4-6 hours
- [ ] **Sprint 13.4** Implement model inference service - 4-6 hours
- [ ] **Sprint 13.5** Add model performance monitoring - 2-2 hours

### Sprint 14: PSA Operations Suite - 28-40 hours
- [ ] **Sprint 14.1** Design PSA planning architecture - 4-6 hours
- [ ] **Sprint 14.2** Implement resource planning module - 8-12 hours
- [ ] **Sprint 14.3** Create capacity analytics dashboard - 8-12 hours
- [ ] **Sprint 14.4** Add revenue forecasting - 4-6 hours
- [ ] **Sprint 14.5** Build project profitability analytics - 4-6 hours

---

## Summary Statistics

**Total Sprint Tasks:** 78 tasks across 14 sprints
- **High Priority (Sprints 1-2):** 17 tasks (~52-72 hours)
- **Medium Priority (Sprints 3-5):** 24 tasks (~68-92 hours)
- **Low Priority (Sprints 6-14):** 37 tasks (~184-272 hours)

**Large Features Requiring Further Planning:** 1 feature (Document co-authoring)

---

## Notes

- **Focus:** High priority authentication and security features first (Sprints 1-2)
- **Next Steps:** Complete calendar sync integration, then move to accounting integrations
- **Completed Work:** See [TODO_COMPLETED.md](./TODO_COMPLETED.md) for historical reference of all completed tasks
- **Sprint Planning:** Each sprint task includes estimated hours for better planning
- **Flexibility:** Task breakdowns can be adjusted based on team capacity and priorities

---

## Reference Documentation

- [System Invariants](spec/SYSTEM_INVARIANTS.md)
- [Platform Capabilities Inventory](docs/03-reference/platform-capabilities.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Implementation Assessment](docs/ARCHIVE/roadmap-legacy-2025-12-30/IMPLEMENTATION_ASSESSMENT.md)
- [Completed Tasks Archive](TODO_COMPLETED.md)
