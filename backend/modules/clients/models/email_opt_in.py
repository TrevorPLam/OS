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
from .contacts import Contact
from .consents import ConsentRecord


class EmailOptInRequest(models.Model):
    """
    Double opt-in request for email marketing (GDPR-2).

    Tracks confirmation tokens and audit details for opt-in workflows.
    """

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="email_opt_in_requests",
        help_text="Contact requesting opt-in",
    )
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

