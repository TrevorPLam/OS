from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


class Deal(models.Model):
    """
    Deal model with value, probability, and associations (DEAL-1).
    
    Represents a sales opportunity/deal that progresses through pipeline stages.
    More flexible than Prospect - can be associated with Accounts, Contacts, 
    and eventually converted to Projects.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="deals",
        help_text="Firm (workspace) this deal belongs to"
    )
    
    # Pipeline & Stage
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.PROTECT,
        related_name="deals",
        help_text="Pipeline this deal belongs to"
    )
    stage = models.ForeignKey(
        PipelineStage,
        on_delete=models.PROTECT,
        related_name="deals",
        help_text="Current stage in the pipeline"
    )
    
    # Deal Details
    name = models.CharField(max_length=255, help_text="Deal name/title")
    description = models.TextField(blank=True, help_text="Deal description and notes")
    
    # Associations (optional - can have account, contact, or both)
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
        help_text="Associated account/company"
    )
    contact = models.ForeignKey(
        AccountContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
        help_text="Primary contact for this deal"
    )
    
    # Financial Details
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Deal value/amount"
    )
    currency = models.CharField(max_length=3, default="USD")
    probability = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Win probability percentage (0-100)"
    )
    weighted_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Auto-calculated: value * probability / 100"
    )
    
    # Timeline
    expected_close_date = models.DateField(help_text="Expected close date")
    actual_close_date = models.DateField(null=True, blank=True, help_text="Actual close date when won/lost")
    
    # Assignment & Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_deals",
        help_text="Primary deal owner"
    )
    team_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="team_deals",
        help_text="Additional team members working on this deal"
    )
    
    # Deal Splitting (DEAL-6) - for multiple owners
    split_percentage = models.JSONField(
        default=dict,
        blank=True,
        help_text="Split percentages for multiple owners {user_id: percentage}"
    )
    
    # Source Tracking
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Lead source (e.g., 'Website', 'Referral', 'Cold Call')"
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
        help_text="Marketing campaign that generated this deal"
    )
    
    # Status & Lifecycle
    is_active = models.BooleanField(default=True, help_text="Whether this deal is active")
    is_won = models.BooleanField(default=False, help_text="Deal was won")
    is_lost = models.BooleanField(default=False, help_text="Deal was lost")
    lost_reason = models.CharField(max_length=255, blank=True, help_text="Reason for losing the deal")
    
    # Rotting/Stale Detection (DEAL-6)
    last_activity_date = models.DateField(null=True, blank=True, help_text="Date of last activity on this deal")
    is_stale = models.BooleanField(default=False, help_text="Deal has had no activity for extended period")
    stale_days_threshold = models.IntegerField(default=30, help_text="Days without activity before marked stale")
    
    # Conversion to Project
    converted_to_project = models.BooleanField(default=False, help_text="Deal converted to project")
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_deals",
        help_text="Project created from this deal"
    )
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_deals",
        help_text="User who created this deal"
    )
    
    # Tags for filtering/organization
    tags = models.JSONField(default=list, blank=True, help_text="Tags for categorizing deals")
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "crm_deals"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "pipeline", "stage"], name="crm_deal_firm_pip_stg_idx"),
            models.Index(fields=["firm", "owner"], name="crm_deal_firm_owner_idx"),
            models.Index(fields=["firm", "is_active"], name="crm_deal_firm_active_idx"),
            models.Index(fields=["firm", "expected_close_date"], name="crm_deal_firm_close_idx"),
            models.Index(fields=["firm", "is_stale"], name="crm_deal_firm_stale_idx"),
            models.Index(fields=["account"], name="crm_deal_account_idx"),
            models.Index(fields=["contact"], name="crm_deal_contact_idx"),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} - {self.stage.name} (${self.value})"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to calculate weighted value and update status."""
        # Calculate weighted value
        self.weighted_value = (self.value * Decimal(self.probability)) / Decimal(100)
        
        # Update is_won/is_lost based on stage
        if self.stage.is_closed_won:
            self.is_won = True
            self.is_active = False
            if not self.actual_close_date:
                from django.utils import timezone
                self.actual_close_date = timezone.now().date()
        elif self.stage.is_closed_lost:
            self.is_lost = True
            self.is_active = False
            if not self.actual_close_date:
                from django.utils import timezone
                self.actual_close_date = timezone.now().date()
        
        # Check for stale deals (DEAL-6)
        if self.last_activity_date and self.is_active:
            from django.utils import timezone
            days_since_activity = (timezone.now().date() - self.last_activity_date).days
            self.is_stale = days_since_activity >= self.stale_days_threshold
        
        super().save(*args, **kwargs)
    
    def update_last_activity(self) -> None:
        """Update last activity date to today."""
        from django.utils import timezone
        self.last_activity_date = timezone.now().date()
        self.is_stale = False
        self.save(update_fields=["last_activity_date", "is_stale", "updated_at"])
    
    def convert_to_project(self, project_data: dict = None) -> Any:
        """
        Convert this deal to a project (DEAL-1 conversion workflow).
        
        Args:
            project_data: Optional dictionary with project creation data
            
        Returns:
            Created Project instance
        """
        if self.converted_to_project:
            raise ValueError("Deal has already been converted to a project")
        
        if not self.is_won:
            raise ValueError("Only won deals can be converted to projects")
        
        from modules.projects.models import Project
        from django.utils import timezone
        
        # Prepare project data
        project_defaults = {
            "firm": self.firm,
            "name": self.name,
            "description": self.description,
            "client": self.account.client if self.account and hasattr(self.account, "client") else None,
            "budget": self.value,
            "owner": self.owner,
            "start_date": timezone.now().date(),
            "status": "planning",
        }
        
        # Merge with provided project data
        if project_data:
            project_defaults.update(project_data)
        
        # Create the project
        project = Project.objects.create(**project_defaults)
        
        # Update deal
        self.converted_to_project = True
        self.project = project
        self.save(update_fields=["converted_to_project", "project", "updated_at"])
        
        return project


class DealTask(models.Model):
    """
    Task associated with a Deal (DEAL-2).
    
    Represents action items and tasks related to deal progression.
    
    TIER 0: Belongs to exactly one Firm via Deal relationship.
    """
    
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    
    # Deal relationship
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name="tasks",
        help_text="Deal this task belongs to"
    )
    
    # Task Details
    title = models.CharField(max_length=255, help_text="Task title")
    description = models.TextField(blank=True, help_text="Task description")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    
    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deal_tasks",
        help_text="User assigned to this task"
    )
    
    # Timeline
    due_date = models.DateField(null=True, blank=True, help_text="Task due date")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When task was completed")
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_deal_tasks",
        help_text="User who created this task"
    )
    
    class Meta:
        db_table = "crm_deal_tasks"
        ordering = ["due_date", "-priority", "title"]
        indexes = [
            models.Index(fields=["deal", "status"], name="crm_deal_task_deal_status_idx"),
            models.Index(fields=["assigned_to", "status"], name="crm_deal_task_user_status_idx"),
            models.Index(fields=["due_date"], name="crm_deal_task_due_idx"),
        ]
    
    def __str__(self) -> str:
        return f"{self.deal.name} - {self.title}"
    
    @property
    def firm(self):
        """Get the firm through the deal relationship."""
        return self.deal.firm
    
    def complete(self) -> None:
        """Mark task as completed."""
        from django.utils import timezone
        self.status = "completed"
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])
        
        # Update deal last activity
        self.deal.update_last_activity()


# Import assignment automation models (DEAL-5)
from .assignment_automation import AssignmentRule, StageAutomation
class DealAssignmentRule(models.Model):
    """
    Deal Assignment Automation Rule (DEAL-5).
    
    Defines rules for automatically assigning deals to users.
    Supports round-robin, territory-based, and custom routing logic.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    ASSIGNMENT_TYPE_CHOICES = [
        ("round_robin", "Round Robin"),
        ("territory", "Territory-Based"),
        ("lead_source", "Lead Source"),
        ("deal_value", "Deal Value"),
        ("load_balance", "Load Balanced"),
    ]
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="deal_assignment_rules",
        help_text="Firm (workspace) this rule belongs to"
    )
    
    # Rule Details
    name = models.CharField(max_length=255, help_text="Rule name")
    description = models.TextField(blank=True, help_text="Rule description")
    assignment_type = models.CharField(
        max_length=50,
        choices=ASSIGNMENT_TYPE_CHOICES,
        default="round_robin",
        help_text="Type of assignment logic"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this rule is active")
    priority = models.IntegerField(default=0, help_text="Rule priority (higher = evaluated first)")
    
    # Pipeline & Stage Filters
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assignment_rules",
        help_text="Apply rule to specific pipeline (null = all pipelines)"
    )
    stage = models.ForeignKey(
        PipelineStage,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assignment_rules",
        help_text="Apply rule when deal enters this stage (null = any stage)"
    )
    
    # Assignment Target Users
    target_users = models.ManyToManyField(
        "auth.User",
        related_name="deal_assignment_rules",
        help_text="Users to assign deals to"
    )
    
    # Round Robin State
    last_assigned_user = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="last_assigned_rules",
        help_text="Last user assigned (for round-robin)"
    )
    
    # Territory-Based Configuration
    territory_field = models.CharField(
        max_length=100,
        blank=True,
        help_text="Field to use for territory matching (e.g., 'account.state', 'account.country')"
    )
    territory_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text="Territory to user mapping {territory: user_id}"
    )
    
    # Value-Based Configuration
    min_deal_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum deal value to trigger this rule"
    )
    max_deal_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum deal value to trigger this rule"
    )
    
    # Lead Source Configuration
    lead_sources = models.JSONField(
        default=list,
        blank=True,
        help_text="List of lead sources to trigger this rule"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_assignment_rules"
    )
    
    class Meta:
        db_table = "crm_deal_assignment_rule"
        ordering = ["-priority", "name"]
        indexes = [
            models.Index(fields=["firm", "is_active"], name="crm_assign_rule_firm_active_idx"),
            models.Index(fields=["pipeline", "is_active"], name="crm_assign_rule_pipe_active_idx"),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.get_assignment_type_display()})"
    
    @property
    def firm_property(self):
        """Get the firm for TIER 0 scoping."""
        return self.firm
    
    def get_next_assignee(self, deal=None):
        """
        Get the next user to assign based on the rule type.
        
        Args:
            deal: Optional Deal instance for context-aware assignment
            
        Returns:
            User instance or None
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        target_users = self.target_users.filter(is_active=True)
        
        if not target_users.exists():
            return None
        
        if self.assignment_type == "round_robin":
            # Get next user in round-robin sequence
            if self.last_assigned_user and self.last_assigned_user in target_users:
                user_list = list(target_users)
                current_index = user_list.index(self.last_assigned_user)
                next_index = (current_index + 1) % len(user_list)
                return user_list[next_index]
            else:
                return target_users.first()
        
        elif self.assignment_type == "territory" and deal and deal.account:
            # Territory-based assignment
            territory_value = self._get_territory_value(deal)
            if territory_value and territory_value in self.territory_mapping:
                user_id = self.territory_mapping[territory_value]
                try:
                    return User.objects.get(id=user_id, is_active=True)
                except User.DoesNotExist:
                    pass
            return None
        
        elif self.assignment_type == "load_balance":
            # Assign to user with fewest active deals
            from django.db.models import Count
            return target_users.annotate(
                deal_count=Count("owned_deals", filter=models.Q(owned_deals__is_active=True))
            ).order_by("deal_count").first()
        
        else:
            # Default to round-robin
            return target_users.first()
    
    def _get_territory_value(self, deal):
        """Extract territory value from deal using territory_field."""
        if not self.territory_field:
            return None
        
        try:
            # Support nested field access like 'account.state'
            obj = deal
            for field in self.territory_field.split('.'):
                obj = getattr(obj, field, None)
                if obj is None:
                    return None
            return str(obj)
        except (AttributeError, TypeError):
            return None
    
    def matches_criteria(self, deal):
        """
        Check if this rule should apply to the given deal.
        
        Args:
            deal: Deal instance
            
        Returns:
            bool: True if rule matches
        """
        # Check pipeline
        if self.pipeline and deal.pipeline != self.pipeline:
            return False
        
        # Check stage
        if self.stage and deal.stage != self.stage:
            return False
        
        # Check deal value range
        if self.min_deal_value and deal.value < self.min_deal_value:
            return False
        if self.max_deal_value and deal.value > self.max_deal_value:
            return False
        
        # Check lead sources (if deal has a lead source field)
        if self.lead_sources:
            deal_source = getattr(deal, 'source', None)
            if deal_source and deal_source not in self.lead_sources:
                return False
        
        return True


class DealStageAutomation(models.Model):
    """
    Deal Stage Automation Trigger (DEAL-5).
    
    Defines automated actions when a deal enters or exits a stage.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    TRIGGER_TYPE_CHOICES = [
        ("enter", "On Enter Stage"),
        ("exit", "On Exit Stage"),
    ]
    
    ACTION_TYPE_CHOICES = [
        ("assign_user", "Assign to User"),
        ("create_task", "Create Task"),
        ("send_notification", "Send Notification"),
        ("update_field", "Update Field"),
    ]
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="deal_stage_automations",
        help_text="Firm (workspace) this automation belongs to"
    )
    
    # Automation Details
    name = models.CharField(max_length=255, help_text="Automation name")
    description = models.TextField(blank=True, help_text="Automation description")
    is_active = models.BooleanField(default=True, help_text="Whether this automation is active")
    
    # Trigger Configuration
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name="stage_automations",
        help_text="Pipeline to monitor"
    )
    stage = models.ForeignKey(
        PipelineStage,
        on_delete=models.CASCADE,
        related_name="stage_automations",
        help_text="Stage that triggers this automation"
    )
    trigger_type = models.CharField(
        max_length=10,
        choices=TRIGGER_TYPE_CHOICES,
        default="enter",
        help_text="When to trigger"
    )
    
    # Action Configuration
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPE_CHOICES,
        help_text="Type of action to perform"
    )
    action_config = models.JSONField(
        default=dict,
        help_text="Action configuration parameters"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_stage_automations"
    )
    
    class Meta:
        db_table = "crm_deal_stage_automation"
        ordering = ["pipeline", "stage", "name"]
        indexes = [
            models.Index(fields=["firm", "is_active"], name="crm_stage_auto_firm_active_idx"),
            models.Index(fields=["pipeline", "stage", "is_active"], name="crm_stage_auto_pipe_stage_idx"),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.pipeline.name} - {self.stage.name})"
    
    @property
    def firm_property(self):
        """Get the firm for TIER 0 scoping."""
        return self.firm
    
    def execute(self, deal):
        """
        Execute the automation action for the given deal.
        
        Args:
            deal: Deal instance
        """
        if not self.is_active:
            return
        
        if self.action_type == "assign_user":
            user_id = self.action_config.get("user_id")
            if user_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(id=user_id, is_active=True)
                    deal.owner = user
                    deal.save(update_fields=["owner", "updated_at"])
                except User.DoesNotExist:
                    pass
        
        elif self.action_type == "create_task":
            task_title = self.action_config.get("title", "New Task")
            task_description = self.action_config.get("description", "")
            task_priority = self.action_config.get("priority", "medium")
            DealTask.objects.create(
                deal=deal,
                title=task_title,
                description=task_description,
                priority=task_priority,
                assigned_to=deal.owner,
                created_by=self.created_by
            )
        
        elif self.action_type == "send_notification":
            # Placeholder for notification logic
            pass
        
        elif self.action_type == "update_field":
            field_name = self.action_config.get("field")
            field_value = self.action_config.get("value")
            if field_name and hasattr(deal, field_name):
                setattr(deal, field_name, field_value)
                deal.save(update_fields=[field_name, "updated_at"])


class DealAlert(models.Model):
    """
    Deal Alert/Notification (DEAL-6).
    
    Tracks alerts and reminders for deals, particularly for stale/rotting deals.
    
    TIER 0: Belongs to exactly one Firm via Deal relationship.
    """
    
    ALERT_TYPE_CHOICES = [
        ("stale", "Stale Deal"),
        ("close_date", "Close Date Approaching"),
        ("value_change", "Value Changed"),
        ("owner_change", "Owner Changed"),
        ("stage_change", "Stage Changed"),
        ("custom", "Custom Alert"),
    ]
    
    ALERT_PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]
    
    # Deal relationship
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name="alerts",
        help_text="Deal this alert is for"
    )
    
    # Alert Details
    alert_type = models.CharField(
        max_length=50,
        choices=ALERT_TYPE_CHOICES,
        help_text="Type of alert"
    )
    priority = models.CharField(
        max_length=20,
        choices=ALERT_PRIORITY_CHOICES,
        default="medium",
        help_text="Alert priority"
    )
    title = models.CharField(max_length=255, help_text="Alert title")
    message = models.TextField(help_text="Alert message")
    
    # Notification
    is_sent = models.BooleanField(default=False, help_text="Whether notification has been sent")
    sent_at = models.DateTimeField(null=True, blank=True, help_text="When notification was sent")
    recipients = models.ManyToManyField(
        "auth.User",
        related_name="deal_alerts",
        help_text="Users to notify"
    )
    
    # Acknowledgement
    is_acknowledged = models.BooleanField(default=False, help_text="Whether alert has been acknowledged")
    acknowledged_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_alerts",
        help_text="User who acknowledged the alert"
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True, help_text="When alert was acknowledged")
    
    # Auto-dismiss
    auto_dismiss_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when alert should be auto-dismissed"
    )
    is_dismissed = models.BooleanField(default=False, help_text="Whether alert has been dismissed")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "crm_deal_alert"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["deal", "is_sent"], name="crm_deal_alert_deal_sent_idx"),
            models.Index(fields=["alert_type", "is_sent"], name="crm_deal_alert_type_sent_idx"),
            models.Index(fields=["is_acknowledged", "is_dismissed"], name="crm_deal_alert_status_idx"),
        ]
    
    def __str__(self) -> str:
        return f"{self.title} - {self.deal.name}"
    
    @property
    def firm(self):
        """Get the firm through the deal relationship."""
        return self.deal.firm
    
    def send_notification(self):
        """
        Send notification to recipients.
        
        This is a placeholder for actual notification logic.
        In production, this would integrate with email, SMS, or in-app notification systems.
        """
        if self.is_sent:
            return

        import logging
        from django.conf import settings
        from django.utils import timezone

        from modules.core.notifications import EmailNotification
        from modules.firm.models import FirmMembership

        logger = logging.getLogger(__name__)
        sent_count = 0
        failed_count = 0

        for recipient in self.recipients.all():
            membership = (
                FirmMembership.objects.filter(firm=self.deal.firm, user=recipient, is_active=True)
                .select_related("profile")
                .first()
            )
            preferences = {}
            if membership and hasattr(membership, "profile") and membership.profile:
                preferences = membership.profile.notification_preferences or {}
            deal_prefs = preferences.get("deal_assignment", {"email": True, "in_app": True})

            if deal_prefs.get("email", True):
                frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
                deal_link = f"{frontend_url}/crm/deals/{self.deal.id}"
                subject = f"Deal assigned: {self.deal.name}"
                html_content = (
                    f"<p>A deal has been assigned to you.</p>"
                    f"<p><strong>{self.deal.name}</strong></p>"
                    f"<p>Value: {self.deal.value}</p>"
                    f"<p><a href=\"{deal_link}\">View deal</a></p>"
                )
                success = EmailNotification.send(
                    to=recipient.email,
                    subject=subject,
                    html_content=html_content,
                )
                if success:
                    sent_count += 1
                else:
                    failed_count += 1

        if sent_count:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save(update_fields=["is_sent", "sent_at", "updated_at"])

        if failed_count:
            logger.warning(
                "Failed to deliver deal alert notifications",
                extra={"deal_id": self.deal.id, "failed": failed_count},
            )
    
    def acknowledge(self, user):
        """Acknowledge the alert."""
        from django.utils import timezone
        
        self.is_acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save(update_fields=["is_acknowledged", "acknowledged_by", "acknowledged_at", "updated_at"])
    
    def dismiss(self):
        """Dismiss the alert."""
        self.is_dismissed = True
        self.save(update_fields=["is_dismissed", "updated_at"])


