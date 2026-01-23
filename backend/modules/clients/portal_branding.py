"""
Client Portal Branding and Customization (PORTAL-1 through PORTAL-4).

Implements:
- PORTAL-1: Custom domain support with SSL and DNS configuration
- PORTAL-2: Visual branding (logo, colors, fonts)
- PORTAL-3: White-label login customization
- PORTAL-4: Custom email branding

TIER 0: All portal branding belongs to exactly one Firm for tenant isolation.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator
from django.db import models
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class PortalBranding(models.Model):
    """
    Client portal branding and customization settings.

    Allows firms to white-label their client portal with custom domain,
    branding, and email templates.

    TIER 0: Belongs to exactly one Firm.
    """

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.OneToOneField(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="portal_branding",
        help_text="Firm this portal branding belongs to",
    )

    # PORTAL-1: Custom Domain Support
    custom_domain = models.CharField(
        max_length=255,
        blank=True,
        help_text="Custom domain for portal (e.g., 'portal.yourcompany.com')",
        validators=[
            RegexValidator(
                regex=r"^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$",
                message="Enter a valid domain name (lowercase, no protocol)",
            )
        ],
    )
    custom_domain_verified = models.BooleanField(
        default=False,
        help_text="Whether custom domain DNS verification is complete",
    )
    custom_domain_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When domain was verified",
    )
    ssl_enabled = models.BooleanField(
        default=False,
        help_text="Whether SSL certificate is provisioned for custom domain",
    )
    ssl_certificate_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="SSL certificate identifier (e.g., AWS ACM certificate ARN)",
    )
    dns_verification_token = models.CharField(
        max_length=255,
        blank=True,
        help_text="DNS verification token (TXT record value)",
    )
    dns_cname_target = models.CharField(
        max_length=255,
        blank=True,
        help_text="CNAME target for custom domain (platform subdomain)",
    )

    # PORTAL-2: Visual Branding
    logo_url = models.URLField(
        blank=True,
        help_text="URL to company logo for portal header",
        validators=[URLValidator()],
    )
    logo_file = models.FileField(
        upload_to="portal/logos/",
        blank=True,
        null=True,
        help_text="Uploaded logo file",
    )
    favicon_url = models.URLField(
        blank=True,
        help_text="URL to favicon",
    )
    primary_color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text="Primary brand color (hex format: #RRGGBB)",
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message="Enter a valid hex color code (e.g., #3B82F6)",
            )
        ],
    )
    secondary_color = models.CharField(
        max_length=7,
        default="#10B981",
        help_text="Secondary brand color (hex format: #RRGGBB)",
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message="Enter a valid hex color code",
            )
        ],
    )
    accent_color = models.CharField(
        max_length=7,
        default="#F59E0B",
        help_text="Accent color for highlights (hex format: #RRGGBB)",
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message="Enter a valid hex color code",
            )
        ],
    )
    background_color = models.CharField(
        max_length=7,
        default="#FFFFFF",
        help_text="Background color (hex format: #RRGGBB)",
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message="Enter a valid hex color code",
            )
        ],
    )
    text_color = models.CharField(
        max_length=7,
        default="#1F2937",
        help_text="Primary text color (hex format: #RRGGBB)",
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message="Enter a valid hex color code",
            )
        ],
    )
    font_family = models.CharField(
        max_length=100,
        default="Inter, system-ui, sans-serif",
        help_text="Font family for portal (CSS font-family value)",
    )
    custom_css = models.TextField(
        blank=True,
        help_text="Custom CSS for additional styling",
    )

    # PORTAL-3: White-Label Login
    login_page_title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Custom title for login page (defaults to firm name)",
    )
    login_page_subtitle = models.CharField(
        max_length=255,
        blank=True,
        help_text="Subtitle/tagline for login page",
    )
    login_background_image = models.URLField(
        blank=True,
        help_text="Background image URL for login page",
    )
    login_background_file = models.FileField(
        upload_to="portal/login-backgrounds/",
        blank=True,
        null=True,
        help_text="Uploaded login background image",
    )
    welcome_message = models.TextField(
        blank=True,
        help_text="Welcome message shown after login",
    )
    remove_platform_branding = models.BooleanField(
        default=False,
        help_text="Remove 'Powered by ConsultantPro' branding from portal",
    )
    custom_login_url_slug = models.SlugField(
        max_length=100,
        blank=True,
        help_text="Custom URL slug for portal login (e.g., 'client-portal')",
    )

    # PORTAL-4: Custom Email Branding
    email_from_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="From name for portal emails (defaults to firm name)",
    )
    email_from_address = models.EmailField(
        blank=True,
        help_text="From email address for portal emails (must be verified)",
    )
    email_from_address_verified = models.BooleanField(
        default=False,
        help_text="Whether email address is verified for sending",
    )
    email_reply_to = models.EmailField(
        blank=True,
        help_text="Reply-to email address",
    )
    email_physical_address = models.TextField(
        blank=True,
        help_text="Physical mailing address for compliance footers",
    )
    email_header_logo_url = models.URLField(
        blank=True,
        help_text="Logo URL for email header",
    )
    email_header_color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text="Header background color for emails (hex format)",
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message="Enter a valid hex color code",
            )
        ],
    )
    email_footer_text = models.TextField(
        blank=True,
        help_text="Custom footer text for emails (HTML allowed)",
    )
    email_signature = models.TextField(
        blank=True,
        help_text="Email signature for portal emails",
    )
    email_custom_html_header = models.TextField(
        blank=True,
        help_text="Custom HTML for email header",
    )
    email_custom_html_footer = models.TextField(
        blank=True,
        help_text="Custom HTML for email footer",
    )

    # Portal Features
    enable_custom_branding = models.BooleanField(
        default=True,
        help_text="Enable custom branding features",
    )
    enable_custom_domain = models.BooleanField(
        default=False,
        help_text="Enable custom domain (requires Enterprise plan)",
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_portal_brandings",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="updated_portal_brandings",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "clients_portal_branding"
        verbose_name = "Portal Branding"
        verbose_name_plural = "Portal Brandings"
        indexes = [
            models.Index(fields=["firm"], name="portal_brand_firm_idx"),
            models.Index(fields=["custom_domain"], name="portal_brand_domain_idx"),
        ]

    def __str__(self):
        return f"Portal Branding for {self.firm.name}"

    def clean(self):
        """Validate portal branding configuration."""
        errors = {}

        # Custom domain validation
        if self.custom_domain:
            # Ensure domain is lowercase
            self.custom_domain = self.custom_domain.lower().strip()

            # Cannot use platform domain
            if "consultantpro" in self.custom_domain:
                errors["custom_domain"] = "Cannot use platform domain"

            # Cannot set as verified without verification
            if self.custom_domain_verified and not self.custom_domain_verified_at:
                self.custom_domain_verified_at = timezone.now()

        # SSL requires domain
        if self.ssl_enabled and not self.custom_domain:
            errors["ssl_enabled"] = "SSL requires a custom domain"

        # Color validation (ensure valid hex)
        color_fields = [
            "primary_color",
            "secondary_color",
            "accent_color",
            "background_color",
            "text_color",
            "email_header_color",
        ]
        for field in color_fields:
            color = getattr(self, field, "")
            if color and not color.startswith("#"):
                errors[field] = f"{field} must start with #"

        # Email validation
        if self.email_from_address and not self.email_from_name:
            self.email_from_name = self.firm.name

        if errors:
            raise ValidationError(errors)

    def verify_custom_domain(self, user=None):
        """
        Verify custom domain DNS configuration.

        Returns:
            bool: True if verification successful
        """
        # Tracked in TODO: T-011 (Implement Portal Branding Infrastructure Integrations - DNS)
        # 1. Check for DNS TXT record with verification token
        # 2. Check for CNAME record pointing to platform
        # 3. Update verification status

        self.custom_domain_verified = True
        self.custom_domain_verified_at = timezone.now()
        self.updated_by = user
        self.save()
        return True

    def provision_ssl_certificate(self):
        """
        Provision SSL certificate for custom domain.

        Returns:
            str: Certificate ID
        """
        # Tracked in TODO: T-011 (Implement Portal Branding Infrastructure Integrations - SSL)
        # 1. Request certificate for custom domain
        # 2. Store certificate ID
        # 3. Enable SSL

        pass

    def generate_dns_verification_token(self):
        """Generate unique DNS verification token."""
        import hashlib
        import secrets

        if not self.dns_verification_token:
            # Generate unique token
            random_string = secrets.token_urlsafe(32)
            self.dns_verification_token = hashlib.sha256(
                f"{self.firm.id}:{self.custom_domain}:{random_string}".encode()
            ).hexdigest()[:32]
            self.save()

        return self.dns_verification_token

    def get_effective_logo_url(self):
        """Get logo URL (prefer uploaded file over URL)."""
        if self.logo_file:
            return self.logo_file.url
        return self.logo_url or ""

    def get_effective_email_logo_url(self):
        """Get email logo URL (prefer email-specific, fall back to general logo)."""
        return self.email_header_logo_url or self.get_effective_logo_url()

    def get_css_variables(self):
        """
        Generate CSS variables for theming.

        Returns:
            dict: CSS variable definitions
        """
        return {
            "--primary-color": self.primary_color,
            "--secondary-color": self.secondary_color,
            "--accent-color": self.accent_color,
            "--background-color": self.background_color,
            "--text-color": self.text_color,
            "--font-family": self.font_family,
        }

    def get_email_template_context(self):
        """
        Get context for email template rendering.

        Returns:
            dict: Template context
        """
        return {
            "firm_name": self.firm.name,
            "from_name": self.email_from_name or self.firm.name,
            "logo_url": self.get_effective_email_logo_url(),
            "header_color": self.email_header_color,
            "footer_text": self.email_footer_text,
            "signature": self.email_signature,
            "custom_header": self.email_custom_html_header,
            "custom_footer": self.email_custom_html_footer,
        }

    def render_email_html(self, body_html: str) -> str:
        """
        Render branded HTML email content with optional custom header/footer.
        """
        context = self.get_email_template_context()
        header = context["custom_header"] or (
            f"<div style=\"background:{context['header_color']};padding:16px;text-align:left;\">"
            f"<img src=\"{context['logo_url']}\" alt=\"{context['firm_name']}\" "
            "style=\"height:32px;\" />"
            "</div>"
            if context["logo_url"]
            else f"<div style=\"background:{context['header_color']};padding:16px;color:#fff;\">"
            f"{context['firm_name']}</div>"
        )
        footer = context["custom_footer"] or (
            f"<div style=\"padding:16px;color:#6b7280;font-size:12px;\">"
            f"{context['footer_text'] or ''}"
            f"{'<br>' + context['signature'] if context['signature'] else ''}"
            "</div>"
        )
        return f"{header}<div style=\"padding:16px;\">{body_html}</div>{footer}"


class DomainVerificationRecord(models.Model):
    """
    Tracks DNS verification attempts for custom domains.

    Used for auditing domain verification process.
    """

    branding = models.ForeignKey(
        PortalBranding,
        on_delete=models.CASCADE,
        related_name="verification_records",
    )
    domain = models.CharField(max_length=255)
    verification_type = models.CharField(
        max_length=20,
        choices=[
            ("txt", "TXT Record"),
            ("cname", "CNAME Record"),
        ],
        default="txt",
    )
    expected_value = models.CharField(max_length=255)
    actual_value = models.CharField(max_length=255, blank=True)
    verified = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "clients_domain_verification"
        ordering = ["-checked_at"]
        indexes = [
            models.Index(fields=["branding", "-checked_at"], name="domain_ver_brand_idx"),
        ]

    def __str__(self):
        return f"Verification for {self.domain} ({self.verification_type})"
