"""
Advanced Access Controls (SEC-3).

Implements:
- Dynamic watermarking (username, IP, timestamp)
- View-only mode (no download, print, copy)
- IP whitelisting for sensitive operations
- Device trust/registration system

SECURITY REQUIREMENTS:
- Prevent unauthorized data exfiltration
- Track document access
- Control access by IP and device
- Forensic traceability
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont


class IPWhitelist(models.Model):
    """
    IP whitelist for sensitive operations.
    
    Restricts certain operations to whitelisted IP addresses.
    """
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='ip_whitelists',
        help_text='Firm this whitelist belongs to'
    )
    
    # IP Configuration
    ip_address = models.GenericIPAddressField(
        help_text='IP address to whitelist'
    )
    
    ip_range = models.CharField(
        max_length=50,
        blank=True,
        help_text='IP range in CIDR notation (e.g., 192.168.1.0/24)'
    )
    
    # Scope
    applies_to = models.CharField(
        max_length=50,
        choices=[
            ('all', 'All Operations'),
            ('break_glass', 'Break-Glass Access'),
            ('admin', 'Admin Operations'),
            ('sensitive_documents', 'Sensitive Documents'),
            ('bulk_operations', 'Bulk Operations'),
        ],
        default='all',
        help_text='What operations does this whitelist apply to?'
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text='Description of why this IP is whitelisted'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ip_whitelists'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Expiration
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this whitelist entry expires (null = never)'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text='Is this whitelist entry active?'
    )
    
    class Meta:
        db_table = 'security_ip_whitelists'
        indexes = [
            models.Index(fields=['firm', 'applies_to', 'is_active']),
            models.Index(fields=['ip_address', 'is_active']),
        ]
        unique_together = [('firm', 'ip_address', 'applies_to')]
    
    def __str__(self):
        return f"{self.ip_address} ({self.get_applies_to_display()}) - {self.firm.name}"
    
    def is_expired(self):
        """Check if whitelist entry is expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @classmethod
    def is_ip_whitelisted(cls, firm, ip_address, operation='all'):
        """
        Check if IP is whitelisted for operation.
        
        Args:
            firm: Firm instance
            ip_address: IP address to check
            operation: Operation to check (default: 'all')
        
        Returns:
            bool: True if whitelisted
        """
        # Check exact IP match
        exact_match = cls.objects.filter(
            firm=firm,
            ip_address=ip_address,
            applies_to__in=[operation, 'all'],
            is_active=True
        ).exclude(
            expires_at__lte=timezone.now()
        ).exists()
        
        if exact_match:
            return True
        
        # Check IP range match (CIDR)
        # Placeholder: would need IP range matching library
        # import ipaddress
        # ranges = cls.objects.filter(
        #     firm=firm,
        #     applies_to__in=[operation, 'all'],
        #     is_active=True,
        #     ip_range__isnull=False
        # ).exclude(expires_at__lte=timezone.now())
        #
        # for range_entry in ranges:
        #     if ipaddress.ip_address(ip_address) in ipaddress.ip_network(range_entry.ip_range):
        #         return True
        
        return False


class TrustedDevice(models.Model):
    """
    Trusted device registration for enhanced security.
    
    Tracks devices that users have registered as trusted.
    """
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='trusted_devices',
        help_text='Firm this device belongs to'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trusted_devices',
        help_text='User who owns this device'
    )
    
    # Device Identification
    device_id = models.CharField(
        max_length=255,
        unique=True,
        help_text='Unique device identifier (fingerprint)'
    )
    
    device_name = models.CharField(
        max_length=255,
        help_text='User-friendly device name (e.g., "John\'s MacBook Pro")'
    )
    
    # Device Details
    user_agent = models.TextField(
        help_text='User agent string'
    )
    
    browser = models.CharField(
        max_length=100,
        blank=True,
        help_text='Browser name'
    )
    
    os = models.CharField(
        max_length=100,
        blank=True,
        help_text='Operating system'
    )
    
    # Trust Status
    is_trusted = models.BooleanField(
        default=False,
        help_text='Is this device trusted?'
    )
    
    trust_level = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Verification'),
            ('basic', 'Basic Trust'),
            ('full', 'Full Trust'),
        ],
        default='pending',
        help_text='Level of trust for this device'
    )
    
    # Verification
    verification_code = models.CharField(
        max_length=100,
        blank=True,
        help_text='Verification code sent to user'
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When device was verified'
    )
    
    # Timestamps
    first_seen_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When device was first seen'
    )
    
    last_seen_at = models.DateTimeField(
        auto_now=True,
        help_text='When device was last used'
    )
    
    # Revocation
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When device trust was revoked'
    )
    
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_devices',
        help_text='Who revoked device trust'
    )
    
    revocation_reason = models.TextField(
        blank=True,
        help_text='Why device trust was revoked'
    )
    
    class Meta:
        db_table = 'security_trusted_devices'
        indexes = [
            models.Index(fields=['firm', 'user', 'is_trusted']),
            models.Index(fields=['device_id']),
            models.Index(fields=['user', 'last_seen_at']),
        ]
    
    def __str__(self):
        return f"{self.device_name} ({self.user.email}) - {self.trust_level}"
    
    def generate_verification_code(self):
        """Generate verification code for device."""
        self.verification_code = secrets.token_urlsafe(32)
        self.save(update_fields=['verification_code'])
        return self.verification_code
    
    def verify(self, code):
        """Verify device with code."""
        if self.verification_code == code:
            self.verified_at = timezone.now()
            self.is_trusted = True
            self.trust_level = 'full'
            self.save(update_fields=['verified_at', 'is_trusted', 'trust_level'])
            return True
        return False
    
    def revoke(self, revoked_by, reason=''):
        """Revoke device trust."""
        self.is_trusted = False
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by
        self.revocation_reason = reason
        self.save(update_fields=['is_trusted', 'revoked_at', 'revoked_by', 'revocation_reason'])
    
    @classmethod
    def get_or_create_device(cls, firm, user, device_fingerprint, user_agent, device_name=''):
        """
        Get or create trusted device.
        
        Args:
            firm: Firm instance
            user: User instance
            device_fingerprint: Unique device fingerprint
            user_agent: User agent string
            device_name: User-friendly device name
        
        Returns:
            Tuple[TrustedDevice, bool]: (device, created)
        """
        device_id = hashlib.sha256(f"{firm.id}:{user.id}:{device_fingerprint}".encode()).hexdigest()
        
        device, created = cls.objects.get_or_create(
            device_id=device_id,
            defaults={
                'firm': firm,
                'user': user,
                'device_name': device_name or f'Device {device_id[:8]}',
                'user_agent': user_agent,
            }
        )
        
        return device, created


class DocumentAccessControl(models.Model):
    """
    Access control settings for documents.
    
    Controls how documents can be accessed (view-only, watermarking, etc.).

    Meta-commentary:
    - **Current Status:** Model captures view-only, watermark, IP, and device access flags.
    - **Follow-up (T-065):** Wire enforcement for watermarking and IP restrictions in download/view endpoints.
    - **Assumption:** Document delivery layer consults this model before serving content.
    - **Missing:** Enforcement logic for watermarking and trusted-device checks.
    - **Limitation:** Flags are stored but not enforced automatically in views/services.
    """
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='document_access_controls',
        help_text='Firm this control belongs to'
    )
    
    document = models.OneToOneField(
        'documents.Document',
        on_delete=models.CASCADE,
        related_name='access_control',
        help_text='Document these controls apply to'
    )
    
    # View-Only Mode
    view_only = models.BooleanField(
        default=False,
        help_text='Restrict to view-only (no download, print, copy)'
    )
    
    disable_download = models.BooleanField(
        default=False,
        help_text='Disable download button'
    )
    
    disable_print = models.BooleanField(
        default=False,
        help_text='Disable print functionality'
    )
    
    disable_copy = models.BooleanField(
        default=False,
        help_text='Disable text selection and copy'
    )
    
    # Watermarking
    enable_watermark = models.BooleanField(
        default=False,
        help_text='Apply dynamic watermark to document'
    )
    
    watermark_text = models.CharField(
        max_length=255,
        blank=True,
        help_text='Custom watermark text (placeholders: {username}, {email}, {ip}, {timestamp})'
    )
    
    watermark_opacity = models.FloatField(
        default=0.3,
        help_text='Watermark opacity (0.0-1.0)'
    )
    
    watermark_position = models.CharField(
        max_length=20,
        choices=[
            ('center', 'Center'),
            ('diagonal', 'Diagonal'),
            ('header', 'Header'),
            ('footer', 'Footer'),
        ],
        default='diagonal',
        help_text='Watermark position'
    )
    
    # IP Restrictions
    require_ip_whitelist = models.BooleanField(
        default=False,
        help_text='Require whitelisted IP to access'
    )
    
    # Device Trust
    require_trusted_device = models.BooleanField(
        default=False,
        help_text='Require verified/trusted device to access'
    )
    
    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_document_access_controls'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents_access_controls'
        indexes = [
            models.Index(fields=['firm', 'view_only']),
            models.Index(fields=['firm', 'enable_watermark']),
        ]
    
    def __str__(self):
        controls = []
        if self.view_only:
            controls.append('view-only')
        if self.enable_watermark:
            controls.append('watermarked')
        if self.require_ip_whitelist:
            controls.append('IP-restricted')
        if self.require_trusted_device:
            controls.append('device-restricted')
        
        return f"Document {self.document_id}: {', '.join(controls) if controls else 'no restrictions'}"


class WatermarkService:
    """
    Service for applying dynamic watermarks to documents.
    """
    
    @staticmethod
    def generate_watermark_text(template: str, user, ip_address: str) -> str:
        """
        Generate watermark text from template.
        
        Args:
            template: Watermark template with placeholders
            user: User instance
            ip_address: IP address
        
        Returns:
            Rendered watermark text
        """
        return template.format(
            username=user.get_full_name() or user.email,
            email=user.email,
            ip=ip_address,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    
    @staticmethod
    def apply_watermark_to_image(image_path: str, watermark_text: str,
                                 position: str = 'diagonal',
                                 opacity: float = 0.3) -> str:
        """
        Apply watermark to image.
        
        Args:
            image_path: Path to image file
            watermark_text: Text to watermark
            position: Watermark position
            opacity: Watermark opacity (0.0-1.0)
        
        Returns:
            Path to watermarked image
        """
        # Open image
        img = Image.open(image_path)
        
        # Create watermark layer
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        # Calculate font size (2% of image height)
        font_size = max(20, int(img.height * 0.02))
        
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', font_size)
        except:
            font = ImageFont.load_default()
        
        # Calculate text size
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position watermark
        if position == 'center':
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2
        elif position == 'diagonal':
            # Rotate and position diagonally
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2
            # Rotation would be done via PIL rotate transform
        elif position == 'header':
            x = (img.width - text_width) // 2
            y = 20
        else:  # footer
            x = (img.width - text_width) // 2
            y = img.height - text_height - 20
        
        # Draw watermark
        color = (255, 255, 255, int(255 * opacity))
        draw.text((x, y), watermark_text, font=font, fill=color)
        
        # Composite watermark onto image
        watermarked = Image.alpha_composite(img.convert('RGBA'), watermark)
        
        # Save watermarked image
        output_path = image_path.replace('.', '_watermarked.')
        watermarked.save(output_path)
        
        return output_path
    
    @staticmethod
    def apply_watermark_to_pdf(pdf_path: str, watermark_text: str,
                               position: str = 'diagonal',
                               opacity: float = 0.3) -> str:
        """
        Apply watermark to PDF.
        
        Args:
            pdf_path: Path to PDF file
            watermark_text: Text to watermark
            position: Watermark position
            opacity: Watermark opacity (0.0-1.0)
        
        Returns:
            Path to watermarked PDF
        """
        # Placeholder: would use PyPDF2 or reportlab to add watermark
        # from PyPDF2 import PdfReader, PdfWriter
        # from reportlab.pdfgen import canvas
        # from reportlab.lib.pagesizes import letter
        
        output_path = pdf_path.replace('.pdf', '_watermarked.pdf')
        
        # Implementation would:
        # 1. Create watermark overlay PDF with reportlab
        # 2. Merge watermark onto each page with PyPDF2
        # 3. Save watermarked PDF
        
        return output_path


def check_ip_access(firm, ip_address, operation='all'):
    """
    Check if IP address is allowed for operation.
    
    Args:
        firm: Firm instance
        ip_address: IP address to check
        operation: Operation to check
    
    Returns:
        bool: True if allowed
    
    Raises:
        PermissionDenied: If IP not whitelisted and whitelist required
    """
    from django.core.exceptions import PermissionDenied
    
    # Check if operation requires whitelist
    # Placeholder: would check firm settings
    requires_whitelist = False  # Would check firm.security_settings.require_ip_whitelist
    
    if requires_whitelist:
        if not IPWhitelist.is_ip_whitelisted(firm, ip_address, operation):
            raise PermissionDenied(f"IP address {ip_address} is not whitelisted for {operation}")
    
    return True


def check_device_trust(firm, user, device_fingerprint):
    """
    Check if device is trusted.
    
    Args:
        firm: Firm instance
        user: User instance
        device_fingerprint: Device fingerprint
    
    Returns:
        Tuple[bool, TrustedDevice]: (is_trusted, device)
    """
    device_id = hashlib.sha256(f"{firm.id}:{user.id}:{device_fingerprint}".encode()).hexdigest()
    
    try:
        device = TrustedDevice.objects.get(
            device_id=device_id,
            is_trusted=True,
            revoked_at__isnull=True
        )
        return True, device
    except TrustedDevice.DoesNotExist:
        return False, None


def enforce_view_only_mode(request, document):
    """
    Enforce view-only mode restrictions on document access.
    
    Args:
        request: HTTP request
        document: Document instance
    
    Returns:
        dict: Access control settings for frontend
    """
    try:
        access_control = document.access_control
    except DocumentAccessControl.DoesNotExist:
        # No restrictions
        return {
            'view_only': False,
            'can_download': True,
            'can_print': True,
            'can_copy': True,
            'watermark': None
        }
    
    # Build access control response
    result = {
        'view_only': access_control.view_only,
        'can_download': not access_control.disable_download,
        'can_print': not access_control.disable_print,
        'can_copy': not access_control.disable_copy,
        'watermark': None
    }
    
    # Add watermark if enabled
    if access_control.enable_watermark:
        watermark_text = WatermarkService.generate_watermark_text(
            access_control.watermark_text or '{username} - {email} - {ip} - {timestamp}',
            request.user,
            request.META.get('REMOTE_ADDR', 'unknown')
        )
        
        result['watermark'] = {
            'text': watermark_text,
            'position': access_control.watermark_position,
            'opacity': access_control.watermark_opacity
        }
    
    return result
