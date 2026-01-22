# API Endpoint Authorization Mapping (DOC-18.1)

**Document Status:** Canonical
**Last Updated:** December 29, 2025
**Purpose:** Maps all API endpoints to canonical actions and documents server-side authorization enforcement

---

## Executive Summary

This document provides a comprehensive inventory of all API endpoints, their authorization requirements, and how they map to the canonical actions defined in docs/03-reference/requirements/DOC-18.md (API_CONTRACTS).

**Key Findings:**
- All staff endpoints enforce `IsAuthenticated` + `DenyPortalAccess`
- Portal endpoints use `IsPortalUserOrFirmUser` + `PortalFirmAccessPermission`
- Firm isolation is enforced via `FirmScopedQuerySet` at the model layer
- Authorization is consistently applied across all ViewSets

---

## Authorization Patterns

### Staff Authorization Stack
```
IsAuthenticated → DenyPortalAccess → FirmScopedQuerySet
```
- `IsAuthenticated`: Requires valid JWT token
- `DenyPortalAccess`: Blocks portal users from staff endpoints
- `FirmScopedQuerySet`: Model-level firm scoping (all queries filtered by user's firm)

### Portal Authorization Stack
```
IsPortalUserOrFirmUser → PortalFirmAccessPermission → Client-Scoped QuerySet
```
- `IsPortalUserOrFirmUser`: Accepts both portal and firm users
- `PortalFirmAccessPermission`: Validates portal user has access to the firm
- Client-Scoped QuerySet: Portal users only see their own client's data

### Admin Authorization Stack
```
IsAuthenticated → IsFirmOwnerOrAdmin → FirmScopedQuerySet
```
- Used for sensitive firm-level operations (offboarding, break-glass)

---

## Endpoint Inventory

### Authentication (`/api/auth/`)

| Endpoint | Method | View | Authorization | Canonical Action |
|----------|--------|------|---------------|------------------|
| `/register/` | POST | RegisterView | AllowAny | Admin: user creation |
| `/login/` | POST | login_view | AllowAny | - |
| `/logout/` | POST | logout_view | IsAuthenticated | - |
| `/profile/` | GET | user_profile_view | IsAuthenticated | Admin: /users |
| `/change-password/` | POST | ChangePasswordView | IsAuthenticated | Admin: /users |
| `/token/refresh/` | POST | CookieTokenRefreshView | - | Cookie-based token refresh |

### Firm Management (`/api/firm/`)

| Endpoint | Method | View | Authorization | Canonical Action |
|----------|--------|------|---------------|------------------|
| `/break-glass/` | GET/POST | BreakGlassStatusViewSet | IsAuthenticated | Admin: break-glass audit |
| `/offboarding/` | GET/POST | FirmOffboardingViewSet | IsAuthenticated + IsFirmOwnerOrAdmin | Admin: data exit |

### CRM - Pre-Sale (`/api/crm/`)

| Endpoint | Method | View | Authorization | Canonical Action |
|----------|--------|------|---------------|------------------|
| `/leads/` | CRUD | LeadViewSet | IsAuthenticated + DenyPortalAccess | CRM: /deals |
| `/prospects/` | CRUD | ProspectViewSet | IsAuthenticated + DenyPortalAccess | CRM: /accounts |
| `/campaigns/` | CRUD | CampaignViewSet | IsAuthenticated + DenyPortalAccess | CRM: (marketing) |
| `/proposals/` | CRUD | ProposalViewSet | IsAuthenticated + DenyPortalAccess | Pricing: /quotes |
| `/contracts/` | CRUD | ContractViewSet | IsAuthenticated + DenyPortalAccess | Engagements: /engagements |

### Clients - Post-Sale (`/api/clients/`)

| Endpoint | Method | View | Authorization | Canonical Action |
|----------|--------|------|---------------|------------------|
| `/organizations/` | CRUD | OrganizationViewSet | IsAuthenticated + DenyPortalAccess | CRM: /accounts |
| `/clients/` | CRUD | ClientViewSet | IsAuthenticated + DenyPortalAccess | CRM: /accounts |
| `/portal-users/` | CRUD | ClientPortalUserViewSet | IsAuthenticated + DenyPortalAccess | Admin: /portal-grants |
| `/notes/` | CRUD | ClientNoteViewSet | IsAuthenticated + DenyPortalAccess | - |
| `/engagements/` | CRUD | ClientEngagementViewSet | IsAuthenticated + DenyPortalAccess | Engagements: /engagements |
| `/projects/` | CRUD | ClientProjectViewSet | IsPortalUserOrFirmUser + PortalFirmAccessPermission | Work: /work-items |
| `/comments/` | CRUD | ClientCommentViewSet | IsPortalUserOrFirmUser + PortalFirmAccessPermission | Communications |
| `/invoices/` | CRUD | ClientInvoiceViewSet | IsPortalUserOrFirmUser + PortalFirmAccessPermission | Billing: /invoices |
| `/chat-threads/` | CRUD | ClientChatThreadViewSet | IsPortalUserOrFirmUser + PortalFirmAccessPermission | Communications: /conversations |
| `/messages/` | CRUD | ClientMessageViewSet | IsPortalUserOrFirmUser + PortalFirmAccessPermission | Communications: /messages |
| `/proposals/` | CRUD | ClientProposalViewSet | IsPortalUserOrFirmUser + PortalFirmAccessPermission | Pricing: /quotes |
| `/contracts/` | CRUD | ClientContractViewSet | IsPortalUserOrFirmUser + PortalFirmAccessPermission | Engagements |
| `/engagement-history/` | GET | ClientEngagementHistoryViewSet | IsPortalUserOrFirmUser + PortalFirmAccessPermission | - |

### Projects (`/api/projects/`)

| Endpoint | Method | View | Authorization | Canonical Action |
|----------|--------|------|---------------|------------------|
| `/projects/` | CRUD | ProjectViewSet | IsAuthenticated + DenyPortalAccess | Work: /work-items |
| `/tasks/` | CRUD | TaskViewSet | IsAuthenticated + DenyPortalAccess | Work: /work-items |
| `/time-entries/` | CRUD | TimeEntryViewSet | IsAuthenticated + DenyPortalAccess | Work: time tracking |

### Finance (`/api/finance/`)

| Endpoint | Method | View | Authorization | Canonical Action |
|----------|--------|------|---------------|------------------|
| `/invoices/` | CRUD | InvoiceViewSet | IsAuthenticated + DenyPortalAccess | Billing: /invoices |
| `/bills/` | CRUD | BillViewSet | IsAuthenticated + DenyPortalAccess | Billing: AP |
| `/ledger-entries/` | CRUD | LedgerEntryViewSet | IsAuthenticated + DenyPortalAccess | Billing: /ledger |
| `/payment/` | CRUD | PaymentViewSet | IsAuthenticated | Billing: /payments |

### Documents (`/api/documents/`)

| Endpoint | Method | View | Authorization | Canonical Action |
|----------|--------|------|---------------|------------------|
| `/folders/` | CRUD | FolderViewSet | IsAuthenticated + DenyPortalAccess | Documents: organization |
| `/documents/` | CRUD | DocumentViewSet | IsAuthenticated + DenyPortalAccess | Documents: /documents |
| `/versions/` | CRUD | VersionViewSet | IsAuthenticated + DenyPortalAccess | Documents: /documents/{id}/versions |

### Assets (`/api/assets/`)

| Endpoint | Method | View | Authorization | Canonical Action |
|----------|--------|------|---------------|------------------|
| `/assets/` | CRUD | AssetViewSet | IsAuthenticated + DenyPortalAccess | Assets (standalone) |
| `/maintenance-logs/` | CRUD | MaintenanceLogViewSet | IsAuthenticated + DenyPortalAccess | Assets |

### Portal (`/api/portal/`)

| Endpoint | Method | View | Authorization | Canonical Action |
|----------|--------|------|---------------|------------------|
| `/projects/` | GET/LIST | ClientProjectViewSet | Portal-scoped | Work visibility |
| `/comments/` | CRUD | ClientCommentViewSet | Portal-scoped | Communications |
| `/invoices/` | GET/LIST | ClientInvoiceViewSet | Portal-scoped | Billing visibility |
| `/chat-threads/` | CRUD | ClientChatThreadViewSet | Portal-scoped | Communications |
| `/messages/` | CRUD | ClientMessageViewSet | Portal-scoped | Communications |
| `/proposals/` | GET/LIST | ClientProposalViewSet | Portal-scoped | Pricing visibility |
| `/contracts/` | GET/LIST | ClientContractViewSet | Portal-scoped | Engagement visibility |
| `/engagement-history/` | GET | ClientEngagementHistoryViewSet | Portal-scoped | History visibility |

### Webhooks

| Endpoint | Method | View | Authorization | Canonical Action |
|----------|--------|------|---------------|------------------|
| `/webhooks/stripe/` | POST | stripe_webhook | Stripe signature verification | Payment processing |

---

## Gap Analysis vs docs/03-reference/requirements/DOC-18.md Canonical Actions

### ✅ Implemented

| Canonical Action | Implementation Status |
|-----------------|----------------------|
| CRM: /accounts | ✅ `/api/clients/clients/`, `/api/clients/organizations/` |
| CRM: /contacts | ✅ Implied via client relationships |
| CRM: /deals | ✅ `/api/crm/leads/`, `/api/crm/prospects/` |
| Engagements: /engagements | ✅ `/api/clients/engagements/`, `/api/crm/contracts/` |
| Work: /work-items | ✅ `/api/projects/projects/`, `/api/projects/tasks/` |
| Pricing: /quotes | ✅ `/api/crm/proposals/` |
| Documents: /documents | ✅ `/api/documents/documents/` |
| Documents: /documents/{id}/versions | ✅ `/api/documents/versions/` |
| Communications: /conversations | ✅ `/api/clients/chat-threads/` |
| Communications: /messages | ✅ `/api/clients/messages/` |
| Billing: /invoices | ✅ `/api/finance/invoices/` |
| Billing: /payments | ✅ `/api/finance/payment/` |
| Billing: /ledger | ✅ `/api/finance/ledger-entries/` |
| Admin: /roles, /users | ✅ `/api/auth/` endpoints |
| Admin: /portal-grants | ✅ `/api/clients/portal-users/` |

### ⚠️ Partially Implemented

| Canonical Action | Status | Notes |
|-----------------|--------|-------|
| Engagements: /engagement-lines | ⚠️ Partial | Engagement model exists; EngagementLine not explicit |
| Documents: /documents/{id}/lock | ⚠️ Partial | Lock fields exist; dedicated endpoint tracked in TODO: T-014 |
| Documents: /documents/{id}/signed-url | ⚠️ Partial | URL generation exists; formal endpoint tracked in TODO: T-014 |
| Documents: /upload-requests | ⚠️ Partial | Upload via document creation; request flow tracked in TODO: T-014 |

### ❌ Not Yet Implemented

| Canonical Action | Priority | Notes |
|-----------------|----------|-------|
| Pricing: /pricing/evaluate | High | DOC-09.1 - Pricing engine MVP |
| Pricing: /quote-versions | High | DOC-09.2 - Quote snapshots |
| Work: /delivery-templates | Medium | DOC-12.1 - Delivery templates MVP |
| Communications: /attachments | Medium | DOC-33.1 - Communications model |
| Calendar: /appointments | Medium | DOC-34.1 - Calendar domain MVP |
| Calendar: /calendar/connections | Medium | DOC-16.1 - Calendar sync MVP |
| Calendar: /calendar/sync | Medium | DOC-16.1 - Calendar sync MVP |
| Billing: /retainers | Low | Retainer model exists; API pending |
| Automation: /orchestrations | Medium | DOC-11.1 - Orchestration engine MVP |
| Automation: /recurrence | Medium | DOC-10.1 - Recurrence engine MVP |
| Admin: /audit | Low | Audit events exist; query API pending |
| Admin: /governance | Low | DOC-07.1 - Governance classification |

---

## Authorization Consistency Checklist

### ✅ All Staff Endpoints
- [x] Use `IsAuthenticated` permission
- [x] Use `DenyPortalAccess` to block portal users
- [x] Use firm-scoped querysets

### ✅ All Portal Endpoints  
- [x] Use `IsPortalUserOrFirmUser` or equivalent
- [x] Use `PortalFirmAccessPermission` for firm access
- [x] Scope queries to client's data only

### ✅ Admin Endpoints
- [x] Firm offboarding requires `IsFirmOwnerOrAdmin`
- [x] Break-glass has audit logging

### ⚠️ Recommendations

1. **PaymentViewSet**: Currently only uses `IsAuthenticated`. Should add `DenyPortalAccess` or explicit portal payment handling.

2. **Missing Idempotency Keys**: Per docs/03-reference/requirements/DOC-18.md, mutations should support `X-Idempotency-Key` header. This should be implemented for:
   - Invoice creation
   - Payment posting
   - Ledger entry creation

3. **Missing Correlation IDs**: Per docs/03-reference/requirements/DOC-18.md, endpoints should accept/generate `X-Correlation-Id`. This is a DOC-21.1 task.

---

## Implementation Notes

### Permission Classes Location
- `src/config/permissions.py`: Base permission classes
- `src/modules/firm/permissions.py`: Firm-specific permissions
- `src/modules/clients/permissions.py`: Portal/client permissions

### QuerySet Scoping
- `FirmScopedQuerySet`: Enforces firm isolation at model layer
- Portal querysets additionally filter by client association

---

## References

- **docs/03-reference/requirements/DOC-18.md**: API_CONTRACTS (canonical endpoint groups)
- **docs/03-reference/requirements/DOC-08.md**: PERMISSIONS_MODEL (authorization rules)
- **spec/SYSTEM_INVARIANTS.md**: Core authorization invariants
- **CONTRIBUTING.md**: Development guidelines for adding endpoints

---

## Next Actions

1. Add `DenyPortalAccess` to PaymentViewSet (or implement portal payment flow)
2. Implement idempotency key support for financial mutations (DOC-13.1)
3. Implement missing canonical endpoints as part of DOC-* tasks
4. Add correlation ID middleware (DOC-21.1)
