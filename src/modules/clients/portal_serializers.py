"""
DRF serializers for Client Portal Branding (PORTAL-1 through PORTAL-4).
"""

from rest_framework import serializers

from .portal_branding import DomainVerificationRecord, PortalBranding


class PortalBrandingSerializer(serializers.ModelSerializer):
    """Serializer for PortalBranding model."""

    effective_logo_url = serializers.SerializerMethodField()
    effective_email_logo_url = serializers.SerializerMethodField()
    css_variables = serializers.SerializerMethodField()

    class Meta:
        model = PortalBranding
        fields = [
            "id",
            # PORTAL-1: Custom Domain
            "custom_domain",
            "custom_domain_verified",
            "custom_domain_verified_at",
            "ssl_enabled",
            "dns_verification_token",
            "dns_cname_target",
            # PORTAL-2: Visual Branding
            "logo_url",
            "logo_file",
            "favicon_url",
            "primary_color",
            "secondary_color",
            "accent_color",
            "background_color",
            "text_color",
            "font_family",
            "custom_css",
            # PORTAL-3: White-Label Login
            "login_page_title",
            "login_page_subtitle",
            "login_background_image",
            "login_background_file",
            "welcome_message",
            "remove_platform_branding",
            "custom_login_url_slug",
            # PORTAL-4: Custom Emails
            "email_from_name",
            "email_from_address",
            "email_from_address_verified",
            "email_reply_to",
            "email_physical_address",
            "email_header_logo_url",
            "email_header_color",
            "email_footer_text",
            "email_signature",
            "email_custom_html_header",
            "email_custom_html_footer",
            # Features
            "enable_custom_branding",
            "enable_custom_domain",
            # Computed fields
            "effective_logo_url",
            "effective_email_logo_url",
            "css_variables",
            # Audit
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "custom_domain_verified",
            "custom_domain_verified_at",
            "ssl_enabled",
            "dns_verification_token",
            "dns_cname_target",
            "email_from_address_verified",
            "effective_logo_url",
            "effective_email_logo_url",
            "css_variables",
            "created_at",
            "updated_at",
        ]

    def get_effective_logo_url(self, obj):
        """Get effective logo URL."""
        return obj.get_effective_logo_url()

    def get_effective_email_logo_url(self, obj):
        """Get effective email logo URL."""
        return obj.get_effective_email_logo_url()

    def get_css_variables(self, obj):
        """Get CSS variables for theming."""
        return obj.get_css_variables()


class DomainVerificationRecordSerializer(serializers.ModelSerializer):
    """Serializer for DomainVerificationRecord model."""

    class Meta:
        model = DomainVerificationRecord
        fields = [
            "id",
            "domain",
            "verification_type",
            "expected_value",
            "actual_value",
            "verified",
            "error_message",
            "checked_at",
        ]
        read_only_fields = [
            "id",
            "actual_value",
            "verified",
            "error_message",
            "checked_at",
        ]
