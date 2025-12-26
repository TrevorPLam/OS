"""
Custom permission classes for fine-grained access control.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return hasattr(obj, "owner") and obj.owner == request.user


class IsCreatorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow creators of an object to edit it.
    Assumes the model instance has a `created_by` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the creator
        return hasattr(obj, "created_by") and obj.created_by == request.user


class IsAssignedUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission for time entries and tasks.
    Only the assigned user or project manager can edit.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # For time entries, only the user can edit their own entries
        if hasattr(obj, "user"):
            return obj.user == request.user

        # For tasks, assigned user or project manager can edit
        if hasattr(obj, "assigned_to") and hasattr(obj, "project"):
            return obj.assigned_to == request.user or (
                hasattr(obj.project, "project_manager") and obj.project.project_manager == request.user
            )

        return False


class CannotModifyInvoicedItems(permissions.BasePermission):
    """
    Prevents modification of invoiced time entries.
    This is a data integrity protection.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read operations
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow creation (POST is handled at view level)
        if request.method == "POST":
            return True

        # Block modification of invoiced items
        if hasattr(obj, "invoiced") and obj.invoiced:
            return False

        return True


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read access to authenticated users, write access to admins only.
    Useful for sensitive modules like finance configuration.
    """

    def has_permission(self, request, view):
        # Allow read permissions to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions only for admin users
        return request.user and request.user.is_staff


class IsPaymentAuthorized(permissions.BasePermission):
    """
    Special permission for payment operations.
    Ensures user has permission to process payments for a client.
    """

    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # For payment operations, user must be staff or the client owner
        if request.user.is_staff:
            return True

        # For specific invoice payments, check in has_object_permission
        return True

    def has_object_permission(self, request, view, obj):
        # Staff can process any payment
        if request.user.is_staff:
            return True

        # For invoices, check if user is the client owner or project manager
        if hasattr(obj, "client"):
            return (hasattr(obj.client, "owner") and obj.client.owner == request.user) or (
                hasattr(obj, "project")
                and obj.project
                and hasattr(obj.project, "project_manager")
                and obj.project.project_manager == request.user
            )

        return False
