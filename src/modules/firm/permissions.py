"""
Platform Permission Classes (TIER 0.5 - Privacy Enforcement).

Enforces the privacy-first posture:
- Platform Operators can access metadata only
- Content fields are explicitly denied
- Break-glass requires active session

Content Models (protected):
- documents (Document, Version)
- messages (future)
- comments (future)
- notes (future)
- invoice line items (text descriptions)
"""
from rest_framework import permissions
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from typing import Optional


class IsPlatformStaff(permissions.BasePermission):
    """
    Base permission for platform staff roles.
    
    Grants access to users with platform_role set.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has a platform profile with a platform role
        if hasattr(request.user, 'platform_profile'):
            return request.user.platform_profile.is_platform_staff
        
        return False


class IsPlatformOperator(permissions.BasePermission):
    """
    Permission for Platform Operator role (metadata-only).
    
    Platform Operators can:
    - View billing metadata (totals, dates, status)
    - View subscription state
    - View audit logs
    - View operational metadata (counts, timestamps)
    
    Platform Operators CANNOT:
    - Read content fields (documents, messages, comments, notes)
    - Access invoice line item details
    - Read engagement/project/task content
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has platform operator role
        if hasattr(request.user, 'platform_profile'):
            return request.user.platform_profile.is_platform_operator
        
        return False


class IsBreakGlassOperator(permissions.BasePermission):
    """
    Permission for Break-Glass Operator role.
    
    Break-Glass Operators can activate break-glass sessions but
    still need an active session to access content.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has break-glass operator role
        if hasattr(request.user, 'platform_profile'):
            return request.user.platform_profile.is_break_glass_operator
        
        return False


class DenyPlatformContentAccess(permissions.BasePermission):
    """
    Explicit deny rule for content-bearing models.
    
    This permission should be applied to ViewSets that serve content fields.
    Platform Operators are always denied, even if other permissions would allow access.
    
    Only Break-Glass Operators with active sessions can access content.
    """
    
    message = "Platform operators cannot access customer content. Break-glass session required."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True  # Let other auth handle this
        
        # Check if user has platform profile
        if not hasattr(request.user, 'platform_profile'):
            return True  # Regular firm user, allow
        
        profile = request.user.platform_profile
        
        # Platform operators are explicitly denied
        if profile.is_platform_operator:
            return False
        
        # Break-glass operators need an active session
        if profile.is_break_glass_operator:
            return self._has_active_break_glass_session(request.user, request)
        
        # Regular users are allowed
        return True
    
    def _has_active_break_glass_session(self, user, request) -> bool:
        """
        Check if user has an active break-glass session.
        
        Note: This will need the firm context from the request.
        For now, we check if ANY active session exists for this user.
        """
        from modules.firm.models import BreakGlassSession
        
        # Check for active sessions
        active_sessions = BreakGlassSession.objects.filter(
            operator=user,
            status=BreakGlassSession.STATUS_ACTIVE
        ).exclude(
            expires_at__lte=timezone.now()
        )
        
        # If firm context is available, scope to that firm
        if hasattr(request, 'firm') and request.firm:
            active_sessions = active_sessions.filter(firm=request.firm)
        
        return active_sessions.exists()


class MetadataOnlyMixin:
    """
    Mixin for ViewSets to enforce metadata-only responses for platform operators.
    
    Usage:
        class MyViewSet(MetadataOnlyMixin, viewsets.ModelViewSet):
            content_fields = ['description', 'notes', 'content', 'body']
            ...
    
    The mixin will automatically filter out content fields from responses
    when the requester is a platform operator.
    """
    
    content_fields = []  # Override in subclass
    
    def get_serializer(self, *args, **kwargs):
        """Override serializer to remove content fields for platform operators."""
        serializer = super().get_serializer(*args, **kwargs)
        
        # Check if requester is a platform operator
        if self._is_platform_operator(self.request):
            # Remove content fields from serializer
            for field in self.content_fields:
                if field in serializer.fields:
                    serializer.fields.pop(field)
        
        return serializer
    
    def _is_platform_operator(self, request) -> bool:
        """Check if requester is a platform operator."""
        if not request or not request.user or not request.user.is_authenticated:
            return False
        
        if hasattr(request.user, 'platform_profile'):
            return request.user.platform_profile.is_platform_operator
        
        return False

