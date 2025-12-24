"""
Client Portal Permission Classes (TIER 0: Task 0.4).

These permission classes implement portal containment (default-deny):
- Portal users can ONLY access portal-specific endpoints
- Portal users receive 403 on all firm admin endpoints
- Firm users can access all endpoints

TIER 0 REQUIREMENT: Portal users must be fully contained.
"""
from rest_framework.permissions import BasePermission
from modules.clients.models import ClientPortalUser


class IsPortalUser(BasePermission):
    """
    Permission class: User must be a client portal user.

    TIER 0: Portal-only endpoints.
    Used for endpoints that ONLY portal users can access.
    """

    def has_permission(self, request, view):
        """Check if user is a client portal user."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a portal user record
        try:
            ClientPortalUser.objects.get(user=request.user)
            return True
        except ClientPortalUser.DoesNotExist:
            return False


class IsFirmUser(BasePermission):
    """
    Permission class: User must be a firm team member (NOT a portal user).

    TIER 0: Firm-only endpoints (portal users blocked).
    Used for endpoints that portal users should NEVER access.
    """

    def has_permission(self, request, view):
        """Check if user is a firm user (not a portal user)."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user is NOT a portal user
        try:
            ClientPortalUser.objects.get(user=request.user)
            # User is a portal user - deny access
            return False
        except ClientPortalUser.DoesNotExist:
            # User is NOT a portal user - they're a firm user
            return True


class IsPortalUserOrFirmUser(BasePermission):
    """
    Permission class: User can be either portal user OR firm user.

    TIER 0: Shared endpoints (both user types can access).
    Used for endpoints that both portal and firm users can access,
    but with different data visibility (handled by queryset scoping).
    """

    def has_permission(self, request, view):
        """Check if user is authenticated (either portal or firm)."""
        return request.user and request.user.is_authenticated


class PortalUserHasPermission(BasePermission):
    """
    Permission class: Portal user has specific permission flag.

    TIER 0: Granular portal permissions.
    Used to check specific permission flags on ClientPortalUser model.

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [PortalUserHasPermission]
            portal_permission_required = 'can_view_projects'
    """

    def has_permission(self, request, view):
        """Check if portal user has the required permission."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Get the required permission from the view
        permission_required = getattr(view, 'portal_permission_required', None)
        if not permission_required:
            # No specific permission required - check if firm user
            try:
                ClientPortalUser.objects.get(user=request.user)
                return False  # Portal user without permission requirement
            except ClientPortalUser.DoesNotExist:
                return True  # Firm user - allow

        # Check if user is portal user with the required permission
        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)
            return getattr(portal_user, permission_required, False)
        except ClientPortalUser.DoesNotExist:
            # Firm user - always allow
            return True


class DenyPortalAccess(BasePermission):
    """
    Permission class: DENY all portal users (firm users only).

    TIER 0: Explicit portal denial for sensitive endpoints.
    Use this on endpoints that should NEVER be accessible to portal users.

    This is an explicit "default-deny" for portal users.
    """

    message = "Portal users do not have access to this endpoint."

    def has_permission(self, request, view):
        """Deny access to portal users."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Explicitly deny portal users
        try:
            ClientPortalUser.objects.get(user=request.user)
            return False  # Portal user - DENY
        except ClientPortalUser.DoesNotExist:
            return True  # Firm user - ALLOW


# TIER 0: Portal endpoint allowlist
# These are the ONLY ViewSet classes that portal users can access
PORTAL_ALLOWED_VIEWSETS = {
    'ClientProjectViewSet',
    'ClientCommentViewSet',
    'ClientInvoiceViewSet',
    'ClientChatThreadViewSet',
    'ClientMessageViewSet',
    'ClientProposalViewSet',
    'ClientContractViewSet',
    'ClientEngagementHistoryViewSet',
}


def is_portal_allowed_viewset(view):
    """
    Check if a view/viewset is in the portal allowlist.

    TIER 0: Portal containment - default deny.
    Returns True only if the view class is in PORTAL_ALLOWED_VIEWSETS.
    """
    view_class_name = view.__class__.__name__
    return view_class_name in PORTAL_ALLOWED_VIEWSETS
