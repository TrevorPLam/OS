"""
Knowledge System Models (DOC-35.1).

Implements docs/03-reference/requirements/DOC-35.md: KNOWLEDGE_SYSTEM_SPEC.

Core models:
- KnowledgeItem: Articles, SOPs, training, KPIs, playbooks
- KnowledgeVersion: Version history for published items
- KnowledgeAttachment: Links to governed documents
- KnowledgeReview: Review approval records
"""

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from modules.firm.utils import FirmScopedManager


class KnowledgeItem(models.Model):
    """
    Knowledge article/manual/SOP/KPI definition (docs/03-reference/requirements/DOC-35.md section 2.1).

    Represents a versioned, governed knowledge artifact with publishing workflow.

    Invariants per docs/03-reference/requirements/DOC-35.md:
    - Published versions SHOULD be immutable; changes create new version
    - Deprecation must retain history
    - All transitions auditable
    """

    # Types per docs/03-reference/requirements/DOC-35.md section 2.1
    TYPE_SOP = "sop"
    TYPE_TRAINING = "training"
    TYPE_KPI = "kpi"
    TYPE_PLAYBOOK = "playbook"
    TYPE_TEMPLATE = "template"
    TYPE_CHOICES = [
        (TYPE_SOP, "Standard Operating Procedure"),
        (TYPE_TRAINING, "Training Manual"),
        (TYPE_KPI, "KPI Definition"),
        (TYPE_PLAYBOOK, "Playbook"),
        (TYPE_TEMPLATE, "Template/Checklist"),
    ]

    # Status workflow per docs/03-reference/requirements/DOC-35.md section 3
    STATUS_DRAFT = "draft"
    STATUS_IN_REVIEW = "in_review"
    STATUS_PUBLISHED = "published"
    STATUS_DEPRECATED = "deprecated"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_IN_REVIEW, "In Review"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_DEPRECATED, "Deprecated"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    # Content format per docs/03-reference/requirements/DOC-35.md section 2.1
    FORMAT_MARKDOWN = "markdown"
    FORMAT_RICH_TEXT = "rich_text"
    FORMAT_CHOICES = [
        (FORMAT_MARKDOWN, "Markdown"),
        (FORMAT_RICH_TEXT, "Rich Text"),
    ]

    # Access control per docs/03-reference/requirements/DOC-35.md section 4
    ACCESS_ALL_STAFF = "all_staff"
    ACCESS_MANAGER_PLUS = "manager_plus"
    ACCESS_ADMIN_ONLY = "admin_only"
    ACCESS_CHOICES = [
        (ACCESS_ALL_STAFF, "All Staff"),
        (ACCESS_MANAGER_PLUS, "Manager+"),
        (ACCESS_ADMIN_ONLY, "Admin Only"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="knowledge_items",
        help_text="Firm (workspace) this knowledge item belongs to",
    )

    # Core fields per docs/03-reference/requirements/DOC-35.md section 2.1
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    summary = models.TextField(help_text="Short summary for listings")
    content = models.TextField(help_text="Main content body")
    content_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default=FORMAT_MARKDOWN)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    version_number = models.IntegerField(default=1, help_text="Current version number")

    # Ownership and review
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_knowledge_items",
        help_text="Staff user who owns this item",
    )
    reviewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="KnowledgeReview",
        through_fields=("knowledge_item", "reviewer"),
        related_name="reviewed_knowledge_items",
        help_text="Staff users who can review this item",
    )

    # Tagging and categorization per docs/03-reference/requirements/DOC-35.md section 5
    tags = models.JSONField(default=list, blank=True, help_text="Tags for search and filtering")
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text="Category (SOP Library, Training, KPI Definitions, etc.)",
    )

    # Access control per docs/03-reference/requirements/DOC-35.md section 4
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_CHOICES,
        default=ACCESS_ALL_STAFF,
        help_text="Minimum role required to view",
    )

    # Publishing workflow timestamps per docs/03-reference/requirements/DOC-35.md section 2.1
    published_at = models.DateTimeField(null=True, blank=True, help_text="When this version was published")
    deprecated_at = models.DateTimeField(null=True, blank=True, help_text="When this item was deprecated")
    deprecation_reason = models.TextField(blank=True, help_text="Required when deprecating (docs/03-reference/requirements/DOC-35.md section 3)")

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_knowledge_items",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_knowledge_items",
    )

    # Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "knowledge_items"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="knowledge_fir_sta_idx"),
            models.Index(fields=["firm", "type"], name="knowledge_fir_typ_idx"),
            models.Index(fields=["firm", "owner"], name="knowledge_fir_own_idx"),
            models.Index(fields=["status", "published_at"], name="knowledge_sta_pub_idx"),
        ]
        unique_together = [["firm", "title", "version_number"]]  # Prevent duplicate titles in same version

    def __str__(self):
        return f"{self.get_type_display()}: {self.title} (v{self.version_number})"

    def clean(self):
        """Validate publishing workflow invariants (docs/03-reference/requirements/DOC-35.md section 2.1, 3)."""
        super().clean()

        # Deprecation must have reason
        if self.status == self.STATUS_DEPRECATED and not self.deprecation_reason:
            raise ValidationError("Deprecation reason is required when deprecating a knowledge item.")

        # Cannot unpublish (docs/03-reference/requirements/DOC-35.md: published versions immutable)
        if self.pk:
            old_instance = KnowledgeItem.objects.get(pk=self.pk)
            if old_instance.status == self.STATUS_PUBLISHED and self.status == self.STATUS_DRAFT:
                raise ValidationError(
                    "Cannot revert published item to draft. Create a new version instead (docs/03-reference/requirements/DOC-35.md section 2.1)."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def publish(self, published_by):
        """
        Publish this knowledge item (docs/03-reference/requirements/DOC-35.md section 3).

        Creates a version snapshot and makes item visible per access policy.
        Published versions are immutable per docs/03-reference/requirements/DOC-35.md section 2.1.
        """
        from datetime import datetime

        if self.status == self.STATUS_PUBLISHED:
            raise ValidationError("Item is already published")

        # Create version snapshot
        KnowledgeVersion.objects.create(
            firm=self.firm,
            knowledge_item=self,
            version_number=self.version_number,
            content_snapshot=self.content,
            content_format=self.content_format,
            change_notes=f"Published by {published_by.get_full_name()}",
            created_by=published_by,
        )

        # Update status
        self.status = self.STATUS_PUBLISHED
        self.published_at = datetime.now()
        self.updated_by = published_by
        self.save()

        # Create audit event
        from modules.firm.audit import AuditEvent

        AuditEvent.objects.create(
            firm=self.firm,
            actor=published_by,
            action="knowledge_item_published",
            object_id=self.id,
            object_type="KnowledgeItem",
            metadata={
                "title": self.title,
                "type": self.type,
                "version": self.version_number,
            },
        )

    def deprecate(self, deprecated_by, reason):
        """
        Deprecate this knowledge item (docs/03-reference/requirements/DOC-35.md section 3).

        Item remains searchable but marked deprecated.
        Deprecation reason required.
        """
        from datetime import datetime

        if self.status != self.STATUS_PUBLISHED:
            raise ValidationError("Only published items can be deprecated")

        if not reason:
            raise ValidationError("Deprecation reason is required (docs/03-reference/requirements/DOC-35.md section 3)")

        self.status = self.STATUS_DEPRECATED
        self.deprecated_at = datetime.now()
        self.deprecation_reason = reason
        self.updated_by = deprecated_by
        self.save()

        # Create audit event
        from modules.firm.audit import AuditEvent

        AuditEvent.objects.create(
            firm=self.firm,
            actor=deprecated_by,
            action="knowledge_item_deprecated",
            object_id=self.id,
            object_type="KnowledgeItem",
            metadata={
                "title": self.title,
                "reason": reason,
            },
        )

    def archive(self, archived_by):
        """
        Archive this knowledge item (docs/03-reference/requirements/DOC-35.md section 3).

        Hidden from default views but retained for history.
        """
        self.status = self.STATUS_ARCHIVED
        self.updated_by = archived_by
        self.save()

        # Create audit event
        from modules.firm.audit import AuditEvent

        AuditEvent.objects.create(
            firm=self.firm,
            actor=archived_by,
            action="knowledge_item_archived",
            object_id=self.id,
            object_type="KnowledgeItem",
            metadata={"title": self.title},
        )

    def create_new_version(self, updated_by, change_notes=""):
        """
        Create a new version of this knowledge item (docs/03-reference/requirements/DOC-35.md section 2.1).

        Published versions are immutable, so changes create new version.
        """
        if self.status != self.STATUS_PUBLISHED:
            raise ValidationError("Can only create new version from published item")

        new_item = KnowledgeItem.objects.create(
            firm=self.firm,
            type=self.type,
            title=self.title,
            summary=self.summary,
            content=self.content,
            content_format=self.content_format,
            status=self.STATUS_DRAFT,
            version_number=self.version_number + 1,
            owner=self.owner,
            tags=self.tags.copy() if self.tags else [],
            category=self.category,
            access_level=self.access_level,
            created_by=updated_by,
            updated_by=updated_by,
        )

        # Create audit event
        from modules.firm.audit import AuditEvent

        AuditEvent.objects.create(
            firm=self.firm,
            actor=updated_by,
            action="knowledge_item_version_created",
            object_id=new_item.id,
            object_type="KnowledgeItem",
            metadata={
                "title": self.title,
                "old_version": self.version_number,
                "new_version": new_item.version_number,
                "change_notes": change_notes,
            },
        )

        return new_item


class KnowledgeVersion(models.Model):
    """
    Version history for knowledge items (docs/03-reference/requirements/DOC-35.md section 2.2).

    Explicit version records for audit and rollback.
    Each publish creates a version snapshot.
    """

    firm = models.ForeignKey("firm.Firm", on_delete=models.CASCADE, related_name="knowledge_versions")
    knowledge_item = models.ForeignKey(KnowledgeItem, on_delete=models.CASCADE, related_name="versions")
    version_number = models.IntegerField()
    content_snapshot = models.TextField(help_text="Content at time of version")
    content_format = models.CharField(max_length=20, choices=KnowledgeItem.FORMAT_CHOICES)
    change_notes = models.TextField(blank=True, help_text="What changed in this version")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_knowledge_versions",
    )

    # Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "knowledge_versions"
        ordering = ["-version_number"]
        indexes = [
            models.Index(fields=["firm", "knowledge_item"], name="knowledge_ver_fir_kno_idx"),
            models.Index(fields=["knowledge_item", "-version_number"], name="knowledge_kno_ver_idx"),
        ]
        unique_together = [["knowledge_item", "version_number"]]

    def __str__(self):
        return f"{self.knowledge_item.title} v{self.version_number}"


class KnowledgeReview(models.Model):
    """
    Review approval records (docs/03-reference/requirements/DOC-35.md section 3).

    Tracks reviewer approval in publishing workflow.
    """

    DECISION_PENDING = "pending"
    DECISION_APPROVED = "approved"
    DECISION_REJECTED = "rejected"
    DECISION_CHOICES = [
        (DECISION_PENDING, "Pending"),
        (DECISION_APPROVED, "Approved"),
        (DECISION_REJECTED, "Rejected"),
    ]

    firm = models.ForeignKey("firm.Firm", on_delete=models.CASCADE, related_name="knowledge_reviews")
    knowledge_item = models.ForeignKey(KnowledgeItem, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="knowledge_reviews",
    )
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default=DECISION_PENDING)
    comments = models.TextField(blank=True)

    # Audit
    requested_at = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="requested_knowledge_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "knowledge_reviews"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["firm", "knowledge_item"], name="knowledge_rev_fir_kno_idx"),
            models.Index(fields=["reviewer", "decision"], name="knowledge_rev_dec_idx"),
        ]
        unique_together = [["knowledge_item", "reviewer"]]  # One review per reviewer per item

    def __str__(self):
        return f"Review: {self.knowledge_item.title} by {self.reviewer.get_full_name()}"

    def approve(self, comments=""):
        """Approve this knowledge item for publishing."""
        from datetime import datetime

        self.decision = self.DECISION_APPROVED
        self.comments = comments
        self.reviewed_at = datetime.now()
        self.save()

        # Create audit event
        from modules.firm.audit import AuditEvent

        AuditEvent.objects.create(
            firm=self.firm,
            actor=self.reviewer,
            action="knowledge_review_approved",
            object_id=self.knowledge_item.id,
            object_type="KnowledgeItem",
            metadata={
                "title": self.knowledge_item.title,
                "reviewer": self.reviewer.get_full_name(),
                "comments": comments,
            },
        )

    def reject(self, comments):
        """Reject this knowledge item."""
        from datetime import datetime

        if not comments:
            raise ValidationError("Comments required when rejecting")

        self.decision = self.DECISION_REJECTED
        self.comments = comments
        self.reviewed_at = datetime.now()
        self.save()

        # Create audit event
        from modules.firm.audit import AuditEvent

        AuditEvent.objects.create(
            firm=self.firm,
            actor=self.reviewer,
            action="knowledge_review_rejected",
            object_id=self.knowledge_item.id,
            object_type="KnowledgeItem",
            metadata={
                "title": self.knowledge_item.title,
                "reviewer": self.reviewer.get_full_name(),
                "comments": comments,
            },
        )


class KnowledgeAttachment(models.Model):
    """
    Links knowledge items to governed documents (docs/03-reference/requirements/DOC-35.md section 2.3).

    Attachments should be Documents in the governed document system.
    Can also reference templates, metrics, external links.
    """

    ATTACHMENT_TYPE_DOCUMENT = "document"
    ATTACHMENT_TYPE_TEMPLATE = "template"
    ATTACHMENT_TYPE_METRIC = "metric"
    ATTACHMENT_TYPE_EXTERNAL = "external"
    ATTACHMENT_TYPE_CHOICES = [
        (ATTACHMENT_TYPE_DOCUMENT, "Document"),
        (ATTACHMENT_TYPE_TEMPLATE, "Delivery Template"),
        (ATTACHMENT_TYPE_METRIC, "Metric Definition"),
        (ATTACHMENT_TYPE_EXTERNAL, "External Link"),
    ]

    firm = models.ForeignKey("firm.Firm", on_delete=models.CASCADE, related_name="knowledge_attachments")
    knowledge_item = models.ForeignKey(KnowledgeItem, on_delete=models.CASCADE, related_name="attachments")
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPE_CHOICES)

    # Polymorphic references (only one should be set based on attachment_type)
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Reference to governed document",
    )
    delivery_template = models.ForeignKey(
        "delivery.DeliveryTemplate",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Reference to delivery template",
    )
    external_url = models.URLField(blank=True, help_text="External link (allowed list policy)")
    description = models.CharField(max_length=255, blank=True, help_text="Optional description of attachment")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_knowledge_attachments",
    )

    # Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "knowledge_attachments"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["firm", "knowledge_item"], name="knowledge_att_fir_kno_idx"),
            models.Index(fields=["attachment_type"], name="knowledge_att_idx"),
        ]

    def __str__(self):
        return f"{self.knowledge_item.title} - {self.get_attachment_type_display()}"

    def clean(self):
        """Validate attachment references."""
        super().clean()

        # Ensure correct reference is set based on type
        if self.attachment_type == self.ATTACHMENT_TYPE_DOCUMENT and not self.document:
            raise ValidationError("Document reference required for document attachment type")
        elif self.attachment_type == self.ATTACHMENT_TYPE_TEMPLATE and not self.delivery_template:
            raise ValidationError("Delivery template reference required for template attachment type")
        elif self.attachment_type == self.ATTACHMENT_TYPE_EXTERNAL and not self.external_url:
            raise ValidationError("External URL required for external attachment type")
