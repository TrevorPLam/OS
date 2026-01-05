# Audit Review Dashboard Wireframes

**Status:** Complete (Wireframes & UX Notes)  
**Last Updated:** January 5, 2026  
**Owner:** Compliance & Platform UX  
**Canonical Status:** Supporting  
**Related Tasks:** AUDIT-1 (Design audit review dashboard wireframes), AUDIT-2 through AUDIT-4  
**Dependencies:** Audit log backend (src/modules/core/), RBAC policies, chart components in `src/frontend/`

## Objectives

Provide a clear UX blueprint for the Audit Review dashboard so engineers and designers can implement AUDIT-2 through AUDIT-4 without ambiguity while preserving tenant isolation and security controls.

## Layout Overview

1. **Header Bar** — Title, firm selector (scoped to current firm), date range picker, and export buttons (CSV/JSON).  
2. **Summary Tiles (Top Row)** — Cards for: Total Events, Critical Alerts (P1), Permission Changes, and Data Exports. Each card links to a filtered table view.  
3. **Filters Panel (Left Sidebar)** — Event type, actor, resource type, permission changes only, result (success/failure), and correlation ID search.  
4. **Main Content (Right Panel)**  
   - **Activity Timeline (upper section):** Vertical timeline with icons by severity, showing timestamp, actor, action, target, and inline JSON diff for permission changes.  
   - **Event Table (lower section):** Paginated grid with sortable columns (timestamp, actor, action, target, IP, status, correlation ID). Row click opens a drawer with full payload and linked runbook.  
5. **Inspector Drawer** — Right-side drawer with tabs: Summary, Raw Event, Related Events (same correlation ID), and Runbook links.

## Interaction Flows

- **Filtering:** Filters apply to both timeline and table; chip-based filters show active selections with one-click clear.  
- **Saved Views:** Admins can save filter presets (e.g., “Permission Changes Last 24h”). Presets are firm-scoped.  
- **Export:** Exports respect filters and include checksum + timestamp in filename for auditability.  
- **Deep Links:** Each event row has a permalink (`/audit/<event_id>`) for investigations.

## Accessibility & Security

- WCAG AA color contrast, keyboard navigable filters, and ARIA labels for icons.  
- Permission checks: only admins/compliance roles can access the dashboard; PII fields are redacted in previews.  
- No client-side caching of payloads in localStorage; rely on secure API calls with short-lived tokens.

## Metrics & Observability

- Frontend telemetry: filter latency, export success/failure, and top filter combinations.  
- Backend metrics: query latency, result counts, and permission-deny rates.  
- Alerting: surface warning banner if backend latency > 2s or if event ingestion lags beyond SLA.

## Acceptance Criteria (AUDIT-1)

- Wireframe-level UX captured with layout, interactions, and accessibility guidance.  
- Export, saved views, and deep-link behaviors defined.  
- Security/privacy constraints documented for PII and role gating.
