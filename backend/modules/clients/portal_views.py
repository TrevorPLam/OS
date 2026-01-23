"""
API Views for Client Portal Branding (PORTAL-1 through PORTAL-4).

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
"""

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
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


def _dns_lookup(name: str, record_type: str) -> list[str]:
    import time
    import requests

    last_error = None
    for attempt in range(3):
        try:
            response = requests.get(
                "https://cloudflare-dns.com/dns-query",
                params={"name": name, "type": record_type},
                headers={"Accept": "application/dns-json"},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            answers = payload.get("Answer", [])
            return [answer.get("data", "") for answer in answers if answer.get("data")]
        except Exception as exc:
            last_error = exc
            time.sleep(1 + attempt)
    raise last_error


def _acm_client():
    import boto3

    region = getattr(settings, "AWS_REGION", None) or getattr(settings, "AWS_DEFAULT_REGION", None) or "us-east-1"
    return boto3.client("acm", region_name=region)


def _ses_client():
    import boto3

    region = getattr(settings, "AWS_REGION", None) or getattr(settings, "AWS_DEFAULT_REGION", None) or "us-east-1"
    return boto3.client("ses", region_name=region)


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

        return Response(
            {
                "domain": branding.custom_domain,
                "verification_token": branding.dns_verification_token,
                "cname_target": branding.dns_cname_target or f"{request.firm.slug}.ubos.app",
                "instructions": {
                    "txt_record": {
                        "name": f"_ubos-verify.{branding.custom_domain}",
                        "type": "TXT",
                        "value": branding.dns_verification_token,
                    },
                    "cname_record": {
                        "name": branding.custom_domain,
                        "type": "CNAME",
                        "value": branding.dns_cname_target or f"{request.firm.slug}.ubos.app",
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

        txt_record_name = f"_ubos-verify.{branding.custom_domain}"
        cname_target = branding.dns_cname_target or f"{request.firm.slug}.ubos.app"

        txt_verified = False
        cname_verified = False
        txt_values = []
        cname_values = []
        error_message = ""

        try:
            txt_values = _dns_lookup(txt_record_name, "TXT")
            cname_values = _dns_lookup(branding.custom_domain, "CNAME")

            txt_verified = branding.dns_verification_token in [
                value.strip('"') for value in txt_values
            ]
            cname_verified = any(cname_target.rstrip(".") in value.rstrip(".") for value in cname_values)
        except Exception as exc:
            error_message = str(exc)

        DomainVerificationRecord.objects.create(
            branding=branding,
            domain=branding.custom_domain,
            verification_type="txt",
            expected_value=branding.dns_verification_token,
            actual_value=", ".join(txt_values),
            verified=txt_verified,
            error_message=error_message,
        )
        DomainVerificationRecord.objects.create(
            branding=branding,
            domain=branding.custom_domain,
            verification_type="cname",
            expected_value=cname_target,
            actual_value=", ".join(cname_values),
            verified=cname_verified,
            error_message=error_message,
        )

        branding.custom_domain_verified = txt_verified and cname_verified
        if branding.custom_domain_verified:
            branding.custom_domain_verified_at = timezone.now()
        branding.save(update_fields=["custom_domain_verified", "custom_domain_verified_at", "updated_at"])

        return Response(
            {
                "domain": branding.custom_domain,
                "verified": branding.custom_domain_verified,
                "checked_at": timezone.now(),
                "txt_verified": txt_verified,
                "cname_verified": cname_verified,
                "txt_records": txt_values,
                "cname_records": cname_values,
                "error": error_message,
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

        last_error = None
        for attempt in range(3):
            try:
                client = _acm_client()
                response = client.request_certificate(
                    DomainName=branding.custom_domain,
                    ValidationMethod="DNS",
                )
                certificate_arn = response.get("CertificateArn")
                branding.ssl_certificate_id = certificate_arn or ""
                branding.ssl_enabled = bool(certificate_arn)
                branding.save(update_fields=["ssl_certificate_id", "ssl_enabled", "updated_at"])
                last_error = None
                break
            except Exception as exc:
                last_error = exc

        if last_error:
            return Response(
                {"error": f"SSL provisioning failed: {last_error}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

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

        last_error = None
        for attempt in range(3):
            try:
                client = _ses_client()
                client.verify_email_identity(EmailAddress=branding.email_from_address)
                last_error = None
                break
            except Exception as exc:
                last_error = exc

        if last_error:
            return Response(
                {"error": f"Email verification failed: {last_error}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

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
