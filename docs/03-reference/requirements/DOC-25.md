# Staff App Information Architecture (STAFF_APP_INFORMATION_ARCHITECTURE)

Defines navigation map and module cross-links for the firm-side UI.
Explanatory, but should align with permissions and domain boundaries.

Primary nav (left)
1. Dashboard
2. Communications
3. Calendar
4. CRM
5. Engagements
6. Work
7. Documents
8. Billing
9. Automation
10. Reporting
11. Knowledge
12. Admin

CRM subnav (Pipeline is inside CRM)
- Accounts
- Contacts
- Deals (Pipeline)
- Activities
- Notes
- (optional) Sequences
- Lists/Segments (dynamic filters: lead status/score, pipeline stage, tags)
- Settings (admin-gated: stages, required fields, custom fields)

Shared “Client 360” pattern (reachable from anywhere)
Tabs:
- Overview
- Contacts
- Deals
- Engagements
- Work
- Documents
- Messages
- Calendar
- Billing
- Activity (Audit tab for privileged roles)

Key cross-links
- Deal → Create Engagement (draft) → Start Quote → Activate on acceptance
- Any object → Open related conversation thread
- Any object → Request documents (creates upload request)
- Any object → Book appointment (context-linked)

## Lists/Segments quick reference

Segments are now available for staff to build reusable targeting lists:
- Firm-scoped filters cover leads, prospects, and clients via `entity_types`.
- Criteria supported today: lead statuses, lead score ranges, prospect pipeline stages, client statuses, and tag slugs.
- Segment.refresh_membership() recalculates member counts and timestamps, using firm isolation on every query.

Admin areas (restricted)
- Users & Roles
- Portal access policies
- Governance (retention, legal hold, exports)
- Integrations (email/calendar)
- Audit viewer
- Templates (delivery/doc)
- System settings (timezone, branding, notifications)

---

