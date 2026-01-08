import hashlib
import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


class EmailOptInRequest(models.Model):
    """
    Double opt-in request for email marketing (GDPR-2).

    Tracks confirmation tokens and audit details for opt-in workflows.
    """

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager
from .contacts import Contact
from .consents import ConsentRecord


class EmailOptInRequest(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    requested_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="When the confirmation link expires")
    confirmed_at = models.DateTimeField(null=True, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_opt_in_requests",
        help_text="User who initiated the opt-in request",
    )
    source = models.CharField(max_length=100, blank=True, help_text="Source of opt-in (e.g., signup_form)")
    source_url = models.URLField(blank=True, help_text="URL where opt-in was requested")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    consent_text = models.TextField(blank=True, help_text="Consent text shown to the contact")
    consent_version = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "clients_email_opt_in_requests"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["contact", "-requested_at"], name="clients_optin_contact_idx"),
            models.Index(fields=["token"], name="clients_optin_token_idx"),
            models.Index(fields=["expires_at"], name="clients_optin_exp_idx"),
        ]

    def __str__(self):
        return f"Opt-in request for {self.contact.email} ({self.requested_at.date()})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_confirmed(self) -> bool:
        return self.confirmed_at is not None

    @classmethod
    def create_request(
        cls,
        contact,
        *,
        requested_by=None,
        source="double_opt_in",
        source_url="",
        ip_address=None,
        user_agent="",
        consent_text="",
        consent_version="",
        expiry_days=14,
    ):
        """Create a double opt-in request and mark the contact unconfirmed."""
        if contact.status != Contact.STATUS_UNCONFIRMED:
            contact.change_status(
                Contact.STATUS_UNCONFIRMED,
                reason="Double opt-in requested",
                changed_by=requested_by,
            )
        contact.opt_out_marketing = True
        contact.save(
            update_fields=[
                "status",
                "status_changed_at",
                "status_changed_by",
                "status_reason",
                "is_active",
                "opt_out_marketing",
                "updated_at",
            ]
        )

        return cls.objects.create(
            contact=contact,
            expires_at=timezone.now() + timedelta(days=expiry_days),
            requested_by=requested_by,
            source=source,
            source_url=source_url,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_text=consent_text,
            consent_version=consent_version,
        )

    def confirm(self, *, actor=None, ip_address=None, user_agent="") -> bool:
        """Confirm opt-in, grant consent, and activate contact."""
        if self.is_expired or self.is_confirmed:
            return False

        self.confirmed_at = timezone.now()
        self.save(update_fields=["confirmed_at"])

        self.contact.confirm_email(changed_by=actor)
        self.contact.opt_out_marketing = False
        self.contact.save(
            update_fields=[
                "status",
                "status_changed_at",
                "status_changed_by",
                "status_reason",
                "is_active",
                "opt_out_marketing",
                "updated_at",
            ]
        )

        ConsentRecord = globals()["ConsentRecord"]
        self.contact.grant_consent(
            consent_type=ConsentRecord.CONSENT_TYPE_EMAIL,
            source="double_opt_in",
            consent_text=self.consent_text,
            consent_version=self.consent_version,
            consent_method=ConsentRecord.CONSENT_METHOD_EXPRESS,
            source_url=self.source_url,
            ip_address=ip_address,
            user_agent=user_agent,
            actor=actor,
            data_categories=[ConsentRecord.DATA_CATEGORY_CONTACT],
        )
        self.contact.grant_consent(
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            source="double_opt_in",
            consent_text=self.consent_text,
            consent_version=self.consent_version,
            consent_method=ConsentRecord.CONSENT_METHOD_EXPRESS,
            source_url=self.source_url,
            ip_address=ip_address,
            user_agent=user_agent,
            actor=actor,
            data_categories=[ConsentRecord.DATA_CATEGORY_CONTACT],
        )

        return True


class EmailUnsubscribeToken(models.Model):
    """Unsubscribe token for email compliance (SPAM-1)."""

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="unsubscribe_tokens",
        help_text="Contact for the unsubscribe token",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=100, blank=True, help_text="Source of unsubscribe link")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = "clients_email_unsubscribe_tokens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["contact", "-created_at"], name="clients_unsub_contact_idx"),
            models.Index(fields=["token"], name="clients_unsub_token_idx"),
        ]

    def __str__(self):
        return f"Unsubscribe token for {self.contact.email}"

    @property
    def is_used(self) -> bool:
        return self.unsubscribed_at is not None

    @classmethod
    def create_token(
        cls,
        contact,
        *,
        source="unsubscribe_link",
        ip_address=None,
        user_agent="",
    ):
        return cls.objects.create(
            contact=contact,
            source=source,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def mark_unsubscribed(self, *, actor=None, ip_address=None, user_agent="") -> bool:
        if self.is_used:
            return False

        self.unsubscribed_at = timezone.now()
        self.save(update_fields=["unsubscribed_at"])

        self.contact.mark_as_unsubscribed(reason="Unsubscribed via link", changed_by=actor)
        self.contact.save(
            update_fields=[
                "status",
                "status_changed_at",
                "status_changed_by",
                "status_reason",
                "is_active",
                "opt_out_marketing",
                "updated_at",
            ]
        )

        ConsentRecord = globals()["ConsentRecord"]
        self.contact.revoke_consent(
            consent_type=ConsentRecord.CONSENT_TYPE_EMAIL,
            source="unsubscribe_link",
            reason="Unsubscribed via link",
            ip_address=ip_address,
            user_agent=user_agent,
            actor=actor,
        )
        self.contact.revoke_consent(
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            source="unsubscribe_link",
            reason="Unsubscribed via link",
            ip_address=ip_address,
            user_agent=user_agent,
            actor=actor,
        )

        return True

    # CRM-INT-4: Consent tracking helper methods
    def has_consent(self, consent_type):
        """
        Check if contact has current consent for a specific type.
        
        Args:
            consent_type: Consent type to check (use ConsentRecord.CONSENT_TYPE_* constants)
        
        Returns:
            bool: True if contact has active consent, False otherwise
        
        Note:
            ConsentRecord is defined later in this module. We use globals() to access it
            at runtime, which is safe because this method is only called after the module
            is fully loaded. This avoids circular import issues.
        """
        # Access ConsentRecord dynamically (defined later in this file)
        ConsentRecord = globals()['ConsentRecord']
        status = ConsentRecord.get_current_consent(self, consent_type)
        return status["has_consent"]
    
    def grant_consent(
        self,
        consent_type,
        source,
        legal_basis="consent",
        data_categories=None,
        consent_text="",
        consent_version="",
        consent_method=None,
        source_url="",
        ip_address=None,
        user_agent="",
        actor=None,
        metadata=None
    ):
        """
        Grant consent for this contact.
        
        Creates a new consent record with action=GRANTED.
        
        Args:
            consent_type: Type of consent (use ConsentRecord.CONSENT_TYPE_* constants)
            source: Source of consent (e.g., 'signup_form', 'email_campaign')
            legal_basis: Legal basis for processing (default: 'consent')
            data_categories: List of data categories (default: empty list)
            consent_text: The exact consent text shown to user
            consent_version: Version of the consent text
            consent_method: Express or implied consent
            source_url: URL where consent was captured
            ip_address: IP address from which consent was given
            user_agent: User agent string
            actor: User who created this record (if staff action)
            metadata: Additional metadata dict
        
        Returns:
            ConsentRecord: The created consent record
        """
        # ConsentRecord is defined later in this file, so we need to access it dynamically
        ConsentRecord = globals()['ConsentRecord']
        return ConsentRecord.objects.create(
            contact=self,
            consent_type=consent_type,
            action=ConsentRecord.ACTION_GRANTED,
            legal_basis=legal_basis,
            data_categories=data_categories or [],
            consent_text=consent_text,
            consent_version=consent_version,
            consent_method=consent_method,
            source=source,
            source_url=source_url,
            ip_address=ip_address,
            user_agent=user_agent,
            actor=actor,
            metadata=metadata or {}
        )
    
    def revoke_consent(
        self,
        consent_type,
        source,
        reason="",
        ip_address=None,
        user_agent="",
        actor=None,
        metadata=None
    ):
        """
        Revoke consent for this contact.
        
        Creates a new consent record with action=REVOKED.
        
        Args:
            consent_type: Type of consent to revoke
            source: Source of revocation (e.g., 'unsubscribe_link', 'portal_settings')
            reason: Reason for revocation (stored in notes)
            ip_address: IP address from which consent was revoked
            user_agent: User agent string
            actor: User who created this record (if staff action)
            metadata: Additional metadata dict
        
        Returns:
            ConsentRecord: The created consent record
        """
        # ConsentRecord is defined later in this file, so we need to access it dynamically
        ConsentRecord = globals()['ConsentRecord']
        return ConsentRecord.objects.create(
            contact=self,
            consent_type=consent_type,
            action=ConsentRecord.ACTION_REVOKED,
            source=source,
            ip_address=ip_address,
            user_agent=user_agent,
            actor=actor,
            metadata=metadata or {},
            notes=reason
        )
    
    def get_consent_status(self):
        """
        Get current consent status for all consent types.
        
        Returns:
            dict: Dictionary mapping consent types to their current status
                {
                    'marketing': {'has_consent': bool, 'timestamp': datetime, ...},
                    'email': {'has_consent': bool, 'timestamp': datetime, ...},
                    ...
                }
        """
        # ConsentRecord is defined later in this file, so we need to access it dynamically
        ConsentRecord = globals()['ConsentRecord']
        status = {}
        for consent_type, _ in ConsentRecord.CONSENT_TYPE_CHOICES:
            status[consent_type] = ConsentRecord.get_current_consent(self, consent_type)
        return status

    def clean(self):
        """
        Validate Contact data integrity.

        Validates:
        - Portal user consistency: portal_user.client == self.client
        - Only one primary contact per client
        """
        from django.core.exceptions import ValidationError

        errors = {}

        # Portal user consistency
        if self.portal_user_id and self.client_id:
            if hasattr(self, "portal_user") and self.portal_user.client_id != self.client_id:
                errors["portal_user"] = "Contact's portal user must belong to the same client."

        # Ensure only one primary contact per client
        if self.is_primary_contact and self.client_id:
            existing_primary = (
                Contact.objects.filter(client=self.client, is_primary_contact=True).exclude(pk=self.pk).first()
            )
            if existing_primary:
                errors["is_primary_contact"] = (
                    f"Client already has a primary contact: {existing_primary.full_name}"
                )

        if errors:
            raise ValidationError(errors)


