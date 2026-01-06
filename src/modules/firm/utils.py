"""
Firm Scoping Utilities (TIER 0).

Provides helpers for ensuring all database queries are properly scoped to a firm.

TIER 0 REQUIREMENT: All customer data queries MUST be scoped to a firm.
Using Model.objects.all() on firm-scoped models is FORBIDDEN.
"""

from contextlib import contextmanager

from django.db import connection, models
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


class FirmScopedQuerySet(models.QuerySet):
    """
    QuerySet that automatically enforces firm scoping.

    Per SYSTEM_SPEC section 3.1.2: "All tenant-scoped queries MUST use FirmScopedQuerySet
    or equivalent enforcement to prevent cross-tenant data access."

    Usage in models:
        class Client(models.Model):
            firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
            # ...

            objects = FirmScopedManager.from_queryset(FirmScopedQuerySet)()

        # In views:
        clients = Client.objects.for_firm(request.firm)

    This QuerySet provides firm-scoped filtering methods and can be chained
    with other QuerySet operations.
    """

    def for_firm(self, firm):
        """
        Filter queryset to a specific firm.

        Args:
            firm: Firm instance to scope to

        Returns:
            QuerySet filtered to the firm

        Raises:
            FirmScopingError: If firm is None
        """
        if firm is None:
            raise FirmScopingError(
                f"Cannot scope {self.model.__name__} to None firm. " "All firm-scoped queries require a firm."
            )
        return self.filter(firm=firm)

    def exclude_deleted(self):
        """
        Exclude soft-deleted records (if model has deleted_at field).

        Returns:
            QuerySet excluding deleted records
        """
        if hasattr(self.model, 'deleted_at'):
            return self.filter(deleted_at__isnull=True)
        return self

    def active(self):
        """
        Filter to active records (combines firm scoping with active status if applicable).

        Returns:
            QuerySet filtered to active records
        """
        qs = self.exclude_deleted()
        if hasattr(self.model, 'is_active'):
            qs = qs.filter(is_active=True)
        elif hasattr(self.model, 'status'):
            # Common pattern: status='active'
            qs = qs.filter(status='active')
        return qs


def firm_scoped_queryset(model_class: models.Model, firm, base_queryset: models.QuerySet | None = None):
    """
    Get a firm-scoped queryset for a model.

    DEPRECATED: Use FirmScopedQuerySet.for_firm() instead.

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
    Custom manager that enforces firm scoping using FirmScopedQuerySet.

    Per SYSTEM_SPEC section 3.1.2: Provides firm-scoped query methods.

    Usage in models:
        class Client(models.Model):
            firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
            # ...

            objects = FirmScopedManager()  # Use as default manager

        # In views:
        clients = Client.objects.for_firm(request.firm)
        active_clients = Client.objects.for_firm(request.firm).active()

    The manager uses FirmScopedQuerySet, providing all its methods (for_firm, exclude_deleted, active).
    """

    def get_queryset(self):
        """
        Return the base FirmScopedQuerySet.

        This ensures all queries through this manager use FirmScopedQuerySet.
        """
        return FirmScopedQuerySet(self.model, using=self._db)

    def for_firm(self, firm):
        """
        Get all objects for a specific firm.

        Args:
            firm: Firm instance to scope to

        Returns:
            FirmScopedQuerySet filtered to the firm
        """
        return self.get_queryset().for_firm(firm)

    def exclude_deleted(self):
        """
        Exclude soft-deleted records.

        Returns:
            FirmScopedQuerySet excluding deleted records
        """
        return self.get_queryset().exclude_deleted()

    def active(self):
        """
        Filter to active records.

        Returns:
            FirmScopedQuerySet filtered to active records
        """
        return self.get_queryset().active()


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


def _get_current_firm_setting() -> str | None:
    """
    Return the current app.current_firm_id GUC value.

    Returns None when unset or when not on PostgreSQL.
    """
    if connection.vendor != "postgresql":
        return None

    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('app.current_firm_id', true)")
        current = cursor.fetchone()[0]

    return current or None


def _normalize_firm_id(firm) -> int | str | None:
    """Extract a firm identifier from a firm instance or raw identifier."""
    if firm is None:
        return None
    return getattr(firm, "id", firm)


def set_current_firm_db_session(firm) -> None:
    """
    Set app.current_firm_id for the active database session.

    Intended for PostgreSQL connections; no-ops on other engines.
    """
    firm_id = _normalize_firm_id(firm)
    if firm_id is None or connection.vendor != "postgresql":
        return

    with connection.cursor() as cursor:
        cursor.execute("SET SESSION app.current_firm_id = %s", [firm_id])


def clear_current_firm_db_session() -> None:
    """
    Reset app.current_firm_id for the active database session.

    Avoids leaking firm context across requests or background jobs.
    """
    if connection.vendor != "postgresql":
        return

    current = _get_current_firm_setting()
    if current is None:
        return

    with connection.cursor() as cursor:
        cursor.execute("RESET app.current_firm_id")


@contextmanager
def firm_db_session(firm):
    """
    Context manager to apply firm context to the current DB session.

    Sets app.current_firm_id for PostgreSQL connections and restores the prior
    value on exit to prevent context bleed across jobs or requests.
    """
    if connection.vendor != "postgresql":
        yield
        return

    previous = _get_current_firm_setting()
    set_current_firm_db_session(firm)

    try:
        yield
    finally:
        if previous:
            set_current_firm_db_session(previous)
        else:
            clear_current_firm_db_session()


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
    - **Current Status:** Lookup helper implemented; returns active session or None.
    - **Follow-up (T-065):** Wire into permission checks and platform endpoints.
    - **Assumption:** This does not enforce access; only provides lookup for guards.
    - **Missing:** Integration with permission checks and platform endpoints.
    - **Limitation:** Requires firm context to resolve sessions; raises if missing.
    """
    if firm is None:
        raise FirmScopingError("Cannot resolve break-glass session without firm context.")
    return BreakGlassSession.objects.for_firm(firm).active().first()


def has_active_break_glass_session(firm) -> bool:
    """
    Return True when a firm has an active break-glass session.

    Meta-commentary:
    - **Current Status:** Boolean check implemented; returns True if active session exists.
    - **Follow-up (T-065):** Use in enforcement gates once break-glass permissions are wired.
    - **Assumption:** Intended for enforcement gates in middleware/permissions.
    - **Missing:** Enforcement gates calling this method.
    - **Limitation:** Only checks for session presence; does not validate action scope.
    """
    return get_active_break_glass_session(firm) is not None


def expire_overdue_break_glass_sessions(firm) -> int:
    """
    Expire overdue break-glass sessions for a firm.

    Meta-commentary:
    - **Current Status:** Expiration logic implemented; calls QuerySet.expire_overdue().
    - **Follow-up (T-066):** Wire to scheduled job once tenant-safe background processing exists.
    - **Assumption:** Intended for scheduled jobs with firm-scoped task execution.
    - **Missing:** Scheduled job integration; currently manual invocation only.
    - **Limitation:** No global expiration; each firm must be processed explicitly.
    """
    if firm is None:
        raise FirmScopingError("Cannot expire break-glass sessions without firm context.")
    return BreakGlassSession.objects.for_firm(firm).expire_overdue()
