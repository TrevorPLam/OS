# Role Based Views (ROLE_BASED_VIEWS)

Defines which roles see which modules and least-privilege defaults.

Staff roles (example)
- FirmAdmin: everything, including Admin + Audit + Integrations + Governance
- Partner/Owner: most operational; limited admin depending on policy
- Manager: CRM/Engagements/Work/Documents/Comms/Calendar; limited billing
- Staff: Work/Documents/Comms/Calendar; limited CRM; no admin
- Billing: Billing + invoice/pay/retainer actions; limited work edits
- ReadOnly: read-only across allowed objects

Module visibility (default)
- Dashboard: all staff
- Communications: all staff
- Calendar: all staff
- CRM: Manager+ (Staff may have limited account read)
- Engagements: all staff (scoped by assignment policy)
- Work: all staff
- Documents: all staff (scoped by permissions)
- Billing: Billing+ (others read-only invoices if allowed)
- Automation: Admin+ (Managers may see limited status views)
- Reporting: Manager+ (Admin sees all)
- Knowledge: all staff (some sections restricted)
- Admin: Admin only

Portal scopes map to portal nav:
- Messages requires portal:message:*
- Documents requires portal:document:*
- Appointments requires portal:appointment:*
- Billing requires portal:invoice:* (and portal:invoice:pay for payment)

---
