"""
Permissions for client portal access control.
"""
from rest_framework.permissions import BasePermission

from modules.clients.models import ClientPortalUser


class PortalAccessPermission(BasePermission):
    """
    Deny portal users on non-portal endpoints unless explicitly allowed.
    """

    message = "Client portal users cannot access this endpoint."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True
        if not ClientPortalUser.objects.filter(user=request.user).exists():
            return True
        return getattr(view, "allow_portal", False)
