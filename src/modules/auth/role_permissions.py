"""
Role-Based Module Visibility Permissions (DOC-27.1).

Implements least privilege defaults per docs/27.
Defines which roles can access which modules.

Module visibility rules:
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
"""

from rest_framework.permissions import BasePermission
from modules.firm.models import FirmMembership


def get_user_role(user, request=None):
    """
    Get user's role for the current firm context.

    Returns normalized role (maps legacy roles to DOC-27.1 roles).
    """
    if not user or not user.is_authenticated:
        return None

    # Get firm from request context
    firm = getattr(request, "firm", None) if request else None
    if not firm:
        return None

    try:
        membership = FirmMembership.objects.get(user=user, firm=firm, is_active=True)
        role = membership.role

        # Normalize legacy roles
        if role in ("owner", "admin"):
            return "firm_admin"
        elif role == "contractor":
            return "staff"

        return role
    except FirmMembership.DoesNotExist:
        return None


def is_admin(user, request=None):
    """Check if user has firm_admin role."""
    return get_user_role(user, request) == "firm_admin"


def is_manager_or_above(user, request=None):
    """Check if user has manager+ role (manager, partner, firm_admin)."""
    role = get_user_role(user, request)
    return role in ("manager", "partner", "firm_admin")


def is_billing_or_above(user, request=None):
    """Check if user has billing+ role."""
    role = get_user_role(user, request)
    return role in ("billing", "firm_admin", "partner")


# Module-specific permission classes


class IsStaffUser(BasePermission):
    """
    Permission class: allows any authenticated staff user (any role).
    
    This is a general permission for staff-only endpoints.
    Portal users are denied.
    """
    
    def has_permission(self, request, view):
        """Check if user is a staff user (has any firm role)."""
        return get_user_role(request.user, request) is not None


class IsManager(BasePermission):
    """
    Permission class: allows manager+ roles (manager, partner, firm_admin).
    
    This is for admin/management endpoints requiring elevated privileges.
    """
    
    def has_permission(self, request, view):
        """Check if user is manager or above."""
        return is_manager_or_above(request.user, request)


class CanAccessDashboard(BasePermission):
    """Dashboard: all staff."""

    def has_permission(self, request, view):
        return get_user_role(request.user, request) is not None


class CanAccessCommunications(BasePermission):
    """Communications: all staff."""

    def has_permission(self, request, view):
        return get_user_role(request.user, request) is not None


class CanAccessCalendar(BasePermission):
    """Calendar: all staff."""

    def has_permission(self, request, view):
        return get_user_role(request.user, request) is not None


class CanAccessCRM(BasePermission):
    """
    CRM: Manager+ (Staff may have limited account read).

    For read operations: staff allowed
    For write operations: manager+ required
    """

    def has_permission(self, request, view):
        role = get_user_role(request.user, request)
        if role is None:
            return False

        # Manager+ can do everything
        if role in ("manager", "partner", "firm_admin"):
            return True

        # Staff can read only
        if role == "staff" and request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        return False


class CanAccessEngagements(BasePermission):
    """Engagements: all staff (scoped by assignment policy)."""

    def has_permission(self, request, view):
        return get_user_role(request.user, request) is not None


class CanAccessWork(BasePermission):
    """Work: all staff."""

    def has_permission(self, request, view):
        return get_user_role(request.user, request) is not None


class CanAccessDocuments(BasePermission):
    """Documents: all staff (scoped by permissions)."""

    def has_permission(self, request, view):
        return get_user_role(request.user, request) is not None


class CanAccessBilling(BasePermission):
    """
    Billing: Billing+ (others read-only invoices if allowed).

    Billing role has full access.
    Others can read-only if explicitly allowed.
    """

    def has_permission(self, request, view):
        role = get_user_role(request.user, request)
        if role is None:
            return False

        # Billing, Partner, Admin have full access
        if role in ("billing", "partner", "firm_admin"):
            return True

        # Manager can read invoices (limited billing per docs/27)
        if role == "manager" and request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        return False


class CanManageBilling(BasePermission):
    """
    Manage Billing: Billing+ only.

    Write operations on billing require billing role or above.
    """

    def has_permission(self, request, view):
        role = get_user_role(request.user, request)
        return role in ("billing", "partner", "firm_admin")


class CanAccessAutomation(BasePermission):
    """
    Automation: Admin+ (Managers may see limited status views).

    Admin has full access.
    Manager can read automation status.
    """

    def has_permission(self, request, view):
        role = get_user_role(request.user, request)
        if role is None:
            return False

        # Admin has full access
        if role == "firm_admin":
            return True

        # Manager can read status
        if role == "manager" and request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        return False


class CanAccessReporting(BasePermission):
    """
    Reporting: Manager+ (Admin sees all).

    Manager and above can access reports.
    Admin has full visibility.
    """

    def has_permission(self, request, view):
        role = get_user_role(request.user, request)
        return role in ("manager", "partner", "firm_admin")


class CanAccessKnowledge(BasePermission):
    """Knowledge: all staff (some sections restricted)."""

    def has_permission(self, request, view):
        return get_user_role(request.user, request) is not None


class CanAccessAdmin(BasePermission):
    """Admin: Admin only."""

    def has_permission(self, request, view):
        return get_user_role(request.user, request) == "firm_admin"


class IsReadOnlyRole(BasePermission):
    """
    Read-only role enforcement.

    Users with readonly role can only perform safe (read) operations.
    """

    def has_permission(self, request, view):
        role = get_user_role(request.user, request)

        # Non-readonly roles have full access
        if role != "readonly":
            return True

        # Readonly role can only do safe methods
        return request.method in ("GET", "HEAD", "OPTIONS")


# Portal scope permissions (DOC-27.1)


class HasPortalScope(BasePermission):
    """
    Base class for portal scope validation.

    Portal scopes map to portal nav per docs/27:
    - portal:message:* for Messages
    - portal:document:* for Documents
    - portal:appointment:* for Appointments
    - portal:invoice:* for Billing
    - portal:invoice:pay for payment
    """

    required_scope = None  # Override in subclasses

    def has_permission(self, request, view):
        """Check if portal user has required scope."""
        from modules.clients.models import ClientPortalUser

        if not request.user or not request.user.is_authenticated:
            return False

        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)

            # Map scope to permission flags
            if self.required_scope == "portal:message:*":
                return portal_user.can_message_staff
            elif self.required_scope == "portal:document:*":
                return portal_user.can_view_documents
            elif self.required_scope == "portal:appointment:*":
                return portal_user.can_book_appointments
            elif self.required_scope == "portal:invoice:*":
                return portal_user.can_view_invoices
            elif self.required_scope == "portal:invoice:pay":
                return portal_user.can_view_invoices  # Can pay if can view

            return False
        except ClientPortalUser.DoesNotExist:
            return False


class HasMessageScope(HasPortalScope):
    """Messages requires portal:message:*"""

    required_scope = "portal:message:*"


class HasDocumentScope(HasPortalScope):
    """Documents requires portal:document:*"""

    required_scope = "portal:document:*"


class HasAppointmentScope(HasPortalScope):
    """Appointments requires portal:appointment:*"""

    required_scope = "portal:appointment:*"


class HasInvoiceScope(HasPortalScope):
    """Billing requires portal:invoice:*"""

    required_scope = "portal:invoice:*"


class HasInvoicePayScope(HasPortalScope):
    """Payment requires portal:invoice:pay"""

    required_scope = "portal:invoice:pay"
