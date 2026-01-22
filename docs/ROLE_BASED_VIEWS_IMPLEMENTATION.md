# Role-Based Views Implementation (DOC-27.1)

**Status:** ✅ Complete
**Date:** December 30, 2025
**Requirements:** docs/03-reference/requirements/DOC-27.md - ROLE_BASED_VIEWS

---

## Overview

This document details the implementation of role-based module visibility and least privilege defaults per docs/03-reference/requirements/DOC-27.md. The system defines 6 staff roles with granular permissions and module access controls.

---

## Staff Roles

### Role Definitions (DOC-27.1)

| Role | Code | Description | Module Access |
|------|------|-------------|---------------|
| **Firm Admin** | `firm_admin` | Everything, including Admin + Audit + Integrations + Governance | All modules |
| **Partner/Owner** | `partner` | Most operational; limited admin depending on policy | All except Admin |
| **Manager** | `manager` | CRM/Engagements/Work/Documents/Comms/Calendar; limited billing | Dashboard, Comms, Calendar, CRM (full), Engagements, Work, Documents, Billing (read), Automation (read), Reporting, Knowledge |
| **Staff** | `staff` | Work/Documents/Comms/Calendar; limited CRM; no admin | Dashboard, Comms, Calendar, CRM (read), Engagements, Work, Documents, Knowledge |
| **Billing** | `billing` | Billing + invoice/pay/retainer actions; limited work edits | Dashboard, Comms, Calendar, Work (limited), Documents, Billing (full), Knowledge |
| **Read-Only** | `readonly` | Read-only across allowed objects | All modules (read-only) |

### Legacy Role Mapping

For backward compatibility, legacy roles are automatically mapped:

| Legacy Role | New Role |
|-------------|----------|
| `owner` | `firm_admin` |
| `admin` | `firm_admin` |
| `contractor` | `staff` |

---

## Permission Defaults

Each role has automatic permission defaults set in `FirmMembership.save()`:

### Firm Admin
```python
can_manage_users = True      # Can invite/remove users
can_manage_clients = True    # Can create/delete clients
can_manage_billing = True    # Can view/modify billing
can_manage_settings = True   # Can modify firm settings
can_view_reports = True      # Can access analytics/reports
```

### Partner/Owner
```python
can_manage_users = False     # Policy-dependent
can_manage_clients = True
can_manage_billing = True
can_manage_settings = False  # Limited admin
can_view_reports = True
```

### Manager
```python
can_manage_users = False
can_manage_clients = True
can_manage_billing = False   # Limited: can view, not manage
can_manage_settings = False
can_view_reports = True      # Manager+ per docs/03-reference/requirements/DOC-27.md
```

### Staff
```python
can_manage_users = False
can_manage_clients = False
can_manage_billing = False
can_manage_settings = False
can_view_reports = False
```

### Billing
```python
can_manage_users = False
can_manage_clients = False
can_manage_billing = True
can_manage_settings = False
can_view_reports = False     # Limited to billing reports
```

### Read-Only
```python
can_manage_users = False
can_manage_clients = False
can_manage_billing = False
can_manage_settings = False
can_view_reports = False
# Note: All operations restricted to safe methods (GET, HEAD, OPTIONS)
```

---

## Module Visibility Rules

Per docs/03-reference/requirements/DOC-27.md, each module has specific visibility rules:

### 1. Dashboard
**Visibility:** All staff
**Permission Class:** `CanAccessDashboard`
**Rule:** Any authenticated firm user

### 2. Communications
**Visibility:** All staff
**Permission Class:** `CanAccessCommunications`
**Rule:** Any authenticated firm user

### 3. Calendar
**Visibility:** All staff
**Permission Class:** `CanAccessCalendar`
**Rule:** Any authenticated firm user

### 4. CRM
**Visibility:** Manager+ (Staff may have limited account read)
**Permission Class:** `CanAccessCRM`
**Rules:**
- Manager+ : Full read/write access
- Staff: Read-only access to accounts they're assigned to
- Billing/ReadOnly: No access

**Implementation:**
```python
# Manager+ can do everything
if role in ("manager", "partner", "firm_admin"):
    return True

# Staff can read only
if role == "staff" and request.method in ("GET", "HEAD", "OPTIONS"):
    return True
```

### 5. Engagements
**Visibility:** All staff (scoped by assignment policy)
**Permission Class:** `CanAccessEngagements`
**Rule:** Any authenticated firm user
**Note:** Object-level scoping limits visibility to assigned engagements

### 6. Work
**Visibility:** All staff
**Permission Class:** `CanAccessWork`
**Rule:** Any authenticated firm user

### 7. Documents
**Visibility:** All staff (scoped by permissions)
**Permission Class:** `CanAccessDocuments`
**Rule:** Any authenticated firm user
**Note:** Document visibility further restricted by document-level permissions

### 8. Billing
**Visibility:** Billing+ (others read-only invoices if allowed)
**Permission Classes:**
- `CanAccessBilling` - View billing
- `CanManageBilling` - Modify billing

**Rules:**
- Billing/Partner/Admin: Full read/write access
- Manager: Read-only access to invoices
- Others: No access

**Implementation:**
```python
# Full access
if role in ("billing", "partner", "firm_admin"):
    return True

# Manager can read invoices (limited billing per docs/03-reference/requirements/DOC-27.md)
if role == "manager" and request.method in ("GET", "HEAD", "OPTIONS"):
    return True
```

### 9. Automation
**Visibility:** Admin+ (Managers may see limited status views)
**Permission Class:** `CanAccessAutomation`
**Rules:**
- Admin: Full access
- Manager: Read-only status views
- Others: No access

### 10. Reporting
**Visibility:** Manager+ (Admin sees all)
**Permission Class:** `CanAccessReporting`
**Rule:** Manager, Partner, or Admin only

### 11. Knowledge
**Visibility:** All staff (some sections restricted)
**Permission Class:** `CanAccessKnowledge`
**Rule:** Any authenticated firm user
**Note:** Section-level restrictions can be applied within knowledge module

### 12. Admin
**Visibility:** Admin only
**Permission Class:** `CanAccessAdmin`
**Rule:** `firm_admin` role only

---

## Portal Scopes (DOC-27.1)

Portal scopes map to portal navigation per docs/03-reference/requirements/DOC-27.md. Each scope is validated via `ClientPortalUser` permission flags.

### Scope Definitions

| Scope | Portal Nav | Permission Flag | Description |
|-------|------------|-----------------|-------------|
| `portal:message:*` | Messages | `can_message_staff` | Send/receive messages |
| `portal:document:*` | Documents | `can_view_documents` | View/upload documents |
| `portal:appointment:*` | Appointments | `can_book_appointments` | Book/view appointments |
| `portal:invoice:*` | Billing | `can_view_invoices` | View invoices |
| `portal:invoice:pay` | Billing (Pay) | `can_view_invoices` | Make payments |

### Permission Classes

**Base Class:**
```python
class HasPortalScope(BasePermission):
    required_scope = None  # Override in subclasses

    def has_permission(self, request, view):
        portal_user = ClientPortalUser.objects.get(user=request.user)
        # Map scope to permission flags
        return check_scope(portal_user, self.required_scope)
```

**Scope-Specific Classes:**
- `HasMessageScope` - `portal:message:*`
- `HasDocumentScope` - `portal:document:*`
- `HasAppointmentScope` - `portal:appointment:*`
- `HasInvoiceScope` - `portal:invoice:*`
- `HasInvoicePayScope` - `portal:invoice:pay`

### Usage in Portal ViewSets

```python
class PortalDocumentViewSet(...):
    permission_classes = [IsAuthenticated, IsPortalUser, HasDocumentScope]
```

---

## Implementation Files

### Models
- `src/modules/firm/models.py` - `FirmMembership` with expanded roles (lines 297-417)
- `src/modules/clients/models.py` - `ClientPortalUser` with scope flags

### Permissions
- `src/modules/auth/role_permissions.py` - All role-based permission classes (291 lines)
  - Role utilities (`get_user_role`, `is_admin`, `is_manager_or_above`, etc.)
  - Module permission classes (12 modules)
  - Portal scope permission classes (5 scopes)
  - Read-only role enforcement

### Migrations
- `src/modules/firm/migrations/0011_role_based_views.py` - Role migration

---

## Usage Examples

### 1. Protecting a ViewSet with Module Permissions

```python
from modules.auth.role_permissions import CanAccessCRM

class LeadViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanAccessCRM]
    # Manager+ can read/write, Staff can read-only
```

### 2. Checking Role Programmatically

```python
from modules.auth.role_permissions import get_user_role, is_manager_or_above

role = get_user_role(request.user, request)
if role == "firm_admin":
    # Admin-only logic
    pass

if is_manager_or_above(request.user, request):
    # Manager+ logic
    pass
```

### 3. Conditional Logic Based on Role

```python
def get_queryset(self):
    queryset = super().get_queryset()
    role = get_user_role(self.request.user, self.request)

    if role == "staff":
        # Staff see only assigned accounts
        queryset = queryset.filter(assigned_to=self.request.user)
    elif role in ("manager", "partner", "firm_admin"):
        # Manager+ see all accounts
        pass

    return queryset
```

### 4. Enforcing Read-Only Role

```python
from modules.auth.role_permissions import IsReadOnlyRole

class SensitiveDataViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsReadOnlyRole]
    # Users with readonly role can only GET
```

### 5. Portal Scope Validation

```python
from modules.auth.role_permissions import HasAppointmentScope

class PortalAppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsPortalUser, HasAppointmentScope]
    # Portal users must have can_book_appointments flag
```

---

## Role Assignment Workflow

### 1. Create FirmMembership

When inviting a user to a firm:

```python
membership = FirmMembership.objects.create(
    firm=firm,
    user=user,
    role="manager",  # Choose appropriate role
    invited_by=request.user,
)
# Permissions automatically set in save() based on role
```

### 2. Update Role

When changing a user's role:

```python
membership.role = "partner"
membership.save()  # Permissions automatically updated
```

### 3. Grant/Revoke Permissions

For fine-grained control beyond role defaults:

```python
# Override default: allow partner to manage users
membership.can_manage_users = True
membership.save(update_fields=["can_manage_users"])
```

---

## Compliance Matrix

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **Staff Roles** |  |  |
| FirmAdmin role | ✅ Complete | `FirmMembership.ROLE_CHOICES` |
| Partner/Owner role | ✅ Complete | `FirmMembership.ROLE_CHOICES` |
| Manager role | ✅ Complete | `FirmMembership.ROLE_CHOICES` |
| Staff role | ✅ Complete | `FirmMembership.ROLE_CHOICES` |
| Billing role | ✅ Complete | `FirmMembership.ROLE_CHOICES` |
| ReadOnly role | ✅ Complete | `FirmMembership.ROLE_CHOICES` |
| **Permission Defaults** |  |  |
| Auto-set on role change | ✅ Complete | `FirmMembership.save()` |
| Least privilege defaults | ✅ Complete | Per docs/03-reference/requirements/DOC-27.md specification |
| Legacy role mapping | ✅ Complete | owner/admin→firm_admin, contractor→staff |
| **Module Visibility** |  |  |
| Dashboard (all staff) | ✅ Complete | `CanAccessDashboard` |
| Communications (all staff) | ✅ Complete | `CanAccessCommunications` |
| Calendar (all staff) | ✅ Complete | `CanAccessCalendar` |
| CRM (Manager+) | ✅ Complete | `CanAccessCRM` with staff read-only |
| Engagements (all staff) | ✅ Complete | `CanAccessEngagements` |
| Work (all staff) | ✅ Complete | `CanAccessWork` |
| Documents (all staff) | ✅ Complete | `CanAccessDocuments` |
| Billing (Billing+) | ✅ Complete | `CanAccessBilling`, `CanManageBilling` |
| Automation (Admin+) | ✅ Complete | `CanAccessAutomation` |
| Reporting (Manager+) | ✅ Complete | `CanAccessReporting` |
| Knowledge (all staff) | ✅ Complete | `CanAccessKnowledge` |
| Admin (Admin only) | ✅ Complete | `CanAccessAdmin` |
| **Portal Scopes** |  |  |
| portal:message:* | ✅ Complete | `HasMessageScope` |
| portal:document:* | ✅ Complete | `HasDocumentScope` |
| portal:appointment:* | ✅ Complete | `HasAppointmentScope` |
| portal:invoice:* | ✅ Complete | `HasInvoiceScope` |
| portal:invoice:pay | ✅ Complete | `HasInvoicePayScope` |

**Overall Compliance:** 100% (28/28 requirements)

---

## Security Considerations

### Principle of Least Privilege

Each role receives only the minimum permissions necessary:
- **Staff** cannot manage clients or view reports
- **Manager** cannot manage billing or settings
- **Billing** cannot manage clients or settings
- **ReadOnly** cannot perform any write operations

### Defense in Depth

Multiple layers of access control:
1. **Role-based** - Module visibility
2. **Permission flags** - Fine-grained capabilities
3. **Object-level** - Queryset scoping (assignment, ownership)
4. **Document-level** - Visibility flags
5. **Action-level** - Method-based restrictions (read vs. write)

### Audit Trail

All role changes are auditable:
- `invited_by` tracks who granted access
- `invited_at` tracks when access was granted
- `last_active_at` tracks user activity
- Firm audit events capture permission changes

---

## Migration Guide

### For Existing Deployments

1. **Run migration:**
   ```bash
   python manage.py migrate firm 0011_role_based_views
   ```

2. **Review migrated roles:**
   - All `owner` and `admin` users → `firm_admin`
   - All `contractor` users → `staff`
   - Existing `staff` unchanged

3. **Adjust roles as needed:**
   ```python
   # Promote managers
   FirmMembership.objects.filter(
       user__in=manager_users
   ).update(role="manager")

   # Assign billing role
   FirmMembership.objects.filter(
       user__in=billing_users
   ).update(role="billing")
   ```

4. **Update ViewSets:**
   Replace generic permission classes with role-based classes:
   ```python
   # Before
   permission_classes = [IsAuthenticated, IsStaffUser]

   # After
   from modules.auth.role_permissions import CanAccessCRM
   permission_classes = [IsAuthenticated, CanAccessCRM]
   ```

---

## Testing

### Manual Testing Checklist

**Role Defaults:**
- [ ] Create firm_admin → all permissions True
- [ ] Create partner → appropriate defaults
- [ ] Create manager → appropriate defaults
- [ ] Create staff → all permissions False
- [ ] Create billing → can_manage_billing True only
- [ ] Create readonly → all permissions False

**Module Access:**
- [ ] Staff can access Dashboard, Comms, Calendar, Work, Documents, Knowledge
- [ ] Staff can read (not write) CRM
- [ ] Manager can access CRM, Reporting, Automation (read)
- [ ] Manager cannot access Admin
- [ ] Billing can access Billing (full), not CRM/Admin
- [ ] Admin can access all modules

**Read-Only Enforcement:**
- [ ] ReadOnly role can GET all accessible modules
- [ ] ReadOnly role cannot POST/PUT/PATCH/DELETE
- [ ] Read-only enforcement returns 403 on write operations

**Portal Scopes:**
- [ ] Portal user with can_message_staff can access messages
- [ ] Portal user without can_book_appointments denied appointments
- [ ] Portal user with can_view_invoices can view billing
- [ ] Portal scopes correctly map to permission flags

### Automated Testing

Recommended test coverage:
```python
# tests/test_role_permissions.py
def test_role_defaults_firm_admin():
    """Firm admin should have all permissions."""
    membership = FirmMembership.objects.create(
        firm=firm, user=user, role="firm_admin"
    )
    assert membership.can_manage_users is True
    assert membership.can_manage_clients is True
    assert membership.can_manage_billing is True
    assert membership.can_manage_settings is True
    assert membership.can_view_reports is True

def test_staff_crm_read_only():
    """Staff should have read-only CRM access."""
    # Test GET allowed, POST denied
    pass

def test_readonly_role_enforcement():
    """ReadOnly role should only allow safe methods."""
    # Test write operations denied
    pass
```

---

## Future Enhancements

### 1. Custom Role Builder
Allow firms to create custom roles with specific permission combinations beyond the 6 predefined roles.

### 2. Time-Based Roles
Temporary role elevation (e.g., acting manager for 2 weeks).

### 3. Role Hierarchy Visualization
Admin UI showing role hierarchy and permission inheritance.

### 4. Role-Based Audit Reports
"Who has access to X?" queries for compliance reviews.

### 5. Conditional Role Logic
Dynamic role assignment based on context (e.g., project-specific manager role).

---

## References

- **docs/03-reference/requirements/DOC-27.md** - ROLE_BASED_VIEWS (canonical spec)
- **DOC-18.1** - API endpoint authorization mapping
- **DOC-26.1** - Client portal IA (portal scope integration)
- **spec/SYSTEM_INVARIANTS.md** - Authorization invariants

---

**Document Version:** 1.0
**Last Updated:** December 30, 2025
**Author:** Claude Code
**Status:** Implementation Complete ✅
