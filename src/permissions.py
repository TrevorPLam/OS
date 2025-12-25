"""Shared permission utilities for APIs and background jobs."""
from typing import Optional

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from modules.clients.models import ClientPortalUser
from modules.firm.utils import get_request_firm


class RequireFirmContext(BasePermission):
    """Ensure requests carry firm context resolved by middleware."""

    message = "Firm context is required for this endpoint."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request, "firm", None))


class PortalFirmAccessPermission(BasePermission):
    """Restrict portal users to their own firm's data with optional capability flag."""

    message = "Portal user is not authorized for this firm or lacks required permissions."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        firm = get_request_firm(request)
        if not firm:
            return False

        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)
        except ClientPortalUser.DoesNotExist:
            return True  # Firm users continue to per-object checks

        if portal_user.client.firm_id != firm.id:
            return False

        required_flag = getattr(view, "portal_permission_required", None)
        if required_flag:
            return bool(getattr(portal_user, required_flag, False))

        return True


class PortalAccessMixin:
    """Helper mixin to centralize portal-user validation for viewsets."""

    portal_permission_required: Optional[str] = None

    def get_validated_portal_user(self, request, enforce_permission: bool = True):
        """
        Return the portal user for the request after firm and capability validation.

        Returns None for firm users. Raises PermissionDenied when the portal user
        does not belong to the current firm or lacks the required capability flag.
        """

        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)
        except ClientPortalUser.DoesNotExist:
            return None

        firm = get_request_firm(request)
        if not firm:
            raise PermissionDenied("Firm context required for portal access.")

        if portal_user.client.firm_id != firm.id:
            raise PermissionDenied("Portal user does not belong to this firm.")

        if enforce_permission and self.portal_permission_required:
            if not getattr(portal_user, self.portal_permission_required, False):
                raise PermissionDenied("Portal user lacks required permissions.")

        return portal_user
