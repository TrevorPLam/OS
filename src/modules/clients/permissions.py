"""
Client Portal Permission Classes (TIER 0: Task 0.4, TIER 2.6: Task 2.6).

These permission classes implement portal containment (default-deny):
- Portal users can ONLY access portal-specific endpoints
- Portal users receive 403 on all firm admin endpoints
- Firm users can access all endpoints

TIER 0 REQUIREMENT: Portal users must be fully contained.
TIER 2.6 REQUIREMENT: Cross-client access allowed ONLY within same organization.
"""
from rest_framework.permissions import BasePermission
from modules.clients.models import ClientPortalUser, Organization


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


# ============================================================================
# TIER 2.6: Organization-Based Cross-Client Access Permissions
# ============================================================================


class HasOrganizationAccess(BasePermission):
    """
    Permission class: User has access to organization-scoped data.

    TIER 2.6: Allow cross-client access within same organization.

    Rules:
    - Firm users: Always allowed (can see all organization data)
    - Portal users: Only allowed if their client belongs to the organization
                    AND organization.enable_cross_client_visibility is True

    This permission should be used on organization-shared endpoints
    where portal users from different clients within the same org
    can see each other's data.

    Usage:
        class OrganizationSharedViewSet(viewsets.ModelViewSet):
            permission_classes = [HasOrganizationAccess]
            # ViewSet must implement get_organization() method
    """

    message = "You do not have access to this organization's data."

    def has_permission(self, request, view):
        """Check if user has access to organization data."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Firm users always have access to organization data
        try:
            ClientPortalUser.objects.get(user=request.user)
            # User is a portal user - needs organization check
            # This will be handled at object level in has_object_permission
            return True
        except ClientPortalUser.DoesNotExist:
            # User is a firm user - full access
            return True

    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific organization object."""
        # Get the organization from the object
        organization = self._get_organization_from_object(obj)
        if not organization:
            # No organization - deny access
            return False

        # Check if organization allows cross-client visibility
        if not organization.enable_cross_client_visibility:
            # Organization has disabled cross-client access
            return False

        # Firm users can access all organization data
        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)
            # Portal user - check if their client is in this organization
            if portal_user.client.organization_id != organization.id:
                return False
            return True
        except ClientPortalUser.DoesNotExist:
            # Firm user - full access
            return True

    def _get_organization_from_object(self, obj):
        """Extract organization from object."""
        # If object is an Organization
        if isinstance(obj, Organization):
            return obj

        # If object has organization FK
        if hasattr(obj, 'organization'):
            return obj.organization

        # If object is a Client with organization
        if hasattr(obj, 'client') and hasattr(obj.client, 'organization'):
            return obj.client.organization

        return None


class RequiresSameOrganization(BasePermission):
    """
    Permission class: Objects must belong to same organization as user's client.

    TIER 2.6: Prevent cross-organization data access.

    Rules:
    - Firm users: Always allowed (can see all data in their firm)
    - Portal users: Can only see data from clients in their organization
                    (if organization exists and cross-client visibility is enabled)

    This is more restrictive than HasOrganizationAccess - it REQUIRES
    the object to have an organization that matches the portal user's client.

    Usage:
        class ClientCommentViewSet(viewsets.ModelViewSet):
            permission_classes = [RequiresSameOrganization]
    """

    message = "You can only access data from your own organization."

    def has_object_permission(self, request, view, obj):
        """Check if object belongs to user's organization."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Firm users can access all objects in their firm
        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)

            # Get portal user's organization
            if not portal_user.client.organization:
                # Portal user has no organization - can only see own client data
                # Check if object belongs to their client
                if hasattr(obj, 'client'):
                    return obj.client_id == portal_user.client_id
                return False

            # Get object's organization
            obj_organization = self._get_organization_from_object(obj)
            if not obj_organization:
                # Object has no organization - deny cross-client access
                if hasattr(obj, 'client'):
                    return obj.client_id == portal_user.client_id
                return False

            # Check if organizations match and cross-client visibility is enabled
            if obj_organization.id != portal_user.client.organization_id:
                return False

            if not obj_organization.enable_cross_client_visibility:
                # Cross-client visibility disabled - can only see own client
                if hasattr(obj, 'client'):
                    return obj.client_id == portal_user.client_id
                return False

            # Same organization + visibility enabled = allow
            return True

        except ClientPortalUser.DoesNotExist:
            # Firm user - full access
            return True

    def _get_organization_from_object(self, obj):
        """Extract organization from object."""
        # If object is an Organization
        if isinstance(obj, Organization):
            return obj

        # If object has organization FK
        if hasattr(obj, 'organization'):
            return obj.organization

        # If object is related to a Client with organization
        if hasattr(obj, 'client') and hasattr(obj.client, 'organization'):
            return obj.client.organization

        return None
