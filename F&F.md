# Features & Functionality Map (F&F)

This document maps **existing and future features** for each module in the codebase, along with an **estimated completion percentage** and **AI-assisted recommendations**. It is intentionally conservative: a feature is marked complete **only** when there is clear evidence in module-level code (file names or directories) indicating the capability exists.

## Methodology & Evidence Boundaries
- **Module inventory source:** `src/modules/` directory listing (module names and their top-level files/directories).
- **Completion scoring:** `completed items / total checklist items` (rounded to whole percent).
- **UNKNOWN rule:** If a feature is expected but has no clear evidence in module-level code, it is left unchecked and treated as **UNKNOWN**.
- **AI infrastructure scan:** A targeted search for LLM/AI-related terms in `src/modules` did **not** reveal explicit AI/LLM infrastructure (e.g., `openai`, `gpt`, `embedding`). Existing AI assistance infrastructure is therefore treated as **UNKNOWN** unless clearly present in module code.

---

## Existing Modules (Source of Truth)
- accounting_integrations
- ad_sync
- assets
- auth
- automation
- calendar
- clients
- communications
- core
- crm
- delivery
- documents
- email_ingestion
- esignature
- finance
- firm
- integrations
- jobs
- knowledge
- marketing
- onboarding
- orchestration
- pricing
- projects
- recurrence
- sms
- snippets
- support
- tracking
- webhooks

---

## accounting_integrations — 80% ████████░░

### Feature & Functionality Checklist
- [x] External accounting data models (models.py)
- [x] Admin configuration (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Sync orchestration (sync_service.py)
- [x] QuickBooks integration service (quickbooks_service.py)
- [x] Xero integration service (xero_service.py)
- [x] Signal hooks (signals.py)
- [ ] Reconciliation dashboards & reporting (UNKNOWN)
- [ ] Error alerting/observability integration (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Auto-categorize transactions and suggest chart-of-accounts mappings.
  - Flag anomalous reconciliation mismatches with likely root causes.
- **Planned AI assistance (cross-module):**
  - Summarize billing discrepancies by client/project and open CRM follow-ups.
  - Recommend cash-flow impacts based on upcoming invoices and calendar events.

---

## ad_sync — 70% ███████░░░

### Feature & Functionality Checklist
- [x] Ad sync data models (models.py)
- [x] Admin configuration (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Connector abstraction (connector.py)
- [x] Sync service orchestration (sync_service.py)
- [x] Background tasks (tasks.py)
- [ ] Scheduling/cron policy management (UNKNOWN)
- [ ] Error reporting & retry analytics (UNKNOWN)
- [ ] Campaign performance dashboards (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Detect sync anomalies and recommend corrective actions (e.g., token refresh).
  - Predict likely campaign metadata mismatches before sync runs.
- **Planned AI assistance (cross-module):**
  - Connect campaign spend to CRM outcomes and suggest budget reallocations.
  - Auto-generate client-facing summaries from synced ad data.

---

## assets — 20% ██░░░░░░░░

### Feature & Functionality Checklist
- [x] Asset data models (models.py)
- [x] Admin management (admin.py)
- [ ] API endpoints for asset CRUD (UNKNOWN)
- [ ] Upload pipeline & storage abstraction (UNKNOWN)
- [ ] CDN delivery integration (UNKNOWN)
- [ ] Metadata tagging & search (UNKNOWN)
- [ ] Versioning & history (UNKNOWN)
- [ ] Access controls & sharing (UNKNOWN)
- [ ] Asset transformations (resize/convert) (UNKNOWN)
- [ ] Audit trails & retention policies (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Auto-tag assets based on content and usage context.
  - Detect duplicates and suggest de-duplication actions.
- **Planned AI assistance (cross-module):**
  - Recommend assets for CRM/marketing campaigns based on past performance.
  - Summarize asset usage for project status updates.

---

## auth — 90% █████████░

### Feature & Functionality Checklist
- [x] Authentication models (models.py)
- [x] Auth views/endpoints (views.py/urls.py)
- [x] Serialization layer (serializers.py)
- [x] Authentication backend & helpers (authentication.py)
- [x] MFA flows (mfa_views.py)
- [x] OAuth flows (oauth_views.py)
- [x] SAML flows (saml_views.py)
- [x] Role/permission mapping (role_permissions.py)
- [x] Cookie/session utilities (cookies.py)
- [ ] Account recovery & password reset flows (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Detect suspicious login patterns and suggest step-up authentication.
  - Draft user-facing security advisories after risky events.
- **Planned AI assistance (cross-module):**
  - Recommend least-privilege role adjustments based on usage patterns.
  - Summarize access changes for audit reporting.

---

## automation — 80% ████████░░

### Feature & Functionality Checklist
- [x] Automation models (models.py)
- [x] Trigger library (triggers.py)
- [x] Action library (actions.py)
- [x] Execution engine (executor.py)
- [x] Analytics/metrics (analytics.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Admin management (admin.py)
- [ ] Versioning/rollback for automations (UNKNOWN)
- [ ] Audit trails for automation runs (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Recommend new triggers/actions based on frequent manual workflows.
  - Detect failing automation patterns and suggest fixes.
- **Planned AI assistance (cross-module):**
  - Auto-create CRM tasks when automation failures impact clients.
  - Suggest calendar reminders when automation bottlenecks occur.

---

## calendar — 82% ████████░░

### Feature & Functionality Checklist
- [x] Availability management (availability_service.py)
- [x] Booking workflows (booking_service.py)
- [x] Booking validation (booking_validation_service.py)
- [x] Routing & round-robin assignment (routing_service.py, round_robin_service.py)
- [x] Meeting polls & group events (meeting_poll_service.py, group_event_service.py)
- [x] Invitations (invitation_service.py)
- [x] Google Calendar integration (google_service.py)
- [x] Microsoft Calendar integration (microsoft_service.py)
- [x] Calendar sync services (sync_service.py, sync_services.py)
- [ ] Calendar analytics/reporting (UNKNOWN)
- [ ] Resource capacity planning (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Optimize availability slots based on historical booking outcomes.
  - Suggest meeting times that minimize context-switching.
- **Planned AI assistance (cross-module):**
  - Coordinate CRM follow-up sequences based on booked meetings.
  - Surface project deadline risks based on calendar load.

---

## clients — 82% ████████░░

### Feature & Functionality Checklist
- [x] Client data models (models/)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Segmentation logic (segmentation.py)
- [x] Bulk operations (bulk_operations.py)
- [x] Contact merging (contact_merger.py)
- [x] Health scoring (health_score_calculator.py, health_score_views.py)
- [x] Client portal experience (portal_views.py, portal_branding.py)
- [ ] Client lifecycle automation (UNKNOWN)
- [ ] Client analytics dashboards (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Predict churn risk and recommend retention actions.
  - Summarize client history for faster onboarding.
- **Planned AI assistance (cross-module):**
  - Recommend project priorities based on client health score trends.
  - Generate billing escalation reminders for at-risk accounts.

---

## communications — 20% ██░░░░░░░░

### Feature & Functionality Checklist
- [x] Communication data models (models.py)
- [x] API endpoints (urls.py/views.py)
- [ ] Multi-channel support (email/SMS/push) (UNKNOWN)
- [ ] Template management (UNKNOWN)
- [ ] Delivery tracking (UNKNOWN)
- [ ] Scheduling/queueing (UNKNOWN)
- [ ] Conversation threading (UNKNOWN)
- [ ] Permissions & privacy controls (UNKNOWN)
- [ ] Spam/abuse handling (UNKNOWN)
- [ ] Analytics & engagement reporting (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Draft response suggestions and summarize conversation history.
  - Detect negative sentiment and recommend escalation.
- **Planned AI assistance (cross-module):**
  - Create CRM tasks from communication outcomes.
  - Suggest calendar follow-ups based on message intent.

---

## core — 92% █████████░

### Feature & Functionality Checklist
- [x] Access controls (access_controls.py)
- [x] Encryption utilities (encryption.py)
- [x] Data erasure workflows (erasure.py)
- [x] Governance controls (governance.py)
- [x] Input validation (input_validation.py)
- [x] Logging & structured logging (logging_utils.py, structured_logging.py)
- [x] Notifications utilities (notifications.py)
- [x] Observability & telemetry (observability.py, telemetry.py)
- [x] Rate limiting (rate_limiting.py)
- [x] Retention & purge workflows (retention.py, purge.py)
- [x] Security monitoring (security_monitoring.py)
- [ ] Feature flag/experimentation framework (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Detect anomalous security events and draft incident summaries.
  - Recommend validation rule updates based on recurring errors.
- **Planned AI assistance (cross-module):**
  - Summarize system health for daily ops reviews.
  - Auto-suggest retention policy changes based on usage trends.

---

## crm — 80% ████████░░

### Feature & Functionality Checklist
- [x] CRM data models (models/)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Lead scoring (lead_scoring.py)
- [x] Assignment automation (assignment_automation.py)
- [x] Deal rotting alerts (deal_rotting_alerts.py)
- [x] Enrichment workflows (enrichment_service.py, enrichment_tasks.py)
- [ ] Pipeline forecasting (UNKNOWN)
- [ ] Activity timeline & audit history (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Predict deal outcomes and recommend next best actions.
  - Generate personalized outreach suggestions.
- **Planned AI assistance (cross-module):**
  - Tie client health scores to CRM pipeline prioritization.
  - Auto-create onboarding checklists from closed-won deals.

---

## delivery — 20% ██░░░░░░░░

### Feature & Functionality Checklist
- [x] Delivery data models (models.py)
- [x] Delivery instantiation logic (instantiator.py)
- [ ] API endpoints (UNKNOWN)
- [ ] Delivery scheduling (UNKNOWN)
- [ ] Status tracking & SLAs (UNKNOWN)
- [ ] Retry & failure handling (UNKNOWN)
- [ ] Notifications (UNKNOWN)
- [ ] Audit trails (UNKNOWN)
- [ ] Reporting dashboards (UNKNOWN)
- [ ] Integration hooks for communications/webhooks (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Predict delivery delays and propose mitigations.
  - Summarize delivery performance by client.
- **Planned AI assistance (cross-module):**
  - Trigger CRM follow-ups based on delivery outcomes.
  - Align project timelines with delivery status changes.

---

## documents — 64% ██████░░░░

### Feature & Functionality Checklist
- [x] Document data models (models/)
- [x] Admin management (admin.py)
- [x] Malware scanning (malware_scan.py)
- [x] Permissions handling (permissions.py)
- [x] Reconciliation utilities (reconciliation.py)
- [x] Document services layer (services.py)
- [ ] API endpoints for document CRUD (UNKNOWN)
- [x] Versioning (models/versions.py)
- [ ] Approval workflows (UNKNOWN)
- [ ] Retention & archival policies (UNKNOWN)
- [ ] Search & indexing (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Auto-classify documents and extract key metadata.
  - Detect inconsistencies in reconciled documents.
- **Planned AI assistance (cross-module):**
  - Suggest required documents for onboarding or billing.
  - Summarize document changes in project updates.

---

## email_ingestion — 70% ███████░░░

### Feature & Functionality Checklist
- [x] Ingestion data models (models.py)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Ingestion services (services.py)
- [x] Retry handling (retry_service.py)
- [x] Staleness handling (staleness_service.py)
- [ ] Attachment processing & storage (UNKNOWN)
- [ ] Spam filtering (UNKNOWN)
- [ ] Analytics/reporting dashboards (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Classify incoming emails to appropriate client/project queues.
  - Summarize long threads for faster triage.
- **Planned AI assistance (cross-module):**
  - Create CRM tasks from important email intents.
  - Auto-link emails to relevant documents and projects.

---

## esignature — 60% ██████░░░░

### Feature & Functionality Checklist
- [x] E-signature data models (models.py)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] DocuSign integration (docusign_service.py)
- [x] Signal hooks (signals.py)
- [ ] Multi-provider support (UNKNOWN)
- [ ] Template & envelope management UI (UNKNOWN)
- [ ] Audit trails & legal hold (UNKNOWN)
- [ ] Reminder & expiration workflows (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Suggest signature order and routing based on contract context.
  - Summarize deviations from standard contract templates.
- **Planned AI assistance (cross-module):**
  - Trigger project kickoff tasks after final signature.
  - Link signed documents to billing milestones.

---

## finance — 58% ██████░░░░

### Feature & Functionality Checklist
- [x] Finance data models (models.py)
- [x] Admin management (admin.py)
- [x] Billing logic (billing.py)
- [x] Billing ledger (billing_ledger.py)
- [x] Reconciliation utilities (reconciliation.py)
- [x] Finance services layer (services.py)
- [x] Square integration (square_service.py)
- [ ] API endpoints for finance operations (UNKNOWN)
- [ ] Tax/VAT handling (UNKNOWN)
- [ ] Financial reporting dashboards (UNKNOWN)
- [ ] Dunning & collections workflows (UNKNOWN)
- [ ] Forecasting & cashflow projections (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Forecast cash flow and flag shortfalls early.
  - Detect anomalous billing ledger entries.
- **Planned AI assistance (cross-module):**
  - Recommend invoice timing based on project milestones.
  - Identify clients at risk based on CRM and payment data.

---

## firm — 67% ███████░░░

### Feature & Functionality Checklist
- [x] Firm data models (models.py)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Permissions handling (permissions.py)
- [x] Audit utilities (audit.py)
- [x] Export utilities (export.py)
- [x] Provisioning flows (provisioning.py)
- [x] Profile views/serializers (profile_views.py, profile_serializers.py)
- [ ] Org-level settings UI (UNKNOWN)
- [ ] Multi-region data residency (UNKNOWN)
- [ ] Compliance reporting dashboards (UNKNOWN)
- [ ] Firm-level analytics & KPIs (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Summarize firm-wide operational risks and compliance gaps.
  - Recommend permission changes based on access usage.
- **Planned AI assistance (cross-module):**
  - Provide an executive daily briefing using CRM, finance, and projects data.
  - Identify workflow bottlenecks affecting multiple teams.

---

## integrations — 50% █████░░░░░

### Feature & Functionality Checklist
- [x] Integration data models (models.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Integration services (services.py)
- [x] Admin management (admin.py)
- [ ] OAuth token lifecycle management (UNKNOWN)
- [ ] Webhook ingestion & verification (UNKNOWN)
- [ ] Integration health dashboards (UNKNOWN)
- [ ] Marketplace discovery/registry (UNKNOWN)
- [ ] Usage analytics & quotas (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Recommend integrations based on usage patterns.
  - Detect integration failures and suggest fixes.
- **Planned AI assistance (cross-module):**
  - Auto-create support tickets for repeated integration errors.
  - Summarize integration impact on client outcomes.

---

## jobs — 30% ███░░░░░░░

### Feature & Functionality Checklist
- [x] Job data models (models.py)
- [x] Admin views (admin_views.py)
- [x] Payload validation rules (payload_validator.py)
- [ ] API endpoints for job lifecycle (UNKNOWN)
- [ ] Scheduling & retry policies (UNKNOWN)
- [ ] Job queue/worker integration (UNKNOWN)
- [ ] Metrics & observability for jobs (UNKNOWN)
- [ ] Dead-letter handling (UNKNOWN)
- [ ] Priority & SLA configuration (UNKNOWN)
- [ ] Audit trails (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Predict job failures and propose retries or backoff.
  - Suggest payload improvements for reliability.
- **Planned AI assistance (cross-module):**
  - Alert project owners when critical jobs fail.
  - Coordinate retry timing with calendar load.

---

## knowledge — 50% █████░░░░░

### Feature & Functionality Checklist
- [x] Knowledge data models (models.py)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Basic knowledge CRUD workflows (views.py)
- [ ] Search & semantic retrieval (UNKNOWN)
- [ ] Versioning & approval workflows (UNKNOWN)
- [ ] Knowledge base analytics (UNKNOWN)
- [ ] Access controls & sharing policies (UNKNOWN)
- [ ] Content import/export (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Provide answer generation and citation linking.
  - Summarize long knowledge articles into briefs.
- **Planned AI assistance (cross-module):**
  - Suggest knowledge articles relevant to support tickets.
  - Auto-link documents and snippets to knowledge entries.

---

## marketing — 58% ██████░░░░

### Feature & Functionality Checklist
- [x] Marketing data models (models.py)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Marketing jobs (jobs.py)
- [x] Queue processing (queue.py)
- [x] Campaign views (views.py)
- [ ] Multi-channel orchestration (UNKNOWN)
- [ ] A/B testing framework (UNKNOWN)
- [ ] Engagement analytics dashboards (UNKNOWN)
- [ ] Compliance & consent management (UNKNOWN)
- [ ] Asset library integration (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Generate campaign briefs and subject lines.
  - Predict engagement and recommend send times.
- **Planned AI assistance (cross-module):**
  - Target campaigns using CRM segmentation and client health scores.
  - Update project timelines based on campaign results.

---

## onboarding — 50% █████░░░░░

### Feature & Functionality Checklist
- [x] Onboarding data models (models.py)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Basic onboarding workflows (views.py)
- [ ] Guided checklist templates (UNKNOWN)
- [ ] Document collection & validation (UNKNOWN)
- [ ] Client progress dashboards (UNKNOWN)
- [ ] Automated reminders (UNKNOWN)
- [ ] Role-based approvals (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Auto-generate onboarding checklists by client profile.
  - Detect blockers and suggest next steps.
- **Planned AI assistance (cross-module):**
  - Link onboarding tasks to project plans and schedules.
  - Trigger billing setup once onboarding milestones complete.

---

## orchestration — 30% ███░░░░░░░

### Feature & Functionality Checklist
- [x] Orchestration data models (models.py)
- [x] Execution engine (executor.py)
- [x] App configuration (apps.py)
- [ ] API endpoints for orchestration workflows (UNKNOWN)
- [ ] Workflow definitions & versioning (UNKNOWN)
- [ ] Event-driven triggers (UNKNOWN)
- [ ] Observability & tracing (UNKNOWN)
- [ ] Error handling & retries (UNKNOWN)
- [ ] Access controls (UNKNOWN)
- [ ] Admin UI (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Recommend workflow optimizations based on execution logs.
  - Detect bottlenecks and propose parallelization.
- **Planned AI assistance (cross-module):**
  - Coordinate automation and jobs scheduling across modules.
  - Suggest process improvements based on support outcomes.

---

## pricing — 70% ███████░░░

### Feature & Functionality Checklist
- [x] Pricing data models (models.py)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Pricing evaluator (evaluator.py)
- [x] Schema compatibility checks (schema_compatibility.py)
- [x] Apps configuration (apps.py)
- [ ] Discounting & promotions engine (UNKNOWN)
- [ ] Price versioning & audit trails (UNKNOWN)
- [ ] Pricing analytics dashboards (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Recommend pricing adjustments based on win/loss data.
  - Detect margin erosion and suggest corrective actions.
- **Planned AI assistance (cross-module):**
  - Suggest pricing tiers based on client usage and support load.
  - Align pricing changes with marketing campaigns.

---

## projects — 40% ████░░░░░░

### Feature & Functionality Checklist
- [x] Project data models (models.py)
- [x] Admin management (admin.py)
- [x] Critical path analysis (critical_path.py)
- [x] Signal hooks (signals.py)
- [ ] API endpoints for project CRUD (UNKNOWN)
- [ ] Gantt/timeline visualization (UNKNOWN)
- [ ] Resource management (UNKNOWN)
- [ ] Milestone & dependency management UI (UNKNOWN)
- [ ] Project health dashboards (UNKNOWN)
- [ ] Time tracking & cost rollups (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Predict project slippage and suggest mitigations.
  - Summarize weekly project status updates.
- **Planned AI assistance (cross-module):**
  - Tie project outcomes to CRM forecasts.
  - Align invoices with project milestones.

---

## recurrence — 30% ███░░░░░░░

### Feature & Functionality Checklist
- [x] Recurrence data models (models.py)
- [x] Recurrence generator (generator.py)
- [x] Backfill utilities (backfill.py)
- [ ] API endpoints for recurrence rules (UNKNOWN)
- [ ] UI for recurrence configuration (UNKNOWN)
- [ ] Exception handling & overrides (UNKNOWN)
- [ ] Timezone-aware recurrence rules (UNKNOWN)
- [ ] Recurrence analytics (UNKNOWN)
- [ ] Validation for rule correctness (UNKNOWN)
- [ ] Versioning/audit trails (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Suggest optimal recurrence patterns based on usage history.
  - Detect conflicting recurrence schedules.
- **Planned AI assistance (cross-module):**
  - Sync recurring tasks with calendar and project schedules.
  - Auto-create reminders in communications workflows.

---

## sms — 70% ███████░░░

### Feature & Functionality Checklist
- [x] SMS data models (models.py)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Twilio integration (twilio_service.py)
- [x] Webhook handling (webhooks.py)
- [x] Apps configuration (apps.py)
- [ ] Template library (UNKNOWN)
- [ ] Scheduling/queueing (UNKNOWN)
- [ ] Delivery analytics dashboards (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Draft SMS responses and suggest tone adjustments.
  - Predict opt-out risk and recommend messaging cadence.
- **Planned AI assistance (cross-module):**
  - Trigger SMS reminders for calendar events.
  - Notify clients about invoice status changes.

---

## snippets — 50% █████░░░░░

### Feature & Functionality Checklist
- [x] Snippet data models (models.py)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Basic snippet CRUD workflows (views.py)
- [ ] Versioning & history (UNKNOWN)
- [ ] Categorization & tagging (UNKNOWN)
- [ ] Usage analytics (UNKNOWN)
- [ ] Access controls & sharing (UNKNOWN)
- [ ] Bulk import/export (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Recommend snippet reuse based on communication context.
  - Auto-generate snippet variations for tone or length.
- **Planned AI assistance (cross-module):**
  - Suggest snippets for support responses.
  - Auto-link snippets to knowledge base articles.

---

## support — 50% █████░░░░░

### Feature & Functionality Checklist
- [x] Support data models (models.py)
- [x] Admin management (admin.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] Basic support workflows (views.py)
- [ ] SLA management (UNKNOWN)
- [ ] Ticket routing & escalation (UNKNOWN)
- [ ] Knowledge base integration (UNKNOWN)
- [ ] Customer satisfaction surveys (UNKNOWN)
- [ ] Support analytics dashboards (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Draft responses and recommend resolutions.
  - Predict ticket priority based on content.
- **Planned AI assistance (cross-module):**
  - Create CRM tasks for high-risk support issues.
  - Schedule calendar follow-ups for unresolved tickets.

---

## tracking — 50% █████░░░░░

### Feature & Functionality Checklist
- [x] Tracking data models (models.py)
- [x] API endpoints (urls.py/views.py)
- [x] Serialization layer (serializers.py)
- [x] App configuration (apps.py)
- [x] Basic tracking workflows (views.py)
- [ ] Event taxonomy & governance (UNKNOWN)
- [ ] Session/user stitching (UNKNOWN)
- [ ] Data retention controls (UNKNOWN)
- [ ] Analytics dashboards (UNKNOWN)
- [ ] Export & integration hooks (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Detect anomalous tracking events and suggest fixes.
  - Summarize key usage trends.
- **Planned AI assistance (cross-module):**
  - Feed tracking insights into CRM health scoring.
  - Recommend marketing campaigns based on behavior data.

---

## webhooks — 40% ████░░░░░░

### Feature & Functionality Checklist
- [x] Webhook data models (models.py)
- [x] Admin management (admin.py)
- [x] Jobs/dispatch processing (jobs.py)
- [x] Queue handling (queue.py)
- [ ] Webhook endpoints & verification (UNKNOWN)
- [ ] Retry/backoff policies (UNKNOWN)
- [ ] Delivery status tracking (UNKNOWN)
- [ ] Secret rotation & signing (UNKNOWN)
- [ ] Tenant isolation policies (UNKNOWN)
- [ ] Observability dashboards (UNKNOWN)

### AI-assisted Recommendations
- **Existing AI assistance infrastructure:** UNKNOWN (no explicit AI/LLM code detected in module files).
- **Planned AI assistance (domain-specific):**
  - Detect failing webhook destinations and suggest fixes.
  - Recommend optimal retry strategies based on history.
- **Planned AI assistance (cross-module):**
  - Generate support tickets for repeated webhook failures.
  - Trigger CRM alerts when client integrations are degraded.

---

## Final Cross-Module Assessment (Potentially Missed Features)

Even with conservative scoring, there are cross-cutting feature classes that may be missing or not explicitly visible at module level. Potential gaps to validate in future audits:
- **Unified permissions & policy management** across all modules (beyond core/auth).
- **Comprehensive analytics dashboards** (module-level reporting appears sparse).
- **Full audit trails and compliance reports** for regulated workflows (finance, documents, esignature).
- **Consistent API coverage** for modules lacking `urls.py`/`views.py` at module level.
- **AI/LLM integration layer** for the assistant behavior and cross-module reasoning.
- **Mobile/portal-specific UX flows** that may live outside `src/modules`.
- **Centralized notification & messaging strategy** across communications, sms, and email.
