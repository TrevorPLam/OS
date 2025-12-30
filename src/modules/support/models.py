"""
Support Models: Ticket, SLA, Survey, SurveyResponse.

Implements HubSpot Service Hub-like functionality:
- Help desk ticketing system
- SLA tracking (response and resolution times)
- Customer feedback surveys
- NPS (Net Promoter Score) tracking

TIER 0: All support entities MUST belong to exactly one Firm for tenant isolation.
"""

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from datetime import timedelta

from modules.firm.utils import FirmScopedManager


class SLAPolicy(models.Model):
    """
    SLA Policy definition (response and resolution time targets).

    Defines service level agreements for ticket handling based on priority.
    Tracks targets for first response and resolution times.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    PRIORITY_CHOICES = [
        ("critical", "Critical"),
        ("high", "High"),
        ("normal", "Normal"),
        ("low", "Low"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="sla_policies",
        help_text="Firm this SLA policy belongs to",
    )

    # Policy identification
    name = models.CharField(max_length=255, help_text="SLA policy name")
    description = models.TextField(blank=True, help_text="Policy description")
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        help_text="Ticket priority this SLA applies to",
    )

    # Response time targets (in minutes)
    first_response_minutes = models.IntegerField(
        help_text="Target time for first response (minutes)",
        validators=[MinValueValidator(1)],
    )

    # Resolution time targets (in minutes)
    resolution_minutes = models.IntegerField(
        help_text="Target time for resolution (minutes)",
        validators=[MinValueValidator(1)],
    )

    # Business hours configuration
    business_hours_only = models.BooleanField(
        default=True,
        help_text="Count only business hours (Mon-Fri 9-5) toward SLA",
    )

    # Status
    is_active = models.BooleanField(default=True, help_text="Is this policy active?")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_sla_policies",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "support_sla_policies"
        ordering = ["priority", "name"]
        indexes = [
            models.Index(fields=["firm", "priority"]),
            models.Index(fields=["firm", "is_active"]),
        ]
        unique_together = [["firm", "priority"]]
        verbose_name_plural = "SLA Policies"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_priority_display()})"

    def get_first_response_deadline(self, created_at: timezone.datetime) -> timezone.datetime:
        """Calculate first response deadline from ticket creation time."""
        return created_at + timedelta(minutes=self.first_response_minutes)

    def get_resolution_deadline(self, created_at: timezone.datetime) -> timezone.datetime:
        """Calculate resolution deadline from ticket creation time."""
        return created_at + timedelta(minutes=self.resolution_minutes)


class Ticket(models.Model):
    """
    Support Ticket model (HubSpot Service Hub style).

    Represents a customer support request with status tracking,
    SLA monitoring, and assignment workflow.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STATUS_CHOICES = [
        ("new", "New"),
        ("open", "Open"),
        ("pending", "Pending Customer"),
        ("on_hold", "On Hold"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    PRIORITY_CHOICES = [
        ("critical", "Critical"),
        ("high", "High"),
        ("normal", "Normal"),
        ("low", "Low"),
    ]

    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("phone", "Phone"),
        ("chat", "Chat"),
        ("portal", "Client Portal"),
        ("api", "API"),
        ("other", "Other"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="tickets",
        help_text="Firm this ticket belongs to",
    )

    # Ticket identification
    ticket_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique ticket number (auto-generated)",
    )

    # Customer relationship
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="support_tickets",
        help_text="Client who submitted the ticket",
    )
    contact_email = models.EmailField(help_text="Contact email for this ticket")
    contact_name = models.CharField(max_length=255, help_text="Contact name")

    # Ticket details
    subject = models.CharField(max_length=500, help_text="Ticket subject/title")
    description = models.TextField(help_text="Detailed description of the issue")
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="normal",
        help_text="Ticket priority level",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
        help_text="Current ticket status",
    )
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default="email",
        help_text="Channel through which ticket was created",
    )

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        help_text="Staff member assigned to this ticket",
    )
    assigned_team = models.CharField(
        max_length=100,
        blank=True,
        help_text="Team assigned to this ticket (e.g., 'Support', 'Technical')",
    )

    # SLA tracking
    sla_policy = models.ForeignKey(
        SLAPolicy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
        help_text="SLA policy applied to this ticket",
    )
    first_response_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the first staff response was sent",
    )
    first_response_sla_breached = models.BooleanField(
        default=False,
        help_text="Did we breach first response SLA?",
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the ticket was resolved",
    )
    resolution_sla_breached = models.BooleanField(
        default=False,
        help_text="Did we breach resolution SLA?",
    )

    # Categorization
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ticket category (e.g., 'Billing', 'Technical', 'General')",
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for categorization and search",
    )

    # Related objects
    related_conversation = models.ForeignKey(
        "communications.Conversation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
        help_text="Related conversation thread",
    )

    # Customer satisfaction
    satisfaction_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Customer satisfaction rating (1-5)",
    )
    satisfaction_comment = models.TextField(
        blank=True,
        help_text="Customer feedback comment",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "support_tickets"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"]),
            models.Index(fields=["firm", "-created_at"]),
            models.Index(fields=["firm", "priority", "status"]),
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["ticket_number"]),
        ]

    def __str__(self) -> str:
        return f"#{self.ticket_number}: {self.subject}"

    def save(self, *args, **kwargs):
        """Auto-generate ticket number if not set."""
        if not self.ticket_number:
            # Generate ticket number: FIRM-YYYYMMDD-XXXX
            from django.utils import timezone
            today = timezone.now().strftime("%Y%m%d")
            last_ticket = (
                Ticket.objects.filter(firm=self.firm, ticket_number__startswith=f"{self.firm_id}-{today}")
                .order_by("-ticket_number")
                .first()
            )
            if last_ticket:
                last_seq = int(last_ticket.ticket_number.split("-")[-1])
                seq = last_seq + 1
            else:
                seq = 1
            self.ticket_number = f"{self.firm_id}-{today}-{seq:04d}"

        # Auto-assign SLA policy based on priority
        if not self.sla_policy_id and self.priority:
            sla_policy = SLAPolicy.objects.filter(
                firm=self.firm, priority=self.priority, is_active=True
            ).first()
            if sla_policy:
                self.sla_policy = sla_policy

        super().save(*args, **kwargs)

    def check_sla_breach(self) -> None:
        """Check and update SLA breach status."""
        if not self.sla_policy:
            return

        now = timezone.now()

        # Check first response SLA
        if not self.first_response_at:
            deadline = self.sla_policy.get_first_response_deadline(self.created_at)
            if now > deadline:
                self.first_response_sla_breached = True

        # Check resolution SLA
        if not self.resolved_at and self.status not in ["resolved", "closed"]:
            deadline = self.sla_policy.get_resolution_deadline(self.created_at)
            if now > deadline:
                self.resolution_sla_breached = True

        self.save(update_fields=["first_response_sla_breached", "resolution_sla_breached"])

    def mark_first_response(self) -> None:
        """Mark ticket as having received first response."""
        if not self.first_response_at:
            self.first_response_at = timezone.now()
            if self.status == "new":
                self.status = "open"
            self.save(update_fields=["first_response_at", "status", "updated_at"])

    def resolve(self, resolved_by: settings.AUTH_USER_MODEL = None) -> None:
        """Mark ticket as resolved."""
        self.status = "resolved"
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])

    def close(self) -> None:
        """Close the ticket."""
        self.status = "closed"
        self.closed_at = timezone.now()
        self.save(update_fields=["status", "closed_at", "updated_at"])


class TicketComment(models.Model):
    """
    Comment/response on a support ticket.

    Tracks all communication on a ticket (staff responses and customer replies).

    TIER 0: Belongs to exactly one Firm (via ticket relationship).
    """

    # Relationship
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="Ticket this comment belongs to",
    )

    # Comment details
    body = models.TextField(help_text="Comment content")
    is_internal = models.BooleanField(
        default=False,
        help_text="Is this an internal note (not visible to customer)?",
    )
    is_customer_reply = models.BooleanField(
        default=False,
        help_text="Was this comment from the customer?",
    )

    # Authorship
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ticket_comments",
        help_text="Staff member who created this comment",
    )
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Customer name if this is a customer reply",
    )
    customer_email = models.EmailField(
        blank=True,
        help_text="Customer email if this is a customer reply",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "support_ticket_comments"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ticket", "created_at"]),
            models.Index(fields=["created_by", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Comment on {self.ticket.ticket_number}"

    def save(self, *args, **kwargs):
        """Mark first response when staff adds first comment."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # If this is a staff comment (not customer, not internal note), mark first response
        if is_new and not self.is_customer_reply and not self.is_internal and self.created_by:
            if not self.ticket.first_response_at:
                self.ticket.mark_first_response()


class Survey(models.Model):
    """
    Customer feedback survey template.

    Defines survey questions for collecting customer feedback,
    including NPS (Net Promoter Score) surveys.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    SURVEY_TYPE_CHOICES = [
        ("nps", "Net Promoter Score (NPS)"),
        ("csat", "Customer Satisfaction (CSAT)"),
        ("ces", "Customer Effort Score (CES)"),
        ("custom", "Custom Survey"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("paused", "Paused"),
        ("archived", "Archived"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="surveys",
        help_text="Firm this survey belongs to",
    )

    # Survey identification
    name = models.CharField(max_length=255, help_text="Survey name (internal)")
    description = models.TextField(blank=True, help_text="Survey description")
    survey_type = models.CharField(
        max_length=20,
        choices=SURVEY_TYPE_CHOICES,
        default="csat",
        help_text="Type of survey",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        help_text="Survey status",
    )

    # Survey content
    introduction_text = models.TextField(
        blank=True,
        help_text="Introduction text shown to respondents",
    )
    questions = models.JSONField(
        default=list,
        help_text="List of survey questions with type and options",
    )
    thank_you_text = models.TextField(
        blank=True,
        help_text="Thank you message after survey submission",
    )

    # Trigger configuration
    trigger_on_ticket_resolution = models.BooleanField(
        default=False,
        help_text="Automatically send when ticket is resolved",
    )
    trigger_on_project_completion = models.BooleanField(
        default=False,
        help_text="Automatically send when project is completed",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_surveys",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "support_surveys"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"]),
            models.Index(fields=["firm", "survey_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_survey_type_display()})"


class SurveyResponse(models.Model):
    """
    Response to a customer survey.

    Tracks individual survey responses including NPS scores.

    TIER 0: Belongs to exactly one Firm (via survey relationship).
    """

    # Relationship
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="responses",
        help_text="Survey this response belongs to",
    )

    # Respondent
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="survey_responses",
        help_text="Client who responded",
    )
    contact_email = models.EmailField(help_text="Email of respondent")
    contact_name = models.CharField(max_length=255, help_text="Name of respondent")

    # Response data
    answers = models.JSONField(
        default=dict,
        help_text="Survey answers keyed by question ID",
    )

    # NPS specific (if survey_type is NPS)
    nps_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="NPS score (0-10), 0=detractor, 7-8=passive, 9-10=promoter",
    )
    nps_category = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("detractor", "Detractor (0-6)"),
            ("passive", "Passive (7-8)"),
            ("promoter", "Promoter (9-10)"),
        ],
        help_text="NPS category based on score",
    )

    # Related context
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="survey_responses",
        help_text="Ticket that triggered this survey (if applicable)",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="survey_responses",
        help_text="Project that triggered this survey (if applicable)",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "support_survey_responses"
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["survey", "-submitted_at"]),
            models.Index(fields=["client", "-submitted_at"]),
            models.Index(fields=["nps_score"]),
            models.Index(fields=["nps_category"]),
        ]

    def __str__(self) -> str:
        return f"Response to {self.survey.name} from {self.contact_name}"

    def save(self, *args, **kwargs):
        """Auto-calculate NPS category from score."""
        if self.nps_score is not None:
            if self.nps_score <= 6:
                self.nps_category = "detractor"
            elif self.nps_score <= 8:
                self.nps_category = "passive"
            else:
                self.nps_category = "promoter"
        super().save(*args, **kwargs)
