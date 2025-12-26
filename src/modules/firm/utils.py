"""
Firm Scoping Utilities (TIER 0).

Provides helpers for ensuring all database queries are properly scoped to a firm.

TIER 0 REQUIREMENT: All customer data queries MUST be scoped to a firm.
Using Model.objects.all() on firm-scoped models is FORBIDDEN.
"""

from django.db import models
from django.http import HttpRequest

from modules.firm.models import BreakGlassSession


class FirmScopingError(Exception):
    """Raised when firm scoping is violated."""

    pass


def get_request_firm(request: HttpRequest):
    """
    Get the firm from the request context.

    Raises:
        FirmScopingError: If request has no firm context

    Returns:
        Firm instance from request
    """
    if not hasattr(request, "firm") or request.firm is None:
        raise FirmScopingError("Request has no firm context. All firm-scoped operations require firm context.")
    return request.firm


def firm_scoped_queryset(model_class: models.Model, firm, base_queryset: models.QuerySet | None = None):
    """
    Get a firm-scoped queryset for a model.

    Args:
        model_class: The Django model class
        firm: The Firm instance to scope to
        base_queryset: Optional base queryset to filter (defaults to model.objects.all())

    Returns:
        QuerySet filtered to the specified firm

    Example:
        # In a view/viewset:
        firm = get_request_firm(request)
        clients = firm_scoped_queryset(Client, firm)
    """
    if firm is None:
        raise FirmScopingError(f"Cannot create firm-scoped queryset for {model_class.__name__}: firm is None")

    if base_queryset is None:
        base_queryset = model_class.objects.all()

    return base_queryset.filter(firm=firm)


class FirmScopedManager(models.Manager):
    """
    Custom manager that enforces firm scoping.

    Usage in models:
        class Client(models.Model):
            firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
            # ...

            objects = models.Manager()  # Keep default manager
            firm_scoped = FirmScopedManager()  # Add firm-scoped manager

        # In views:
        clients = Client.firm_scoped.for_firm(request.firm)
    """

    def for_firm(self, firm):
        """
        Get all objects for a specific firm.

        Args:
            firm: Firm instance to scope to

        Returns:
            QuerySet filtered to the firm
        """
        if firm is None:
            raise FirmScopingError(
                f"Cannot scope {self.model.__name__} to None firm. " "All firm-scoped queries require a firm."
            )
        return self.filter(firm=firm)


class FirmScopedMixin:
    """
    Mixin for ViewSets that automatically scopes querysets to request firm.

    TIER 0: This mixin ensures all ViewSet queries are automatically firm-scoped.

    Usage:
        class ClientViewSet(FirmScopedMixin, viewsets.ModelViewSet):
            model = Client
            serializer_class = ClientSerializer

            # get_queryset() is automatically implemented
    """

    def get_queryset(self):
        """
        Get queryset scoped to the request's firm.

        Override this method if you need additional filtering.
        """
        if not hasattr(self, "model"):
            raise NotImplementedError(
                f"{self.__class__.__name__} must define 'model' attribute " "when using FirmScopedMixin"
            )

        firm = get_request_firm(self.request)
        return firm_scoped_queryset(self.model, firm)


def validate_firm_access(obj, firm):
    """
    Validate that an object belongs to the given firm.

    Raises:
        FirmScopingError: If object doesn't belong to firm

    Args:
        obj: Model instance with 'firm' foreign key
        firm: Firm instance to validate against

    Example:
        client = Client.objects.get(id=client_id)
        validate_firm_access(client, request.firm)
    """
    if not hasattr(obj, "firm"):
        raise FirmScopingError(
            f"{obj.__class__.__name__} does not have 'firm' attribute. " "Cannot validate firm access."
        )

    if obj.firm_id != firm.id:
        raise FirmScopingError(
            f"Access denied: {obj.__class__.__name__} {obj.id} belongs to firm {obj.firm_id}, "
            f"but request is scoped to firm {firm.id}"
        )


def get_firm_or_403(request: HttpRequest):
    """
    Get firm from request or raise PermissionDenied.

    This is a convenience wrapper for views that need firm context.

    Returns:
        Firm instance

    Raises:
        PermissionDenied: If no firm context on request
    """
    from django.core.exceptions import PermissionDenied

    if not hasattr(request, "firm") or request.firm is None:
        raise PermissionDenied(
            "This operation requires firm context. " "Access via firm subdomain or include firm_id in token."
        )

    return request.firm


def get_active_break_glass_session(firm):
    """
    Return the active break-glass session for a firm, if any.

    Meta-commentary:
    - This does not enforce access; it only provides a lookup for guards.
    - Follow-up: wire this into permission checks and platform endpoints.
    """
    if firm is None:
        raise FirmScopingError("Cannot resolve break-glass session without firm context.")
    return BreakGlassSession.objects.for_firm(firm).active().first()


def has_active_break_glass_session(firm) -> bool:
    """
    Return True when a firm has an active break-glass session.

    Meta-commentary:
    - Intended for enforcement gates once break-glass permissions are wired.
    """
    return get_active_break_glass_session(firm) is not None


def expire_overdue_break_glass_sessions(firm) -> int:
    """
    Expire overdue break-glass sessions for a firm.

    Meta-commentary:
    - Intended for scheduled jobs once tenant-safe background processing exists.
    """
    if firm is None:
        raise FirmScopingError("Cannot expire break-glass sessions without firm context.")
    return BreakGlassSession.objects.for_firm(firm).expire_overdue()
