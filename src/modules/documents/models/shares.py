import ipaddress
import uuid
from typing import Any

import bcrypt
from django.conf import settings
from django.db import models
from django.utils import timezone

from modules.core.encryption import field_encryption_service
from modules.firm.utils import FirmScopedManager
from modules.projects.models import Project


class ExternalShare(models.Model):
    """
    External document sharing model (Task 3.10).
    
    Enables secure token-based sharing of documents with external parties
    without requiring authentication. Supports password protection, expiration,
    download limits, and comprehensive access tracking.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    ACCESS_TYPE_CHOICES = [
        ("view", "View Only"),
        ("download", "Download"),
        ("comment", "View & Comment"),
        ("upload", "Upload Only"),
    ]
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="external_shares",
        help_text="Firm (workspace) this share belongs to",
    )
    
    # Document being shared (nullable for upload-only shares)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="external_shares",
        help_text="The document being shared externally (null for upload-only shares)",
    )
    
    # Share token (UUID for secure public access)
    share_token = models.UUIDField(
        unique=True,
        db_index=True,
        editable=False,
        help_text="Unique token for accessing this share",
    )
    
    # Share configuration
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        default="view",
        help_text="Type of access granted",
    )
    
    # Password protection
    require_password = models.BooleanField(
        default=False,
        help_text="Whether password is required to access",
    )
    password_hash = models.CharField(
        max_length=128,
        blank=True,
        help_text="Bcrypt hash of the password (if required)",
    )
    
    # Expiration and limits
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this share expires (null = no expiration)",
    )
    max_downloads = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of downloads allowed (null = unlimited)",
    )
    download_count = models.IntegerField(
        default=0,
        help_text="Current number of downloads",
    )
    
    # Revocation
    revoked = models.BooleanField(
        default=False,
        help_text="Whether this share has been revoked",
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this share was revoked",
    )
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_shares",
        help_text="User who revoked this share",
    )
    revoke_reason = models.TextField(
        blank=True,
        help_text="Reason for revocation",
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_shares",
        help_text="User who created this share",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "documents_external_shares"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "document"], name="doc_ext_fir_doc_idx"),
            models.Index(fields=["firm", "created_by"], name="doc_ext_fir_cre_idx"),
            models.Index(fields=["expires_at"], name="doc_ext_exp_idx"),
            models.Index(fields=["revoked"], name="doc_ext_rev_idx"),
        ]
    
    def __str__(self) -> str:
        return f"Share: {self.document.name} ({self.share_token})"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        # Generate share token on creation
        if not self.share_token:
            self.share_token = uuid.uuid4()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self) -> bool:
        """Check if the share has expired."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_download_limit_reached(self) -> bool:
        """Check if download limit has been reached."""
        if self.max_downloads is None:
            return False
        return self.download_count >= self.max_downloads
    
    @property
    def is_active(self) -> bool:
        """Check if the share is currently active and accessible."""
        return not self.revoked and not self.is_expired and not self.is_download_limit_reached
    
    def verify_password(self, password: str) -> bool:
        """
        Verify the provided password against the stored hash.
        
        Args:
            password: The password to verify
            
        Returns:
            True if password is correct, False otherwise
        """
        if not self.require_password:
            return True
        
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def set_password(self, password: str) -> None:
        """
        Set the password for this share.
        
        Args:
            password: The plaintext password to hash and store
        """
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        self.require_password = True
    
    def revoke(self, user: Any, reason: str = "") -> None:
        """
        Revoke this share.
        
        Args:
            user: The user revoking the share
            reason: Optional reason for revocation
        """
        self.revoked = True
        self.revoked_at = timezone.now()
        self.revoked_by = user
        self.revoke_reason = reason
        self.save(update_fields=["revoked", "revoked_at", "revoked_by", "revoke_reason", "updated_at"])
    
    def increment_download_count(self) -> None:
        """Increment the download counter."""
        self.download_count += 1
        self.save(update_fields=["download_count", "updated_at"])
    
    def clean(self) -> None:
        """Validate external share data."""
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Firm consistency
        if self.document_id and self.firm_id:
            if hasattr(self, "document") and self.document.firm_id != self.firm_id:
                errors["document"] = "Share firm must match document's firm."
        
        # Password validation
        if self.require_password and not self.password_hash:
            errors["password_hash"] = "Password hash is required when password protection is enabled."
        
        # Download limit validation
        if self.max_downloads is not None and self.max_downloads < 0:
            errors["max_downloads"] = "Max downloads must be non-negative."
        
        if errors:
            raise ValidationError(errors)


class SharePermission(models.Model):
    """
    Share permission configuration model (Task 3.10).
    
    Defines detailed permissions for external shares including
    print control, watermark settings, and other fine-grained controls.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="share_permissions",
        help_text="Firm (workspace) this permission belongs to",
    )
    
    # Associated share
    external_share = models.OneToOneField(
        ExternalShare,
        on_delete=models.CASCADE,
        related_name="permissions",
        help_text="The external share these permissions apply to",
    )
    
    # Permission flags
    allow_print = models.BooleanField(
        default=True,
        help_text="Allow printing the document",
    )
    allow_copy = models.BooleanField(
        default=True,
        help_text="Allow copying text from the document",
    )
    
    # Watermark settings
    apply_watermark = models.BooleanField(
        default=False,
        help_text="Whether to apply a watermark",
    )
    watermark_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Watermark text to display",
    )
    watermark_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional watermark settings (opacity, position, etc.)",
    )
    
    # IP restrictions
    allowed_ip_addresses = models.JSONField(
        default=list,
        blank=True,
        help_text="List of allowed IP addresses/ranges (empty = no restriction)",
    )
    
    # Email notifications
    notify_on_access = models.BooleanField(
        default=False,
        help_text="Send notification when document is accessed",
    )
    notification_emails = models.JSONField(
        default=list,
        blank=True,
        help_text="Email addresses to notify on access",
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "documents_share_permissions"
        indexes = [
            models.Index(fields=["firm", "external_share"], name="doc_sha_fir_ext_idx"),
        ]
    
    def __str__(self) -> str:
        return f"Permissions for {self.external_share.share_token}"
    
    def is_ip_allowed(self, ip_address: str) -> bool:
        """
        Check if an IP address is allowed to access the share.
        
        Supports both individual IP addresses and CIDR ranges.
        
        Args:
            ip_address: The IP address to check (e.g., "192.168.1.1")
            
        Returns:
            True if allowed (or no restrictions), False otherwise
            
        Examples:
            >>> perm.allowed_ip_addresses = ["192.168.1.1", "10.0.0.0/8"]
            >>> perm.is_ip_allowed("192.168.1.1")  # Exact match
            True
            >>> perm.is_ip_allowed("10.5.10.20")  # In CIDR range
            True
            >>> perm.is_ip_allowed("172.16.0.1")  # Not in list
            False
        """
        if not self.allowed_ip_addresses:
            return True
        
        try:
            # Parse the incoming IP address
            ip_obj = ipaddress.ip_address(ip_address)
        except ValueError:
            # Invalid IP address format
            return False
        
        # Check against each entry in allowed_ip_addresses
        for allowed_entry in self.allowed_ip_addresses:
            try:
                # Try to parse as CIDR network
                if "/" in allowed_entry:
                    network = ipaddress.ip_network(allowed_entry, strict=False)
                    if ip_obj in network:
                        return True
                else:
                    # Try exact IP match
                    allowed_ip = ipaddress.ip_address(allowed_entry)
                    if ip_obj == allowed_ip:
                        return True
            except ValueError:
                # Invalid entry in allowed_ip_addresses, skip it
                continue
        
        return False
    
    def clean(self) -> None:
        """Validate share permission data."""
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Firm consistency
        if self.external_share_id and self.firm_id:
            if hasattr(self, "external_share") and self.external_share.firm_id != self.firm_id:
                errors["external_share"] = "Permission firm must match share's firm."
        
        # Watermark validation
        if self.apply_watermark and not self.watermark_text:
            errors["watermark_text"] = "Watermark text is required when watermark is enabled."
        
        # Validate IP addresses and CIDR ranges
        if self.allowed_ip_addresses:
            invalid_ips = []
            for ip_entry in self.allowed_ip_addresses:
                try:
                    if "/" in ip_entry:
                        # Validate CIDR notation
                        ipaddress.ip_network(ip_entry, strict=False)
                    else:
                        # Validate IP address
                        ipaddress.ip_address(ip_entry)
                except ValueError:
                    invalid_ips.append(ip_entry)
            
            if invalid_ips:
                errors["allowed_ip_addresses"] = (
                    f"Invalid IP address or CIDR format: {', '.join(invalid_ips)}. "
                    "Use formats like '192.168.1.1' or '10.0.0.0/8'."
                )
        
        if errors:
            raise ValidationError(errors)


class ShareAccess(models.Model):
    """
    Share access tracking model (Task 3.10).
    
    Tracks all access attempts to external shares for audit and analytics.
    Records both successful and failed access attempts.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    ACTION_CHOICES = [
        ("view", "View"),
        ("download", "Download"),
        ("failed_password", "Failed Password"),
        ("failed_expired", "Failed - Expired"),
        ("failed_revoked", "Failed - Revoked"),
        ("failed_limit", "Failed - Download Limit"),
        ("failed_ip", "Failed - IP Restricted"),
    ]
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="share_accesses",
        help_text="Firm (workspace) this access belongs to",
    )
    
    # Associated share
    external_share = models.ForeignKey(
        ExternalShare,
        on_delete=models.CASCADE,
        related_name="access_logs",
        help_text="The external share being accessed",
    )
    
    # Access details
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Type of access action",
    )
    success = models.BooleanField(
        help_text="Whether the access was successful",
    )
    accessed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the access occurred",
    )
    
    # Request metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the request",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string",
    )
    referer = models.TextField(
        blank=True,
        help_text="HTTP referer",
    )
    
    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional access metadata",
    )
    
    # TIER 0: Manager (no firm_scoped needed - these are audit records)
    objects = models.Manager()
    
    class Meta:
        db_table = "documents_share_accesses"
        ordering = ["-accessed_at"]
        indexes = [
            models.Index(fields=["firm", "external_share", "-accessed_at"], name="doc_sha_fir_ext_acc_idx"),
            models.Index(fields=["firm", "action", "-accessed_at"], name="doc_sha_fir_act_acc_idx"),
            models.Index(fields=["ip_address", "-accessed_at"], name="doc_sha_ip_acc_idx"),
        ]
    
    def __str__(self) -> str:
        status = "Success" if self.success else "Failed"
        return f"{self.action} - {status} at {self.accessed_at}"
    
    @classmethod
    def log_access(
        cls,
        firm_id: int,
        external_share: ExternalShare,
        action: str,
        success: bool,
        ip_address: str | None = None,
        user_agent: str = "",
        referer: str = "",
        metadata: dict | None = None,
    ):
        """
        Convenience method to log a share access attempt.
        
        Usage:
            ShareAccess.log_access(
                firm_id=share.firm_id,
                external_share=share,
                action="download",
                success=True,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
            )
        """
        return cls.objects.create(
            firm_id=firm_id,
            external_share=external_share,
            action=action,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent[:1000] if user_agent else "",  # Truncate
            referer=referer[:1000] if referer else "",  # Truncate
            metadata=metadata or {},
        )


