"""
Sprint 1: Authentication Models

Models for OAuth, SAML, and MFA configuration.
"""

from django.conf import settings
from django.db import models


class UserMFAProfile(models.Model):
    """
    Sprint 1.12: User MFA Profile
    
    Extends User model with MFA-related fields.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mfa_profile",
        help_text="Link to Django User"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number for SMS-based MFA"
    )
    sms_mfa_enabled = models.BooleanField(
        default=False,
        help_text="Whether SMS-based MFA is enabled"
    )
    
    class Meta:
        verbose_name = "User MFA Profile"
        verbose_name_plural = "User MFA Profiles"
    
    def __str__(self):
        return f"MFA Profile for {self.user.username}"


class SAMLConfiguration(models.Model):
    """
    Sprint 1.8: SAML IdP Configuration Model
    
    Stores SAML Identity Provider metadata and Service Provider settings.
    Allows dynamic SAML configuration without code changes.
    """
    name = models.CharField(max_length=255, help_text="Friendly name for this SAML configuration")
    
    # Service Provider (SP) settings
    sp_entity_id = models.CharField(max_length=500, help_text="Service Provider Entity ID (URL)")
    sp_public_cert = models.TextField(blank=True, help_text="SP X.509 public certificate (PEM format)")
    sp_private_key = models.TextField(blank=True, help_text="SP private key (PEM format)")
    
    # Identity Provider (IdP) settings
    idp_entity_id = models.CharField(max_length=500, help_text="Identity Provider Entity ID")
    idp_sso_url = models.URLField(help_text="IdP Single Sign-On URL")
    idp_slo_url = models.URLField(blank=True, help_text="IdP Single Logout URL")
    idp_x509_cert = models.TextField(help_text="IdP X.509 certificate (PEM format)")
    
    # Sprint 1.9: Attribute mapping configuration
    attribute_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text="Map SAML attributes to User model fields. Example: {'email': 'mail', 'first_name': 'givenName'}"
    )
    
    is_active = models.BooleanField(default=True, help_text="Only one configuration can be active at a time")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SAML Configuration"
        verbose_name_plural = "SAML Configurations"
        ordering = ["-is_active", "-created_at"]
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
    
    def save(self, *args, **kwargs):
        # Ensure only one active configuration
        if self.is_active:
            SAMLConfiguration.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
