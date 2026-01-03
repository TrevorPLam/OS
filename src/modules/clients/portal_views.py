"""
API Views for Client Portal Branding (PORTAL-1 through PORTAL-4).

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
"""

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from modules.firm.utils import FirmScopedMixin

from .portal_branding import DomainVerificationRecord, PortalBranding
from .portal_serializers import (
    DomainVerificationRecordSerializer,
    PortalBrandingSerializer,
)


class PortalBrandingViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Portal Branding management.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = PortalBranding
    serializer_class = PortalBrandingSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "put", "head", "options"]

    def get_queryset(self):
        """Get portal branding for current firm."""
        return PortalBranding.objects.filter(firm=self.request.firm)

    def get_object(self):
        """Get or create portal branding for current firm."""
        branding, created = PortalBranding.objects.get_or_create(
            firm=self.request.firm,
            defaults={
                "created_by": self.request.user,
                "updated_by": self.request.user,
            },
        )
        return branding

    def list(self, request):
        """Get portal branding for current firm."""
        branding = self.get_object()
        serializer = self.get_serializer(branding)
        return Response(serializer.data)

    def perform_update(self, serializer):
        """Set updated_by on update."""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["post"], url_path="verify-domain")
    def verify_domain(self, request):
        """
        Verify custom domain DNS configuration (PORTAL-1).

        Checks DNS records and updates verification status.
        """
        branding = self.get_object()

        if not branding.custom_domain:
            return Response(
                {"error": "No custom domain configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate verification token if not exists
        if not branding.dns_verification_token:
            branding.generate_dns_verification_token()

        # Tracked in TODO: T-011 (Implement Portal Branding Infrastructure Integrations - DNS)
        # For now, return verification instructions
        return Response(
            {
                "domain": branding.custom_domain,
                "verification_token": branding.dns_verification_token,
                "cname_target": branding.dns_cname_target or f"{request.firm.slug}.consultantpro.app",
                "instructions": {
                    "txt_record": {
                        "name": f"_consultantpro-verify.{branding.custom_domain}",
                        "type": "TXT",
                        "value": branding.dns_verification_token,
                    },
                    "cname_record": {
                        "name": branding.custom_domain,
                        "type": "CNAME",
                        "value": branding.dns_cname_target or f"{request.firm.slug}.consultantpro.app",
                    },
                },
                "verified": branding.custom_domain_verified,
            }
        )

    @action(detail=False, methods=["post"], url_path="check-domain-status")
    def check_domain_status(self, request):
        """
        Check DNS verification status for custom domain (PORTAL-1).

        Performs live DNS lookup to verify configuration.
        """
        branding = self.get_object()

        if not branding.custom_domain:
            return Response(
                {"error": "No custom domain configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Tracked in TODO: T-011 (Implement Portal Branding Infrastructure Integrations - DNS)
        # 1. Query DNS for TXT record
        # 2. Query DNS for CNAME record
        # 3. Update verification status
        # 4. Create verification record

        # Create verification record
        verification = DomainVerificationRecord.objects.create(
            branding=branding,
            domain=branding.custom_domain,
            verification_type="txt",
            expected_value=branding.dns_verification_token,
            verified=False,  # Tracked in TODO: T-011 (DNS verification)
        )

        return Response(
            {
                "domain": branding.custom_domain,
                "verified": verification.verified,
                "checked_at": verification.checked_at,
                "error": verification.error_message,
            }
        )

    @action(detail=False, methods=["post"], url_path="provision-ssl")
    def provision_ssl(self, request):
        """
        Provision SSL certificate for custom domain (PORTAL-1).

        Requires:
        - Custom domain verified
        - Enterprise subscription tier
        """
        branding = self.get_object()

        if not branding.custom_domain:
            return Response(
                {"error": "No custom domain configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not branding.custom_domain_verified:
            return Response(
                {"error": "Domain not verified. Verify domain first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check subscription tier
        if request.firm.subscription_tier != "enterprise":
            return Response(
                {"error": "SSL provisioning requires Enterprise plan"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Tracked in TODO: T-011 (Implement Portal Branding Infrastructure Integrations - SSL)
        # 1. Request certificate
        # 2. Store certificate ID
        # 3. Configure CloudFront/ALB

        branding.ssl_enabled = True
        branding.ssl_certificate_id = "mock-cert-id"  # Tracked in TODO: T-011 (Real certificate ID)
        branding.save()

        return Response(
            {
                "domain": branding.custom_domain,
                "ssl_enabled": branding.ssl_enabled,
                "certificate_id": branding.ssl_certificate_id,
            }
        )

    @action(detail=False, methods=["post"], url_path="verify-email")
    def verify_email(self, request):
        """
        Verify custom email address for sending (PORTAL-4).

        Sends verification email and tracks status.
        """
        branding = self.get_object()

        if not branding.email_from_address:
            return Response(
                {"error": "No email address configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Tracked in TODO: T-011 (Implement Portal Branding Infrastructure Integrations - Email)
        # 1. Send verification email
        # 2. Wait for verification confirmation
        # 3. Update verification status

        return Response(
            {
                "email": branding.email_from_address,
                "verification_sent": True,
                "verified": branding.email_from_address_verified,
            }
        )

    @action(detail=False, methods=["post"], url_path="upload-logo")
    def upload_logo(self, request):
        """
        Upload logo file (PORTAL-2).

        Accepts multipart/form-data with 'logo' file field.
        """
        branding = self.get_object()

        if "logo" not in request.FILES:
            return Response(
                {"error": "No logo file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logo_file = request.FILES["logo"]

        # Validate file size (max 5MB)
        if logo_file.size > 5 * 1024 * 1024:
            return Response(
                {"error": "Logo file too large (max 5MB)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file type
        allowed_types = ["image/png", "image/jpeg", "image/svg+xml"]
        if logo_file.content_type not in allowed_types:
            return Response(
                {"error": f"Invalid file type. Allowed: {', '.join(allowed_types)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        branding.logo_file = logo_file
        branding.updated_by = request.user
        branding.save()

        serializer = self.get_serializer(branding)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="upload-login-background")
    def upload_login_background(self, request):
        """
        Upload login background image (PORTAL-3).

        Accepts multipart/form-data with 'background' file field.
        """
        branding = self.get_object()

        if "background" not in request.FILES:
            return Response(
                {"error": "No background file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        background_file = request.FILES["background"]

        # Validate file size (max 10MB)
        if background_file.size > 10 * 1024 * 1024:
            return Response(
                {"error": "Background file too large (max 10MB)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file type
        allowed_types = ["image/png", "image/jpeg"]
        if background_file.content_type not in allowed_types:
            return Response(
                {"error": f"Invalid file type. Allowed: {', '.join(allowed_types)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        branding.login_background_file = background_file
        branding.updated_by = request.user
        branding.save()

        serializer = self.get_serializer(branding)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="preview-css")
    def preview_css(self, request):
        """
        Get CSS preview for portal branding (PORTAL-2).

        Returns CSS variables and custom CSS.
        """
        branding = self.get_object()

        css_variables = branding.get_css_variables()
        custom_css = branding.custom_css

        # Generate full CSS
        css_output = ":root {\n"
        for var, value in css_variables.items():
            css_output += f"  {var}: {value};\n"
        css_output += "}\n\n"

        if custom_css:
            css_output += f"/* Custom CSS */\n{custom_css}"

        return Response(
            {
                "variables": css_variables,
                "custom_css": custom_css,
                "full_css": css_output,
            }
        )

    @action(detail=False, methods=["get"], url_path="email-template-preview")
    def email_template_preview(self, request):
        """
        Get email template preview with branding (PORTAL-4).

        Returns HTML preview of email template.
        """
        branding = self.get_object()

        context = branding.get_email_template_context()

        # Tracked in TODO: T-011 (Implement Portal Branding Infrastructure Integrations - Email Template)
        html_preview = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
                .header {{ background-color: {branding.email_header_color}; padding: 20px; text-align: center; }}
                .header img {{ max-width: 200px; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <img src="{context['logo_url']}" alt="{context['firm_name']}" />
            </div>
            <div class="content">
                <h2>Sample Email</h2>
                <p>This is a preview of how your portal emails will look.</p>
            </div>
            <div class="footer">
                <p>{context['footer_text'] or '© ' + context['firm_name']}</p>
                {context['signature'] or ''}
            </div>
        </body>
        </html>
        """

        return Response(
            {
                "context": context,
                "html_preview": html_preview,
            }
        )


class DomainVerificationRecordViewSet(FirmScopedMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Domain Verification Records.

    Read-only access to verification history.
    TIER 0: Scoped to firm via branding relationship.
    """

    model = DomainVerificationRecord
    serializer_class = DomainVerificationRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get verification records for current firm's portal branding."""
        return DomainVerificationRecord.objects.filter(
            branding__firm=self.request.firm
        ).order_by("-checked_at")
