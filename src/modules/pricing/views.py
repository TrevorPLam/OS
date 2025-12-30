"""
API Views for Pricing module (DOC-09.2).

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
DOC-09.2: QuoteVersion retrieval is audited for compliance.

Implements:
- RuleSetViewSet: Manage versioned pricing rules
- QuoteViewSet: Manage quote drafts
- QuoteVersionViewSet: Retrieve immutable quote snapshots (audit-logged)
"""

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.filters import BoundedSearchFilter
from config.query_guards import QueryTimeoutMixin
from modules.clients.permissions import DenyPortalAccess
from modules.firm.audit import AuditEvent
from modules.firm.utils import FirmScopedMixin, get_request_firm
from modules.pricing.models import Quote, QuoteVersion, RuleSet
from modules.pricing.serializers import (
    QuoteListSerializer,
    QuoteSerializer,
    QuoteVersionListSerializer,
    QuoteVersionSerializer,
    RuleSetListSerializer,
    RuleSetSerializer,
)


class RuleSetViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for RuleSet management.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    DOC-09.1: Published rulesets are immutable.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    """

    model = RuleSet
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "code", "schema_version"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "version", "created_at", "published_at"]
    ordering = ["-version"]

    def get_serializer_class(self):
        """Use lightweight serializer for list view."""
        if self.action == "list":
            return RuleSetListSerializer
        return RuleSetSerializer

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("firm", "created_by")

    def perform_create(self, serializer):
        """Set firm and created_by when creating ruleset."""
        firm = get_request_firm(self.request)
        serializer.save(firm=firm, created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """
        Publish a ruleset, making it immutable.

        DOC-09.1: Published rulesets cannot be modified.
        """
        ruleset = self.get_object()

        if ruleset.status == "published":
            return Response(
                {"detail": "Ruleset is already published."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            ruleset.publish(user=request.user)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Audit the publish action
        AuditEvent.objects.create(
            firm=ruleset.firm,
            category=AuditEvent.CATEGORY_CONFIG,
            action="pricing_ruleset_published",
            severity=AuditEvent.SEVERITY_INFO,
            actor_user=request.user,
            resource_type="RuleSet",
            resource_id=str(ruleset.id),
            metadata={
                "ruleset_code": ruleset.code,
                "ruleset_version": ruleset.version,
                "checksum": ruleset.checksum,
            },
        )

        serializer = self.get_serializer(ruleset)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def deprecate(self, request, pk=None):
        """
        Deprecate a ruleset.

        Published rulesets can be deprecated but remain immutable.
        """
        ruleset = self.get_object()

        if ruleset.status == "deprecated":
            return Response(
                {"detail": "Ruleset is already deprecated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ruleset.status = "deprecated"
        ruleset.deprecated_at = timezone.now()
        ruleset.save()

        # Audit the deprecation action
        AuditEvent.objects.create(
            firm=ruleset.firm,
            category=AuditEvent.CATEGORY_CONFIG,
            action="pricing_ruleset_deprecated",
            severity=AuditEvent.SEVERITY_INFO,
            actor_user=request.user,
            resource_type="RuleSet",
            resource_id=str(ruleset.id),
            metadata={
                "ruleset_code": ruleset.code,
                "ruleset_version": ruleset.version,
            },
        )

        serializer = self.get_serializer(ruleset)
        return Response(serializer.data)


class QuoteViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Quote management.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    DOC-09.1: Quotes are mutable working drafts.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    """

    model = Quote
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "client"]
    search_fields = ["quote_number", "client__company_name"]
    ordering_fields = ["quote_number", "created_at", "valid_until"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Use lightweight serializer for list view."""
        if self.action == "list":
            return QuoteListSerializer
        return QuoteSerializer

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related(
            "firm",
            "client",
            "created_by",
            "current_version",
        )

    def perform_create(self, serializer):
        """Set firm and created_by when creating quote."""
        firm = get_request_firm(self.request)
        serializer.save(firm=firm, created_by=self.request.user)


class QuoteVersionViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for QuoteVersion retrieval (read-only).

    DOC-09.2: QuoteVersion is immutable snapshot for audit.
    All retrieval operations are audit-logged for compliance.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    """

    model = QuoteVersion
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "quote", "ruleset"]
    ordering_fields = ["version_number", "created_at", "issued_at", "accepted_at"]
    ordering = ["-version_number"]

    def get_serializer_class(self):
        """Use lightweight serializer for list view."""
        if self.action == "list":
            return QuoteVersionListSerializer
        return QuoteVersionSerializer

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related(
            "firm",
            "quote",
            "quote__client",
            "ruleset",
            "issued_by",
            "accepted_by",
        ).prefetch_related("line_item_records")

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single quote version with audit logging.

        DOC-09.2: All quote version retrievals are audited for compliance.
        """
        instance = self.get_object()

        # Audit the retrieval action
        AuditEvent.objects.create(
            firm=instance.firm,
            category=AuditEvent.CATEGORY_DATA_ACCESS,
            action="pricing_quote_version_retrieved",
            severity=AuditEvent.SEVERITY_INFO,
            actor_user=request.user,
            resource_type="QuoteVersion",
            resource_id=str(instance.id),
            metadata={
                "quote_number": instance.quote.quote_number,
                "version_number": instance.version_number,
                "status": instance.status,
                "total_amount": str(instance.total_amount),
                "currency": instance.currency,
                "ruleset_id": instance.ruleset_id,
                "ruleset_checksum": instance.ruleset_checksum,
                "correlation_id": instance.correlation_id,
            },
            request_ip=self._get_client_ip(request),
            request_path=request.path,
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """
        List quote versions with audit logging.

        DOC-09.2: Audit log when quote versions are listed for review.
        """
        response = super().list(request, *args, **kwargs)

        # Audit the list action
        firm = get_request_firm(request)
        AuditEvent.objects.create(
            firm=firm,
            category=AuditEvent.CATEGORY_DATA_ACCESS,
            action="pricing_quote_versions_listed",
            severity=AuditEvent.SEVERITY_INFO,
            actor_user=request.user,
            resource_type="QuoteVersion",
            metadata={
                "count": len(response.data.get("results", [])),
                "filters": dict(request.query_params),
            },
            request_ip=self._get_client_ip(request),
            request_path=request.path,
        )

        return response

    @action(detail=True, methods=["get"])
    def trace(self, request, pk=None):
        """
        Retrieve evaluation trace for audit purposes.

        DOC-09.2: Evaluation trace retrieval is separately audited.
        """
        instance = self.get_object()

        # Audit the trace retrieval action
        AuditEvent.objects.create(
            firm=instance.firm,
            category=AuditEvent.CATEGORY_DATA_ACCESS,
            action="pricing_quote_trace_retrieved",
            severity=AuditEvent.SEVERITY_INFO,
            actor_user=request.user,
            resource_type="QuoteVersion",
            resource_id=str(instance.id),
            metadata={
                "quote_number": instance.quote.quote_number,
                "version_number": instance.version_number,
                "correlation_id": instance.correlation_id,
            },
            request_ip=self._get_client_ip(request),
            request_path=request.path,
        )

        return Response({
            "quote_version_id": instance.id,
            "version_number": instance.version_number,
            "evaluation_trace": instance.evaluation_trace,
            "ruleset_checksum": instance.ruleset_checksum,
            "outputs_checksum": instance.outputs_checksum,
        })

    def _get_client_ip(self, request):
        """Extract client IP from request for audit logging."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
