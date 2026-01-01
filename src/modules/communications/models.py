"""
Communications Models (DOC-33.1 per docs/33 COMMUNICATIONS_SPEC)

Implements the communications domain with:
- Conversation: Thread model with visibility rules (internal_only | client_visible)
- Participant: Staff and portal user participants
- Message: Messages with type support (text, system_event, attachment, action)
- MessageAttachment: Link to governed Documents
- MessageRevision: Edit history preservation
- ConversationLink: Domain object associations

TIER 0: All communications belong to exactly one Firm for tenant isolation.
"""

from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class Conversation(models.Model):
    """
    Conversation (thread) model per docs/33 section 2.1.

    A Conversation is a thread of messages that can be:
    - internal_only: staff participants only
    - client_visible: includes portal participants

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    VISIBILITY_CHOICES = [
        ("internal_only", "Internal Only (Staff)"),
        ("client_visible", "Client Visible (Portal Access)"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("archived", "Archived"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="conversations",
        help_text="Firm (workspace) this conversation belongs to",
    )

    # Conversation metadata
    subject = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional subject line for the conversation",
    )
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default="internal_only",
        help_text="Visibility determines who can see this conversation",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    # Primary anchor (optional context link)
    primary_object_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of primary linked object (e.g., Account, Engagement)",
    )
    primary_object_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of primary linked object",
    )

    # Activity tracking
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Timestamp of the most recent message",
    )
    message_count = models.IntegerField(
        default=0,
        help_text="Total number of messages in this conversation",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_conversations",
        help_text="User who created this conversation",
    )
    correlation_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Correlation ID from creation request",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "communications_conversation"
        ordering = ["-last_message_at", "-created_at"]
        indexes = [
            models.Index(fields=["firm", "visibility", "-last_message_at"], name="communicat_fir_vis_las_idx"),
            models.Index(fields=["firm", "status", "-last_message_at"], name="communicat_fir_sta_las_idx"),
            models.Index(fields=["firm", "primary_object_type", "primary_object_id"], name="communicat_fir_pri_pri_idx"),
        ]

    def __str__(self) -> str:
        subject = self.subject or f"Conversation #{self.id}"
        return f"{subject} ({self.visibility})"

    def clean(self) -> None:
        """Validate conversation data integrity."""
        from django.core.exceptions import ValidationError

        errors = {}

        # internal_only conversations cannot have portal participants
        # (enforced in Participant model validation)

        if errors:
            raise ValidationError(errors)


class Participant(models.Model):
    """
    Participant model per docs/33 section 2.2.

    Participants can be:
    - StaffUser (participant_type='staff')
    - PortalIdentity (participant_type='portal', linked to Contact)

    Invariants:
    - internal_only conversations MUST NOT include portal participants
    - Adding/removing participants MUST be auditable
    """

    PARTICIPANT_TYPE_CHOICES = [
        ("staff", "Staff User"),
        ("portal", "Portal User"),
    ]

    ROLE_CHOICES = [
        ("member", "Member"),
        ("owner", "Owner"),
        ("moderator", "Moderator"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="conversation_participants",
    )

    # Conversation link
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participants",
    )

    # Participant identity
    participant_type = models.CharField(
        max_length=10,
        choices=PARTICIPANT_TYPE_CHOICES,
    )
    staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="conversation_participations",
        help_text="Staff user if participant_type='staff'",
    )
    portal_user_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Portal user ID if participant_type='portal'",
    )
    contact = models.ForeignKey(
        "clients.Contact",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="conversation_participations",
        help_text="Contact linked to portal user",
    )

    # Role
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="member",
    )

    # Membership status
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When participant left the conversation (null = still active)",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "communications_participant"
        indexes = [
            models.Index(fields=["firm", "conversation"], name="communicat_par_fir_con_idx"),
            models.Index(fields=["firm", "staff_user"], name="communicat_fir_sta_idx"),
            models.Index(fields=["firm", "portal_user_id"], name="communicat_fir_por_idx"),
        ]
        unique_together = [
            # A user can only be in a conversation once
            ["conversation", "staff_user"],
            ["conversation", "portal_user_id"],
        ]

    def __str__(self) -> str:
        if self.participant_type == "staff" and self.staff_user:
            return f"{self.staff_user} in {self.conversation}"
        return f"Portal User {self.portal_user_id} in {self.conversation}"

    @property
    def is_active(self) -> bool:
        """Check if participant is still active in the conversation."""
        return self.left_at is None

    def clean(self) -> None:
        """Validate participant data integrity."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Firm consistency
        if self.conversation_id and self.firm_id:
            if hasattr(self, "conversation") and self.conversation.firm_id != self.firm_id:
                errors["conversation"] = "Participant firm must match conversation's firm."

        # Participant type validation
        if self.participant_type == "staff" and not self.staff_user_id:
            errors["staff_user"] = "Staff user is required for staff participants."
        if self.participant_type == "portal" and not self.portal_user_id:
            errors["portal_user_id"] = "Portal user ID is required for portal participants."

        # Internal-only conversation cannot have portal participants
        if self.conversation_id and hasattr(self, "conversation"):
            if self.conversation.visibility == "internal_only" and self.participant_type == "portal":
                errors["participant_type"] = "Portal users cannot participate in internal-only conversations."

        if errors:
            raise ValidationError(errors)


class Message(models.Model):
    """
    Message model per docs/33 section 2.3.

    Messages are append-only by default. Edits/deletes preserve history.

    Message types:
    - text: Regular text message
    - system_event: System-generated notification
    - attachment: File attachment message
    - action: Action/task message
    """

    MESSAGE_TYPE_CHOICES = [
        ("text", "Text Message"),
        ("system_event", "System Event"),
        ("attachment", "Attachment"),
        ("action", "Action"),
    ]

    SENDER_TYPE_CHOICES = [
        ("staff", "Staff User"),
        ("portal", "Portal User"),
        ("system", "System"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="messages",
    )

    # Conversation link
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    # Sender information
    sender_type = models.CharField(
        max_length=10,
        choices=SENDER_TYPE_CHOICES,
    )
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_messages",
        help_text="Staff user who sent the message",
    )
    sender_portal_user_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Portal user ID if sender_type='portal'",
    )

    # Message content
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default="text",
    )
    body = models.TextField(
        blank=True,
        help_text="Message body (may be empty for attachment-only messages)",
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Bounded metadata (e.g., mentions, formatting)",
    )

    # Edit/delete tracking
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the message was last edited",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Soft delete timestamp (tombstone preserved)",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    correlation_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Correlation ID from request",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "communications_message"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["firm", "conversation", "created_at"], name="communicat_fir_con_cre_idx"),
            models.Index(fields=["firm", "sender_user", "-created_at"], name="communicat_fir_sen_use_idx"),
            models.Index(fields=["firm", "sender_portal_user_id", "-created_at"], name="communicat_fir_sen_por_idx"),
            models.Index(fields=["correlation_id"], name="communicat_cor_idx"),
        ]

    def __str__(self) -> str:
        return f"Message #{self.id} in {self.conversation}"

    @property
    def is_deleted(self) -> bool:
        """Check if message has been soft deleted."""
        return self.deleted_at is not None

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Update conversation statistics when message is saved."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.is_deleted:
            # Update conversation statistics
            self.conversation.message_count = self.conversation.messages.filter(
                deleted_at__isnull=True
            ).count()
            self.conversation.last_message_at = self.created_at
            self.conversation.save(update_fields=["message_count", "last_message_at"])

    def clean(self) -> None:
        """Validate message data integrity."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Firm consistency
        if self.conversation_id and self.firm_id:
            if hasattr(self, "conversation") and self.conversation.firm_id != self.firm_id:
                errors["conversation"] = "Message firm must match conversation's firm."

        # Sender validation
        if self.sender_type == "staff" and not self.sender_user_id:
            errors["sender_user"] = "Sender user is required for staff messages."
        if self.sender_type == "portal" and not self.sender_portal_user_id:
            errors["sender_portal_user_id"] = "Portal user ID is required for portal messages."

        if errors:
            raise ValidationError(errors)


class MessageAttachment(models.Model):
    """
    Message attachment model per docs/33 section 2.4.

    Attachments MUST be governed Documents.
    Links messages to Documents with attachment role.

    Constraints:
    - Portal user uploads route through governed upload flow
    - Attachment visibility matches conversation and document rules
    """

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="message_attachments",
    )

    # Links
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="message_attachments",
        help_text="The governed document that is attached",
    )

    # Metadata
    attached_at = models.DateTimeField(auto_now_add=True)
    attached_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="attached_documents",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "communications_message_attachment"
        indexes = [
            models.Index(fields=["firm", "message"], name="communicat_fir_mes_idx"),
            models.Index(fields=["firm", "document"], name="communicat_fir_doc_idx"),
        ]
        unique_together = [["message", "document"]]

    def __str__(self) -> str:
        return f"Attachment: {self.document.name} on Message #{self.message_id}"

    def clean(self) -> None:
        """Validate attachment data integrity."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Firm consistency
        if self.message_id and self.firm_id:
            if hasattr(self, "message") and self.message.firm_id != self.firm_id:
                errors["message"] = "Attachment firm must match message's firm."
        if self.document_id and self.firm_id:
            if hasattr(self, "document") and self.document.firm_id != self.firm_id:
                errors["document"] = "Attachment firm must match document's firm."

        if errors:
            raise ValidationError(errors)


class MessageRevision(models.Model):
    """
    Message revision history per docs/33 section 7.2.

    Preserves edit history for messages when edits are allowed.
    """

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="message_revisions",
    )

    # Message link
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="revisions",
    )

    # Revision details
    revision_number = models.IntegerField()
    body_snapshot = models.TextField(
        help_text="Content of the message at this revision",
    )
    edited_at = models.DateTimeField()
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="message_edits",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "communications_message_revision"
        ordering = ["-revision_number"]
        indexes = [
            models.Index(fields=["firm", "message", "-revision_number"], name="communicat_fir_mes_rev_idx"),
        ]
        unique_together = [["message", "revision_number"]]

    def __str__(self) -> str:
        return f"Revision {self.revision_number} of Message #{self.message_id}"


class ConversationLink(models.Model):
    """
    Conversation link model per docs/33 section 4.

    Links conversations to domain objects (Account, Engagement, etc.).
    A conversation MAY have multiple links but SHOULD have one primary anchor.
    """

    OBJECT_TYPE_CHOICES = [
        ("Account", "Account"),
        ("Engagement", "Engagement"),
        ("EngagementLine", "Engagement Line"),
        ("WorkItem", "Work Item"),
        ("Invoice", "Invoice"),
        ("Appointment", "Appointment"),
        ("Project", "Project"),
        ("Document", "Document"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="conversation_links",
    )

    # Links
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="links",
    )

    # Target object
    object_type = models.CharField(
        max_length=50,
        choices=OBJECT_TYPE_CHOICES,
    )
    object_id = models.IntegerField()

    # Link metadata
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the primary anchor for the conversation",
    )
    linked_at = models.DateTimeField(auto_now_add=True)
    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_conversation_links",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "communications_conversation_link"
        indexes = [
            models.Index(fields=["firm", "conversation"], name="communicat_lnk_fir_con_idx"),
            models.Index(fields=["firm", "object_type", "object_id"], name="communicat_fir_obj_obj_idx"),
        ]
        unique_together = [["conversation", "object_type", "object_id"]]

    def __str__(self) -> str:
        return f"Link: {self.conversation} -> {self.object_type}#{self.object_id}"

    def clean(self) -> None:
        """Validate link data integrity."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Firm consistency
        if self.conversation_id and self.firm_id:
            if hasattr(self, "conversation") and self.conversation.firm_id != self.firm_id:
                errors["conversation"] = "Link firm must match conversation's firm."

        if errors:
            raise ValidationError(errors)
