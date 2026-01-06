# TODO.md — Repository Task List

Document Type: Workflow
Last Updated: 2026-01-05
Task Truth Source: **TODO.md**

This file is the single source of truth for actionable work.
If another document disagrees, the task record in this file wins (unless the Constitution overrides).

## Task schema (required)
- **ID**: `T-###` (unique)
- **Priority**: `P0 | P1 | P2 | P3`
- **Type**: `SECURITY | RELEASE | DEPENDENCY | DOCS | QUALITY | BUG | FEATURE | CHORE`
- **Owner**: `AGENT | Trevor`
- **Status**: `READY | BLOCKED | IN-PROGRESS | IN-REVIEW`
- **Context**: why the task exists (1–5 bullets)
- **Acceptance Criteria**: verifiable checklist
- **References**: file paths and/or links inside this repo
- **Dependencies**: task IDs (if any)
- **Effort**: `S | M | L` (relative; explain if unclear)

### Priority meaning
- **P0**: blocks production readiness or causes security/data loss
- **P1**: high impact; do within 7 days
- **P2**: important but not urgent; do within 30 days
- **P3**: backlog/tech debt; do when convenient

### Ownership rule
- **Owner: AGENT** means the task can be executed by a coding agent in-repo.
- **Owner: Trevor** means it requires external actions (provider dashboards, DNS, billing, approvals).

## Active tasks

### T-011: Implement portal branding infrastructure integrations (DNS, SSL, email templates)
Priority: P1
Type: FEATURE
Owner: AGENT
Status: READY
Context:
- Portal branding references DNS/SSL/email template integrations but the integrations are not implemented.
Acceptance Criteria:
- [ ] DNS/SSL integration paths are implemented and wired into portal branding workflows.
- [ ] Email template integration is implemented for portal branding emails.
- [ ] Inline placeholders referencing this work are removed or updated.
References:
- src/modules/clients/portal_branding.py
- src/modules/clients/portal_views.py
Dependencies: None
Effort: M

### T-013: Decide and document the frontend component library
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Context:
- Architecture documentation calls out a TBD component library, blocking consistent UI implementation choices.
Acceptance Criteria:
- [ ] Component library decision documented with rationale.
- [ ] Architecture doc updated to reflect the chosen library.
References:
- docs/ARCHITECTURE.md
Dependencies: None
Effort: S

### T-014: Implement document lock, signed-url, and upload request endpoints
Priority: P1
Type: FEATURE
Owner: AGENT
Status: READY
Context:
- API mapping lists partial document endpoints with TBD notes, indicating missing canonical endpoints.
Acceptance Criteria:
- [ ] Document lock, signed-url, and upload request endpoints exist with DRF views and routes.
- [ ] API endpoint mapping updated to remove TBD notes.
- [ ] Authorization mapping and permissions documented.
References:
- docs/API_ENDPOINT_AUTHORIZATION_MAPPING.md
- src/modules/documents/
Dependencies: None
Effort: M

### T-015: Pin bcrypt to a specific version in production requirements
Priority: P2
Type: DEPENDENCY
Owner: AGENT
Status: READY
Context:
- bcrypt is specified with a range, which can cause non-reproducible builds.
Acceptance Criteria:
- [ ] requirements.txt uses an exact bcrypt version.
- [ ] Inline note documents the selected version rationale.
References:
- requirements.txt
Dependencies: None
Effort: S

### T-016: Align frontend lint tooling with declared dependencies
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Context:
- The frontend lint script references eslint without declaring it as a dev dependency.
Acceptance Criteria:
- [ ] npm run lint succeeds with declared devDependencies.
- [ ] package.json includes required lint dependencies or the lint script is removed if not used.
References:
- src/frontend/package.json
Dependencies: None
Effort: S

### T-017: Normalize legacy roadmap entries into the governance task format
Priority: P1
Type: CHORE
Owner: AGENT
Status: READY
Context:
- The roadmap pre-dates the governance-aligned task template and requires normalization for consistency.
Acceptance Criteria:
- [ ] Legacy roadmap entries are converted into T-### tasks following the required template.
- [ ] Completed or duplicate items are migrated to TODOCOMPLETED.md with completion dates.
- [ ] Top-priority tasks are clearly ranked for immediate execution.
References:
- TODO.md
- TODOCOMPLETED.md
- CODEAUDIT.md
Dependencies: None
Effort: L

### T-018: Build pipeline visualization UI (DEAL-3)
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Context:
- Pipeline deal management lacks the Kanban-style visualization and interactions called out in the implementation doc.
Acceptance Criteria:
- [ ] Kanban board view renders deals grouped by stage.
- [ ] Drag-and-drop stage transitions persist updates.
- [ ] Pipeline filtering and search are available in the UI.
- [ ] Deal cards display key metrics for quick scanning.
References:
- docs/PIPELINE_DEAL_MANAGEMENT.md
Dependencies: None
Effort: M

### T-019: Expand deal forecasting and analytics (DEAL-4)
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Context:
- Forecasting and analytics capabilities are partially implemented and need the remaining reporting features.
Acceptance Criteria:
- [ ] Win/loss tracking is captured and reportable.
- [ ] Pipeline performance reports are available for review.
- [ ] Revenue projection calculations are surfaced alongside existing weighted forecasting.
References:
- docs/PIPELINE_DEAL_MANAGEMENT.md
Dependencies: None
Effort: M

### T-020: Implement deal assignment automation (DEAL-5)
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Context:
- Automated routing and stage-driven assignment rules are not yet implemented for deals.
Acceptance Criteria:
- [ ] Round-robin deal assignment is available.
- [ ] Territory-based routing rules can be configured.
- [ ] Deal stage automation triggers assignment actions.
References:
- docs/PIPELINE_DEAL_MANAGEMENT.md
Dependencies: None
Effort: M

### T-021: Add deal splitting and rotting alert automation (DEAL-6)
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Context:
- Deal splitting and stale deal detection exist, but automated notifications and alerts are missing.
Acceptance Criteria:
- [ ] Automated reminders trigger for stale deals.
- [ ] Alerting logic covers deal splitting/rotting workflows beyond the existing model flags.
References:
- docs/PIPELINE_DEAL_MANAGEMENT.md
Dependencies: None
Effort: M

### T-022: Document environment variable reference
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Context:
- The reference index lists environment variables documentation as UNKNOWN.
Acceptance Criteria:
- [ ] docs/03-reference/environment-variables.md exists and documents required environment variables.
- [ ] docs/03-reference/README.md reflects the verified reference entry.
References:
- docs/03-reference/README.md
- .env.example
Dependencies: None
Effort: S

### T-023: Document management commands reference
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Context:
- The reference index lists management commands documentation as UNKNOWN.
Acceptance Criteria:
- [ ] docs/03-reference/management-commands.md exists and documents supported commands.
- [ ] docs/03-reference/README.md reflects the verified reference entry.
References:
- docs/03-reference/README.md
Dependencies: None
Effort: S

### T-024: Publish tier system reference or retire stale links
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Context:
- The reference index links to a tier system document that is missing.
Acceptance Criteria:
- [ ] docs/03-reference/tier-system.md is created with the current tier system details, or the index links are removed with rationale noted.
- [ ] docs/03-reference/README.md and docs/README.md reflect the verified state.
References:
- docs/03-reference/README.md
- docs/README.md
Dependencies: None
Effort: S

### SEC-6: Require webhook signature verification for DocuSign and Twilio
Priority: P1
Type: SECURITY
Owner: AGENT
Status: READY
Context:
- Webhook handlers allow unsigned requests when secrets are missing.
Acceptance Criteria:
- [ ] DocuSign webhooks reject requests when DOCUSIGN_WEBHOOK_SECRET is not configured.
- [ ] Twilio webhooks reject requests when TWILIO_AUTH_TOKEN is not configured.
- [ ] Environment validation reports missing secrets when webhooks are enabled.
References:
- src/modules/esignature/views.py
- src/modules/sms/webhooks.py
- src/config/env_validator.py
Dependencies: None
Effort: M

### SEC-7: Move auth tokens out of localStorage
Priority: P1
Type: SECURITY
Owner: AGENT
Status: READY
Context:
- localStorage tokens are vulnerable to XSS theft.
Acceptance Criteria:
- [ ] Access/refresh tokens are stored in HttpOnly, Secure, SameSite cookies.
- [ ] Frontend no longer reads/writes tokens from localStorage.
- [ ] Auth refresh and logout flows function with cookie-based tokens.
References:
- src/frontend/src/contexts/AuthContext.tsx
- src/frontend/src/api/client.ts
- src/modules/auth/
Dependencies: None
Effort: M

### LLM-1: Implement firm-scoped LLM client with safety controls
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Context:
- Safe GPT usage requires filters, metering, and auditability before rollout.
Acceptance Criteria:
- [ ] OpenAI/Azure client wrapper includes retries, timeouts, and zero-retention settings.
- [ ] Prompt/input redaction, output moderation, and audit logging enforced per request.
- [ ] Token usage metered per firm with admin-visible quotas.
References:
- src/modules (LLM integration points TBD)
Dependencies: None
Effort: M

### LLM-2: Add meeting prep background job with caching and fallbacks
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Context:
- Meeting prep automation depends on reliable asynchronous generation with cache safety.
Acceptance Criteria:
- [ ] Celery task generates summaries with cache keying by firm and meeting context hash.
- [ ] Results delivered asynchronously with webhook/notification hooks and deterministic fallback text.
- [ ] Admin controls exist for enabling/disabling LLM features per firm.
References:
- Celery worker configuration
- Meeting prep feature docs
Dependencies: LLM-1
Effort: M

## Backlog
<!-- Add future tasks here. -->

## Notes
- No automation is allowed to rewrite this file.
- Optional scripts may generate `TODO.generated.md` for convenience; it is never authoritative.
