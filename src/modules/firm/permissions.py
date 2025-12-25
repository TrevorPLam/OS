"""
TIER 0: Platform Privacy Enforcement Permissions.

Implements explicit deny rules for customer content models.

CRITICAL REQUIREMENT:
- Platform operators cannot read customer content by default
- Content includes: documents, messages, comments, notes, invoice line items
- Only metadata is accessible (counts, timestamps, IDs, error traces)
- Break-glass access is rare, explicit, and audited

Meta-commentary:
- These permissions enforce the privacy-first design from NOTES_TO_CLAUDE.md
- Platform staff should use metadata-only views for diagnostics and support
- Content access requires active break-glass session (Tier 0.6)
"""
from rest_framework import permissions
from django.core.exceptions import PermissionDenied
from modules.firm.models import BreakGlassSession


class IsPlatformOperator(permissions.BasePermission):
    """
    Check if user is a platform operator with active platform access.

    This permission checks for:
    - User has platform_profile
    - Platform profile is active
    - Platform role is either operator or break-glass operator
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has platform profile
        if not hasattr(request.user, 'platform_profile'):
            return False

        profile = request.user.platform_profile
        return profile.is_platform_active


class DenyContentAccessByDefault(permissions.BasePermission):
    """
    TIER 0: Default-deny for customer content.

    Platform operators are FORBIDDEN from accessing customer content
    unless they have an active break-glass session.

    Content models (explicit deny list):
    - documents.Document (file content via S3 keys)
    - documents.Version (version content)
    - Any model with 'content', 'text', 'body', 'message', 'notes' fields
    - Invoice line items (billing context)
    - Comments and messages

    Metadata is allowed:
    - IDs, timestamps, counts, status fields
    - Error traces (technical diagnostics)
    - Billing totals (not line items)
    - Firm/client names and basic attributes

    Meta-commentary:
    - This permission should be applied to ALL content-bearing ViewSets
    - Break-glass enforcement is checked via has_active_break_glass_session
    - Future: integrate with audit logging to record break-glass content access
    """

    # Content models that are explicitly denied
    CONTENT_MODEL_DENY_LIST = [
        'documents.Document',
        'documents.Version',
        # Future: add Message, Comment, Note models when they exist
    ]

    # Content fields that should never be returned to platform operators
    CONTENT_FIELD_DENY_LIST = [
        'content',
        'text',
        'body',
        'message',
        'notes',
        's3_key',  # S3 keys allow content retrieval
        'bucket_name',  # Same as above
        'line_items',  # Invoice line items contain billing context
    ]

    def has_permission(self, request, view):
        """
        Check if user can access this endpoint at all.

        Platform operators need explicit break-glass for content models.
        """
        # Non-platform users go through normal permissions
        if not self._is_platform_user(request.user):
            return True

        # Check if this is a content model
        model_name = self._get_model_name(view)
        if model_name in self.CONTENT_MODEL_DENY_LIST:
            # Require active break-glass session for content models
            return self._has_active_break_glass(request)

        # Metadata models are allowed
        return True

    def has_object_permission(self, request, view, obj):
        """
        Check if user can access a specific object.

        Same logic as has_permission but at object level.
        """
        # Non-platform users go through normal permissions
        if not self._is_platform_user(request.user):
            return True

        # Check if this is a content model
        model_name = f"{obj._meta.app_label}.{obj._meta.model_name}"
        if model_name.lower() in [m.lower() for m in self.CONTENT_MODEL_DENY_LIST]:
            return self._has_active_break_glass(request)

        return True

    def _is_platform_user(self, user):
        """Check if user is a platform operator."""
        if not user or not user.is_authenticated:
            return False
        return hasattr(user, 'platform_profile') and user.platform_profile.is_platform_active

    def _get_model_name(self, view):
        """Get the model name for a ViewSet."""
        if hasattr(view, 'queryset') and view.queryset is not None:
            model = view.queryset.model
            return f"{model._meta.app_label}.{model._meta.model_name}"
        elif hasattr(view, 'model'):
            model = view.model
            return f"{model._meta.app_label}.{model._meta.model_name}"
        return None

    def _has_active_break_glass(self, request):
        """
        Check if user has an active break-glass session.

        Logs audit event when break-glass is used to access content.
        """
        # Platform user must have break-glass capability
        if not hasattr(request.user, 'platform_profile'):
            return False

        profile = request.user.platform_profile
        if not profile.can_activate_break_glass:
            return False

        # Must have firm context
        if not hasattr(request, 'firm') or request.firm is None:
            return False

        # Check for active break-glass session for this operator in this firm
        active_session = BreakGlassSession.objects.filter(
            firm=request.firm,
            operator=request.user,
            status=BreakGlassSession.STATUS_ACTIVE
        ).first()

        if active_session and active_session.is_active:
            # Log audit event for break-glass content access
            self._log_break_glass_content_access(request, active_session)
            return True

        return False

    def _log_break_glass_content_access(self, request, session):
        """Log audit event when break-glass accesses content."""
        try:
            from modules.firm.audit import audit

            audit.log_break_glass_event(
                firm=request.firm,
                action='break_glass_content_access',
                actor=request.user,
                reason=session.reason,
                target_model='ContentModel',
                target_id='',
                metadata={
                    'path': request.path,
                    'method': request.method,
                    'session_id': session.id,
                    'impersonated_user_id': session.impersonated_user_id,
                },
            )
        except Exception:
            # Don't block access if audit logging fails
            pass


class MetadataOnlyAccess(permissions.BasePermission):
    """
    TIER 0: Restrict serializer fields to metadata-only for platform operators.

    This permission works with serializers to ensure platform operators
    only see metadata fields, not content fields.

    Metadata fields (allowed):
    - id, created_at, updated_at, status
    - firm_id, client_id, user_id (foreign keys)
    - file_size, mime_type, version_number (technical metadata)
    - error traces, counts, aggregates

    Content fields (denied):
    - content, text, body, message, notes
    - s3_key, bucket_name (enables content retrieval)
    - line_items (invoice context)

    Usage:
        # In ViewSet:
        permission_classes = [IsPlatformOperator, MetadataOnlyAccess]

        # In Serializer:
        class Meta:
            fields = '__all__'
            # Platform operators will only see METADATA_ALLOWED_FIELDS

    Meta-commentary:
    - This should be combined with custom serializers that filter fields
    - Future: implement serializer mixins to auto-filter content fields
    """

    METADATA_ALLOWED_FIELDS = [
        'id',
        'created_at',
        'updated_at',
        'status',
        'firm_id',
        'client_id',
        'user_id',
        'file_size',
        'mime_type',
        'version_number',
        'count',
        'total',
        'error_trace',
    ]

    def has_permission(self, request, view):
        """
        Always return True - this permission controls field visibility,
        not endpoint access.
        """
        return True


class RequireBreakGlassForContent(permissions.BasePermission):
    """
    TIER 0: Explicit break-glass requirement for content access.

    This is a stricter version of DenyContentAccessByDefault.
    Use this on endpoints that ONLY serve content (no metadata).

    Examples:
    - Document download endpoints
    - Message content endpoints
    - Invoice line item detail views

    Meta-commentary:
    - These endpoints should return 403 for platform operators without break-glass
    - Error message should clearly indicate break-glass is required
    """

    def has_permission(self, request, view):
        """Require active break-glass for ALL platform users."""
        if not self._is_platform_user(request.user):
            return True

        # Platform users MUST have active break-glass
        if not self._has_active_break_glass(request):
            raise PermissionDenied(
                "This endpoint requires an active break-glass session. "
                "Platform operators cannot access customer content without break-glass."
            )

        return True

    def has_object_permission(self, request, view, obj):
        """Same requirement at object level."""
        return self.has_permission(request, view)

    def _is_platform_user(self, user):
        """Check if user is a platform operator."""
        if not user or not user.is_authenticated:
            return False
        return hasattr(user, 'platform_profile') and user.platform_profile.is_platform_active

    def _has_active_break_glass(self, request):
        """Check for active break-glass session and log content access."""
        if not hasattr(request.user, 'platform_profile'):
            return False

        profile = request.user.platform_profile
        if not profile.can_activate_break_glass:
            return False

        if not hasattr(request, 'firm') or request.firm is None:
            return False

        active_session = BreakGlassSession.objects.filter(
            firm=request.firm,
            operator=request.user,
            status=BreakGlassSession.STATUS_ACTIVE
        ).first()

        if active_session and active_session.is_active:
            # Log audit event for break-glass content access
            self._log_break_glass_content_access(request, active_session)
            return True

        return False

    def _log_break_glass_content_access(self, request, session):
        """Log audit event when break-glass accesses content."""
        try:
            from modules.firm.audit import audit

            audit.log_break_glass_event(
                firm=request.firm,
                action='break_glass_content_access',
                actor=request.user,
                reason=session.reason,
                target_model='ContentModel',
                target_id='',
                metadata={
                    'path': request.path,
                    'method': request.method,
                    'session_id': session.id,
                    'impersonated_user_id': session.impersonated_user_id,
                },
            )
        except Exception:
            # Don't block access if audit logging fails
            pass
