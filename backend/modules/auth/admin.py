"""
Sprint 1: Authentication Admin Configuration
"""

from django.contrib import admin
from modules.auth.models import SAMLConfiguration, UserMFAProfile


@admin.register(UserMFAProfile)
class UserMFAProfileAdmin(admin.ModelAdmin):
    """
    Sprint 1.12: Admin interface for User MFA profiles.
    """
    list_display = ["user", "phone_number", "sms_mfa_enabled"]
    list_filter = ["sms_mfa_enabled"]
    search_fields = ["user__username", "user__email", "phone_number"]
    raw_id_fields = ["user"]


@admin.register(SAMLConfiguration)
class SAMLConfigurationAdmin(admin.ModelAdmin):
    """
    Sprint 1.8: Admin interface for SAML configuration.
    """
    list_display = ["name", "sp_entity_id", "idp_entity_id", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "sp_entity_id", "idp_entity_id"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = [
        (
            "Basic Information",
            {
                "fields": ["name", "is_active"]
            }
        ),
        (
            "Service Provider (SP) Settings",
            {
                "fields": ["sp_entity_id", "sp_public_cert", "sp_private_key"],
                "description": "ConsultantPro acts as the Service Provider"
            }
        ),
        (
            "Identity Provider (IdP) Settings",
            {
                "fields": ["idp_entity_id", "idp_sso_url", "idp_slo_url", "idp_x509_cert"],
                "description": "Your enterprise IdP settings (Azure AD, Okta, etc.)"
            }
        ),
        (
            "Attribute Mapping",
            {
                "fields": ["attribute_mapping"],
                "description": "Map SAML assertion attributes to User fields"
            }
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"]
            }
        ),
    ]
