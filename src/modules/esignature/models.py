"""Database models for e-signature integrations."""

from django.db import models
from django.utils import timezone

from modules.firm.models import Firm


class DocuSignConnection(models.Model):
    """
    DocuSign OAuth connection for a firm.
    
    Each firm can have one active DocuSign connection for e-signature workflows.
    Stores OAuth tokens and account information.
    """
    
    firm = models.OneToOneField(
        Firm,
        on_delete=models.CASCADE,
        related_name="docusign_connection",
        help_text="Firm that owns this DocuSign connection"
    )
    
    # OAuth credentials
    access_token = models.TextField(help_text="Encrypted OAuth access token")
    refresh_token = models.TextField(help_text="Encrypted OAuth refresh token")
    token_expires_at = models.DateTimeField(help_text="When the access token expires")
    
    # DocuSign account information
    account_id = models.CharField(max_length=255, help_text="DocuSign account ID")
    account_name = models.CharField(max_length=255, help_text="DocuSign account name")
    base_uri = models.URLField(help_text="DocuSign API base URL for this account")
    
    # Connection metadata
    is_active = models.BooleanField(default=True, help_text="Whether this connection is active")
    connected_at = models.DateTimeField(auto_now_add=True)
    connected_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="docusign_connections_created"
    )
    
    # Status tracking
    last_sync_at = models.DateTimeField(null=True, blank=True, help_text="Last successful API interaction")
    last_error = models.TextField(blank=True, help_text="Last error message, if any")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "esignature_docusign_connections"
        verbose_name = "DocuSign Connection"
        verbose_name_plural = "DocuSign Connections"
        indexes = [
            models.Index(fields=["firm", "is_active"]),
        ]
    
    def __str__(self):
        return f"DocuSign Connection for {self.firm.name}"
    
    def is_token_expired(self):
        """Check if access token is expired."""
        return timezone.now() >= self.token_expires_at


class Envelope(models.Model):
    """
    DocuSign envelope tracking.
    
    Represents a document envelope sent for signature.
    Tracks envelope status and links to proposals or contracts.
    """
    
    STATUS_CHOICES = [
        ("created", "Created"),
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("signed", "Signed"),
        ("completed", "Completed"),
        ("declined", "Declined"),
        ("voided", "Voided"),
        ("error", "Error"),
    ]
    
    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name="docusign_envelopes",
        help_text="Firm that owns this envelope"
    )
    
    connection = models.ForeignKey(
        DocuSignConnection,
        on_delete=models.CASCADE,
        related_name="envelopes",
        help_text="DocuSign connection used for this envelope"
    )
    
    # DocuSign envelope information
    envelope_id = models.CharField(max_length=255, unique=True, help_text="DocuSign envelope ID")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="created")
    
    # Linked entities (nullable to support both proposals and contracts)
    proposal = models.ForeignKey(
        "clients.Proposal",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="docusign_envelopes",
        help_text="Proposal this envelope is for"
    )
    
    contract = models.ForeignKey(
        "clients.Contract",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="docusign_envelopes",
        help_text="Contract this envelope is for"
    )
    
    # Metadata
    subject = models.CharField(max_length=255, help_text="Envelope email subject")
    message = models.TextField(blank=True, help_text="Envelope email message")
    
    # Recipient information (stored as JSON)
    recipients = models.JSONField(default=list, help_text="List of recipients")
    
    # Status tracking
    sent_at = models.DateTimeField(null=True, blank=True, help_text="When envelope was sent")
    delivered_at = models.DateTimeField(null=True, blank=True, help_text="When envelope was delivered")
    signed_at = models.DateTimeField(null=True, blank=True, help_text="When envelope was signed")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When envelope was completed")
    voided_at = models.DateTimeField(null=True, blank=True, help_text="When envelope was voided")
    voided_reason = models.TextField(blank=True, help_text="Reason for voiding")
    
    # Error tracking
    error_message = models.TextField(blank=True, help_text="Error message if status is error")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="docusign_envelopes_created"
    )
    
    class Meta:
        db_table = "esignature_envelopes"
        verbose_name = "Envelope"
        verbose_name_plural = "Envelopes"
        indexes = [
            models.Index(fields=["firm", "status"]),
            models.Index(fields=["envelope_id"]),
            models.Index(fields=["proposal"]),
            models.Index(fields=["contract"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            # Ensure envelope is linked to either proposal or contract, not both
            models.CheckConstraint(
                check=(
                    models.Q(proposal__isnull=False, contract__isnull=True) |
                    models.Q(proposal__isnull=True, contract__isnull=False)
                ),
                name="envelope_linked_to_one_entity"
            )
        ]
    
    def __str__(self):
        entity = self.proposal or self.contract
        entity_type = "Proposal" if self.proposal else "Contract"
        return f"Envelope {self.envelope_id} for {entity_type} ({self.status})"


class WebhookEvent(models.Model):
    """
    DocuSign webhook event log (SEC-1: Idempotency tracking).
    
    Stores webhook events received from DocuSign for debugging, audit trail,
    and idempotency checking to prevent duplicate processing.
    """
    
    # TIER 0: Firm tenancy (for idempotency queries)
    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name="docusign_webhook_events",
        help_text="Firm this webhook event belongs to"
    )
    
    envelope = models.ForeignKey(
        Envelope,
        on_delete=models.CASCADE,
        related_name="webhook_events",
        null=True,
        blank=True,
        help_text="Envelope this event is for (null if envelope not found)"
    )
    
    # DocuSign event tracking
    envelope_id = models.CharField(max_length=255, help_text="DocuSign envelope ID from webhook")
    event_id = models.CharField(
        max_length=255,
        help_text="DocuSign event ID (unique identifier from DocuSign webhook)"
    )
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Idempotency key for this webhook event"
    )
    event_type = models.CharField(max_length=100, help_text="Type of event (e.g., envelope-completed)")
    event_status = models.CharField(max_length=50, help_text="Status from event (e.g., completed)")
    
    # Raw webhook data
    payload = models.JSONField(help_text="Raw webhook payload")
    headers = models.JSONField(default=dict, help_text="Webhook request headers")
    
    # Processing status
    processed = models.BooleanField(default=False, help_text="Whether this event has been processed")
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, help_text="Error message if processing failed")
    
    received_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "esignature_webhook_events"
        verbose_name = "Webhook Event"
        verbose_name_plural = "Webhook Events"
        indexes = [
            models.Index(fields=["firm", "envelope_id"], name="esig_wh_fir_env_idx"),
            models.Index(fields=["envelope_id"], name="esig_wh_env_idx"),
            models.Index(fields=["received_at"], name="esig_wh_rcv_idx"),
            models.Index(fields=["processed"], name="esig_wh_pro_idx"),
            models.Index(fields=["event_id"], name="esig_wh_evt_id_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["event_id"],
                name="esignature_webhook_event_unique"
            )
        ]
        ordering = ["-received_at"]
    
    def __str__(self):
        return f"Webhook {self.event_type} for {self.envelope_id} at {self.received_at}"
