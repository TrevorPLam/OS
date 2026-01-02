"""
Granular Permission System for Documents (SEC-2).

Implements folder-level and file-level CRUD permissions with inheritance.

SECURITY REQUIREMENTS:
- Folder-level permissions (Create, Read, Update, Delete)
- File-level permission overrides
- Permission inheritance from parent folders
- Role-based default permissions
- Explicit deny support (deny overrides allow)

Permission Model:
- Subject: User or Role
- Resource: Folder or Document
- Action: Create, Read, Update, Delete, Share
- Effect: Allow or Deny

Permission Resolution Order:
1. Explicit deny (highest priority)
2. File-level permissions
3. Folder-level permissions (with inheritance)
4. Role-based defaults (lowest priority)
"""

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import models
from rest_framework.permissions import BasePermission


class DocumentPermission(models.Model):
    """
    Granular permission for documents and folders.
    
    Supports:
    - Folder-level permissions (inherited by children)
    - File-level permission overrides
    - User-specific and role-specific permissions
    - Allow/Deny effects (deny wins)
    """
    
    # Permission Actions
    ACTION_CREATE = 'create'
    ACTION_READ = 'read'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_SHARE = 'share'
    ACTION_DOWNLOAD = 'download'
    
    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create files/subfolders'),
        (ACTION_READ, 'Read/View content'),
        (ACTION_UPDATE, 'Update/Modify'),
        (ACTION_DELETE, 'Delete'),
        (ACTION_SHARE, 'Share with others'),
        (ACTION_DOWNLOAD, 'Download files'),
    ]
    
    # Permission Effects
    EFFECT_ALLOW = 'allow'
    EFFECT_DENY = 'deny'
    
    EFFECT_CHOICES = [
        (EFFECT_ALLOW, 'Allow'),
        (EFFECT_DENY, 'Deny (overrides allow)'),
    ]
    
    # Resource Type
    RESOURCE_FOLDER = 'folder'
    RESOURCE_DOCUMENT = 'document'
    
    RESOURCE_CHOICES = [
        (RESOURCE_FOLDER, 'Folder'),
        (RESOURCE_DOCUMENT, 'Document'),
    ]
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='document_permissions',
        help_text='Firm this permission belongs to'
    )
    
    # Subject (who has permission)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_permissions',
        help_text='User with this permission (null = role-based)'
    )
    
    role = models.CharField(
        max_length=50,
        blank=True,
        help_text='Role with this permission (blank = user-specific)'
    )
    
    # Resource (what the permission applies to)
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_CHOICES,
        help_text='Type of resource (folder or document)'
    )
    
    folder = models.ForeignKey(
        'documents.Folder',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='permissions',
        help_text='Folder this permission applies to (null if document-level)'
    )
    
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='permissions',
        help_text='Document this permission applies to (null if folder-level)'
    )
    
    # Permission Details
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text='Action being permitted or denied'
    )
    
    effect = models.CharField(
        max_length=10,
        choices=EFFECT_CHOICES,
        default=EFFECT_ALLOW,
        help_text='Allow or deny this action (deny wins)'
    )
    
    # Inheritance Control
    apply_to_children = models.BooleanField(
        default=True,
        help_text='Apply this permission to all child folders/documents'
    )
    
    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_document_permissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    reason = models.TextField(
        blank=True,
        help_text='Reason for granting/denying permission (audit trail)'
    )
    
    class Meta:
        db_table = 'documents_permissions'
        indexes = [
            models.Index(fields=['firm', 'user', 'resource_type']),
            models.Index(fields=['firm', 'role', 'resource_type']),
            models.Index(fields=['folder', 'action']),
            models.Index(fields=['document', 'action']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | ~models.Q(role=''),
                name='user_or_role_required'
            ),
            models.CheckConstraint(
                check=models.Q(folder__isnull=False) | models.Q(document__isnull=False),
                name='folder_or_document_required'
            ),
        ]
        permissions = [
            ('manage_document_permissions', 'Can manage document permissions'),
        ]
    
    def __str__(self):
        subject = f"User {self.user.email}" if self.user else f"Role {self.role}"
        resource = f"Folder {self.folder_id}" if self.folder else f"Document {self.document_id}"
        return f"{subject} -> {self.effect} {self.action} on {resource}"
    
    def clean(self):
        """Validate permission rules."""
        from django.core.exceptions import ValidationError
        
        # Must have either user or role
        if not self.user and not self.role:
            raise ValidationError("Permission must specify either user or role")
        
        # Must have either folder or document
        if not self.folder and not self.document:
            raise ValidationError("Permission must specify either folder or document")
        
        # Cannot have both user and role
        if self.user and self.role:
            raise ValidationError("Permission cannot specify both user and role")
        
        # Cannot have both folder and document
        if self.folder and self.document:
            raise ValidationError("Permission cannot specify both folder and document")
        
        # Validate resource type matches resource
        if self.resource_type == self.RESOURCE_FOLDER and not self.folder:
            raise ValidationError("resource_type is 'folder' but no folder specified")
        if self.resource_type == self.RESOURCE_DOCUMENT and not self.document:
            raise ValidationError("resource_type is 'document' but no document specified")


class PermissionChecker:
    """
    Permission resolution engine for documents.
    
    Resolves permissions using inheritance and priority rules:
    1. Explicit deny (highest priority)
    2. File-level permissions
    3. Folder-level permissions (with inheritance)
    4. Role-based defaults (lowest priority)
    """
    
    def __init__(self, user, firm):
        self.user = user
        self.firm = firm
        self.role = self._get_user_role()
    
    def _get_user_role(self):
        """Get user's role in the firm."""
        from modules.firm.models import FirmMembership
        
        try:
            membership = FirmMembership.objects.get(
                user=self.user,
                firm=self.firm,
                is_active=True
            )
            return membership.role
        except FirmMembership.DoesNotExist:
            return None
    
    def can_perform(self, action, resource):
        """
        Check if user can perform action on resource.
        
        Args:
            action: Action to perform (create, read, update, delete, share, download)
            resource: Folder or Document instance
        
        Returns:
            bool: True if permission granted
        """
        # Admin always has permission
        if self.role in ('owner', 'admin', 'firm_admin'):
            return True
        
        # Check for explicit deny (highest priority)
        if self._has_explicit_deny(action, resource):
            return False
        
        # Check file-level permissions
        if hasattr(resource, 'permissions'):  # Document
            if self._check_resource_permissions(action, resource):
                return True
        
        # Check folder-level permissions (with inheritance)
        if hasattr(resource, 'folder'):  # Document has folder
            folder = resource.folder
        elif hasattr(resource, 'parent'):  # Folder
            folder = resource
        else:
            folder = None
        
        if folder and self._check_folder_permissions(action, folder):
            return True
        
        # Check role-based defaults
        return self._check_role_defaults(action, resource)
    
    def _has_explicit_deny(self, action, resource):
        """Check for explicit deny permission."""
        # Check user-specific deny
        user_deny = DocumentPermission.objects.filter(
            firm=self.firm,
            user=self.user,
            action=action,
            effect=DocumentPermission.EFFECT_DENY,
        )
        
        if isinstance(resource, models.Model):
            if hasattr(resource, 'folder_id'):  # Document
                user_deny = user_deny.filter(document=resource)
            else:  # Folder
                user_deny = user_deny.filter(folder=resource)
        
        if user_deny.exists():
            return True
        
        # Check role-specific deny
        if self.role:
            role_deny = DocumentPermission.objects.filter(
                firm=self.firm,
                role=self.role,
                action=action,
                effect=DocumentPermission.EFFECT_DENY,
            )
            
            if isinstance(resource, models.Model):
                if hasattr(resource, 'folder_id'):  # Document
                    role_deny = role_deny.filter(document=resource)
                else:  # Folder
                    role_deny = role_deny.filter(folder=resource)
            
            if role_deny.exists():
                return True
        
        return False
    
    def _check_resource_permissions(self, action, resource):
        """Check permissions on specific resource."""
        # User-specific permission
        user_perm = DocumentPermission.objects.filter(
            firm=self.firm,
            user=self.user,
            action=action,
            effect=DocumentPermission.EFFECT_ALLOW,
        )
        
        if hasattr(resource, 'folder_id'):  # Document
            user_perm = user_perm.filter(document=resource)
        else:  # Folder
            user_perm = user_perm.filter(folder=resource)
        
        if user_perm.exists():
            return True
        
        # Role-specific permission
        if self.role:
            role_perm = DocumentPermission.objects.filter(
                firm=self.firm,
                role=self.role,
                action=action,
                effect=DocumentPermission.EFFECT_ALLOW,
            )
            
            if hasattr(resource, 'folder_id'):  # Document
                role_perm = role_perm.filter(document=resource)
            else:  # Folder
                role_perm = role_perm.filter(folder=resource)
            
            if role_perm.exists():
                return True
        
        return False
    
    def _check_folder_permissions(self, action, folder):
        """Check folder permissions with inheritance."""
        # Walk up folder hierarchy
        current_folder = folder
        
        while current_folder:
            # Check permissions on current folder
            permissions = DocumentPermission.objects.filter(
                firm=self.firm,
                folder=current_folder,
                action=action,
                effect=DocumentPermission.EFFECT_ALLOW,
                apply_to_children=True,
            )
            
            # User-specific permission
            if permissions.filter(user=self.user).exists():
                return True
            
            # Role-specific permission
            if self.role and permissions.filter(role=self.role).exists():
                return True
            
            # Move to parent folder
            current_folder = current_folder.parent if hasattr(current_folder, 'parent') else None
        
        return False
    
    def _check_role_defaults(self, action, resource):
        """Check default permissions for role."""
        # Default permissions per role (least privilege)
        role_defaults = {
            'staff': ['read'],
            'manager': ['read', 'create', 'update'],
            'partner': ['read', 'create', 'update', 'delete', 'share'],
            'billing': ['read', 'create', 'update'],
        }
        
        if self.role in role_defaults:
            return action in role_defaults[self.role]
        
        return False


class HasDocumentPermission(BasePermission):
    """
    DRF permission class for document operations.
    
    Checks granular permissions on documents and folders.
    """
    
    def has_permission(self, request, view):
        """Check if user can access documents at all."""
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Must have firm context
        firm = getattr(request, 'firm', None)
        if not firm:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user can perform action on specific document/folder."""
        firm = getattr(request, 'firm', None)
        if not firm:
            return False
        
        # Map HTTP method to action
        action_map = {
            'GET': DocumentPermission.ACTION_READ,
            'HEAD': DocumentPermission.ACTION_READ,
            'OPTIONS': DocumentPermission.ACTION_READ,
            'POST': DocumentPermission.ACTION_CREATE,
            'PUT': DocumentPermission.ACTION_UPDATE,
            'PATCH': DocumentPermission.ACTION_UPDATE,
            'DELETE': DocumentPermission.ACTION_DELETE,
        }
        
        action = action_map.get(request.method, DocumentPermission.ACTION_READ)
        
        # Check permission
        checker = PermissionChecker(request.user, firm)
        return checker.can_perform(action, obj)


def check_document_permission(user, firm, action, resource):
    """
    Helper function to check document permission.
    
    Args:
        user: User instance
        firm: Firm instance
        action: Action to perform (create, read, update, delete, share, download)
        resource: Folder or Document instance
    
    Returns:
        bool: True if permission granted
    
    Raises:
        PermissionDenied: If permission denied and raise_exception=True
    """
    checker = PermissionChecker(user, firm)
    
    if not checker.can_perform(action, resource):
        raise PermissionDenied(
            f"You do not have permission to {action} this {resource.__class__.__name__.lower()}"
        )
    
    return True


def grant_permission(firm, user=None, role=None, resource=None, action='read',
                    effect='allow', apply_to_children=True, created_by=None, reason=''):
    """
    Grant permission to user or role on resource.
    
    Args:
        firm: Firm instance
        user: User instance (for user-specific permission)
        role: Role name (for role-specific permission)
        resource: Folder or Document instance
        action: Action to grant (create, read, update, delete, share, download)
        effect: Effect (allow or deny)
        apply_to_children: Apply to child folders/documents
        created_by: User who created this permission
        reason: Reason for granting permission
    
    Returns:
        DocumentPermission instance
    """
    if hasattr(resource, 'folder_id'):  # Document
        resource_type = DocumentPermission.RESOURCE_DOCUMENT
        document = resource
        folder = None
    else:  # Folder
        resource_type = DocumentPermission.RESOURCE_FOLDER
        folder = resource
        document = None
    
    permission = DocumentPermission.objects.create(
        firm=firm,
        user=user,
        role=role,
        resource_type=resource_type,
        folder=folder,
        document=document,
        action=action,
        effect=effect,
        apply_to_children=apply_to_children,
        created_by=created_by,
        reason=reason
    )
    
    return permission


def revoke_permission(firm, user=None, role=None, resource=None, action=None):
    """
    Revoke permission from user or role on resource.
    
    Args:
        firm: Firm instance
        user: User instance (for user-specific permission)
        role: Role name (for role-specific permission)
        resource: Folder or Document instance
        action: Action to revoke (None = all actions)
    
    Returns:
        int: Number of permissions revoked
    """
    filters = {
        'firm': firm,
    }
    
    if user:
        filters['user'] = user
    if role:
        filters['role'] = role
    if action:
        filters['action'] = action
    
    if hasattr(resource, 'folder_id'):  # Document
        filters['document'] = resource
    else:  # Folder
        filters['folder'] = resource
    
    count, _ = DocumentPermission.objects.filter(**filters).delete()
    return count
