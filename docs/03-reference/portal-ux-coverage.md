# Portal & Mobile UX Coverage (T-124)

## Purpose

Document the current portal and mobile UX coverage, map frontend routes to backend endpoints, and capture gaps that need follow-up work.

## Scope & Evidence

**Frontend sources reviewed**
- `src/frontend/src/App.tsx` (portal route inventory)
- `src/frontend/src/pages/ClientPortal.tsx` (portal UI tabs and data loading)
- `src/frontend/src/api/clientPortal.ts` (portal API usage)
- `src/frontend/src/api/documents.ts` (document download/listing used in portal)
- `src/frontend/src/pages/ClientPortal.css` (responsive behavior)

**Backend sources reviewed**
- `src/api/portal/urls.py` (portal API surface)
- `docs/CLIENT_PORTAL_IA_IMPLEMENTATION.md` (portal IA expectations)

## Portal UI Route Inventory (Frontend)

| Route | UI Entry | Primary UI Areas | Backend Calls Used | Coverage Status |
| --- | --- | --- | --- | --- |
| `/client-portal` | `ClientPortal` page | Work, Documents, Invoices, Messages, Engagement | `clientPortalApi` (`/api/portal/*`), `portalDocumentsApi` (`/api/portal/documents`, `/api/portal/folders`) | **Aligned** (portal endpoints in use) |

### Portal UI Coverage Notes

- The portal UI is a single route with tabbed sections (work/projects, documents, invoices, messages, engagement). It now relies on `/api/portal/*` endpoints for projects, billing, messaging, comments, and documents, ensuring portal users consume the allowlisted API surface from `src/api/portal/urls.py`.
- The portal UI currently does **not** expose appointments booking, profile management, or account switching despite corresponding backend portal endpoints.

## Portal API Surface Inventory (Backend)

| Portal Endpoint (Router) | Purpose | UI Coverage |
| --- | --- | --- |
| `/api/portal/home/` | Portal home dashboard | **Missing** (not surfaced in UI) |
| `/api/portal/chat-threads/` | Portal messaging threads | **Covered** |
| `/api/portal/messages/` | Portal messaging | **Covered** |
| `/api/portal/documents/` | Portal documents list | **Covered** |
| `/api/portal/folders/` | Portal document folders | **Covered** |
| `/api/portal/appointments/` | Portal appointments | **Missing** |
| `/api/portal/invoices/` | Portal invoices | **Covered** |
| `/api/portal/projects/` | Portal projects | **Covered** |
| `/api/portal/contracts/` | Portal contracts | **Covered** |
| `/api/portal/proposals/` | Portal proposals | **Covered** |
| `/api/portal/engagement-history/` | Portal engagement history | **Covered** |
| `/api/portal/profile/` | Portal profile | **Missing** |
| `/api/portal/accounts/` | Portal account switcher | **Missing** |
| `/api/portal/comments/` | Portal task comments (legacy) | **Covered** |

## Mobile Coverage Inventory

- **Dedicated mobile routes:** None found in `src/frontend/src/App.tsx`.
- **Responsive behavior:** `ClientPortal.css` includes a mobile breakpoint at 768px with layout adjustments for portal stats, tabs, and document cards.
- **Other portal/mobile coverage:** **UNKNOWN** beyond the portal page without deeper page-by-page responsive audits.

## Gaps & Follow-up Tasks

1. **Missing portal flows:** UI lacks appointments booking, portal profile management, and account switching despite backend support.

Follow-up tasks added in `TODO.md`:
- **T-145**: Align client portal frontend to `/api/portal/*` endpoints (client portal API migration).
- **T-146**: Add portal appointments booking UI to the Client Portal.
- **T-147**: Add portal profile and account switcher UI in Client Portal.

## Notes

This audit is scoped to portal UX coverage and mobile responsiveness signals in the portal UI. A deeper mobile audit of the staff-facing UI would require a separate task once a mobile UX strategy is confirmed.
