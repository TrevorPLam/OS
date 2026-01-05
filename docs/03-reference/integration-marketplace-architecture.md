# Integration Marketplace Architecture

**Status:** Complete (Architecture Design)  
**Last Updated:** January 5, 2026  
**Owner:** Integrations Team  
**Canonical Status:** Supporting  
**Related Tasks:** MARKET-1 (Design integration marketplace architecture), MARKET-2 through MARKET-5  
**Dependencies:** OAuth apps registry, billing/entitlement checks, UI component library

## Purpose

Define the end-to-end architecture for a secure integration marketplace that lets firms discover, install, and manage third-party integrations while preserving tenant isolation and auditability.

## Core Requirements

1. **Safe-by-Default Installations** — Installs require explicit admin approval and firm-scoped credentials.  
2. **Catalog & Search** — Filter by category, capability, and permission scope; support featured and recommended tiles.  
3. **Entitlements** — Feature flags + billing checks gate premium integrations.  
4. **Auditability** — Every install/update/uninstall is logged with actor, timestamp, and diff of scopes.  
5. **Supportability** — Clear health/status indicators and error surfacing in the admin UI.

## System Components

- **Integration Registry (Backend):** Django models under `src/modules/integrations/` (new) or `src/modules/core/` to store integration definitions, scopes, OAuth metadata, pricing tier, and availability.  
- **Marketplace API:** REST endpoints under `/api/v1/marketplace/` for listing, searching, installing, uninstalling, and retrieving status. Uses DRF serializers with firm scoping and permission classes enforcing admin-only actions.  
- **Installation Flow:**  
  - OAuth-based integrations redirect to `/api/v1/marketplace/install/<integration_slug>/callback` with state + PKCE verification.  
  - API-key integrations collect keys via secure secrets storage and validate with a lightweight connectivity check.  
  - Webhooks/queues configured via the integration record (e.g., Slack signing secret, Salesforce webhook URLs).  
- **Configuration UI:** React screens under `src/frontend/` for catalog, detail pages, and per-install settings. Uses reusable components for scope display, permissions, and status badges.  
- **Observability:** Each integration install tracks health (last sync, last error, quota usage) and surfaces alerts to admins.

## Data Model (Conceptual)

- `IntegrationProvider`: slug, display name, categories, docs/support links, required scopes, auth type (OAuth2/API key/none), available plans.  
- `IntegrationInstallation`: firm, provider, status (installed, errored, disconnected), credentials reference, installed_by, installed_at, configuration payload, scopes granted, webhooks configured.  
- `IntegrationEvent`: audit log entry for lifecycle events and configuration changes.

## Security & Governance

- **Tenant Isolation:** Installation records always include `firm_id`; credentials are stored per firm using the platform secret store.  
- **Scope Minimization:** Display requested scopes before install; store granted scopes and enforce at runtime.  
- **Rotation & Revocation:** Support token refresh, manual disconnect, and automated revocation on repeated failures.  
- **Rate Limits:** Apply per-provider rate limits; backoff + DLQ for webhook ingests.  
- **Compliance:** Log data flows for PII and ensure consent flags are honored before syncing contact data.

## UX Flow (Happy Path)

1. Admin browses catalog → opens provider detail page.  
2. Admin reviews scopes/plan → clicks Install.  
3. For OAuth providers, user is redirected to consent; on success, the callback stores credentials and runs a connectivity test.  
4. Marketplace UI shows install success, health status, and quick actions (configure sync, view logs, uninstall).  
5. Health cards and notifications alert when syncs fail or tokens expire.

## Operational Considerations

- **Migration Strategy:** Introduce registry models via migrations and seed initial providers (Slack, Salesforce, Zoom, etc.).  
- **Rollout:** Start with internal beta firms; gate features behind `INTEGRATION_MARKETPLACE_ENABLED` flag.  
- **Monitoring:** Metrics on install conversions, failure reasons, and sync health; alerts on elevated error rates per provider.  
- **Support Runbooks:** Add runbooks for OAuth callback failures, sync failures, and permission revocations.

## Acceptance Criteria (MARKET-1)

- Marketplace architecture documented with data model, API surface, and UI flows.  
- Security, audit, and tenant-isolation controls defined for installation lifecycle.  
- Operational rollout plan captured to inform implementation tasks.
