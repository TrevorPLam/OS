"""
Deal Assignment Automation (DEAL-5).

This module provides automated deal assignment logic including:
- Round-robin assignment
- Territory-based routing
- Deal stage automation triggers

Meta-commentary:
- **Current Status:** Round-robin assignment is implemented; territory/value/source rules fall back to round robin.
- **Design Rationale:** Rules apply in priority order with pipeline/stage filters (WHY: deterministic routing).
- **Missing:** Territory/value/source-specific routing logic beyond placeholders.
"""

from django.db import models
from django.conf import settings
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class AssignmentRule(models.Model):
    """
    Assignment rule for automatic deal routing (DEAL-5).
    
    Rules are evaluated in priority order to determine deal ownership.
    """
    
    RULE_TYPE_CHOICES = [
        ('round_robin', 'Round Robin'),
        ('territory', 'Territory-Based'),
        ('value_based', 'Value-Based'),
        ('source_based', 'Source-Based'),
    ]
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="deal_assignment_rules",
        help_text="Firm this rule belongs to"
    )
    
    # Rule Configuration
    name = models.CharField(max_length=255, help_text="Rule name")
    description = models.TextField(blank=True, help_text="Rule description")
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES, default='round_robin')
    is_active = models.BooleanField(default=True, help_text="Whether this rule is active")
    priority = models.IntegerField(default=0, help_text="Rule evaluation priority (lower = higher priority)")
    
    # Pipeline/Stage Filters
    pipelines = models.ManyToManyField(
        "crm.Pipeline",
        blank=True,
        related_name="assignment_rules",
        help_text="Apply to specific pipelines (empty = all)"
    )
    stages = models.ManyToManyField(
        "crm.PipelineStage",
        blank=True,
        related_name="assignment_rules",
        help_text="Apply to specific stages (empty = all)"
    )
    
    # Condition Filters (JSON)
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional conditions (value_min, value_max, sources, etc.)"
    )
    
    # Assignment Configuration
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="deal_assignment_rules",
        help_text="Users in the assignment pool"
    )
    
    # Round Robin State
    last_assigned_index = models.IntegerField(
        default=-1,
        help_text="Index of last assigned user (for round robin)"
    )
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_assignment_rules"
    )
    
    class Meta:
        db_table = "crm_assignment_rules"
        ordering = ["priority", "name"]
        indexes = [
            models.Index(fields=["firm", "is_active"], name="crm_assign_rule_firm_active_idx"),
            models.Index(fields=["firm", "priority"], name="crm_assign_rule_firm_priority_idx"),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.get_rule_type_display()})"
    
    def matches_deal(self, deal) -> bool:
        """Check if this rule matches the given deal."""
        # Check if rule is active
        if not self.is_active:
            return False
        
        # Check pipeline filter
        if self.pipelines.exists() and deal.pipeline not in self.pipelines.all():
            return False
        
        # Check stage filter
        if self.stages.exists() and deal.stage not in self.stages.all():
            return False
        
        # Check value conditions
        if 'value_min' in self.conditions:
            if float(deal.value) < float(self.conditions['value_min']):
                return False
        
        if 'value_max' in self.conditions:
            if float(deal.value) > float(self.conditions['value_max']):
                return False
        
        # Check source conditions
        if 'sources' in self.conditions and self.conditions['sources']:
            if deal.source not in self.conditions['sources']:
                return False
        
        return True
    
    def get_next_assignee(self):
        """Get the next assignee based on rule type."""
        assignees_list = list(self.assignees.filter(is_active=True))
        
        if not assignees_list:
            return None
        
        if self.rule_type == 'round_robin':
            # Round robin: rotate through assignees
            next_index = (self.last_assigned_index + 1) % len(assignees_list)
            self.last_assigned_index = next_index
            self.save(update_fields=['last_assigned_index', 'updated_at'])
            return assignees_list[next_index]
        
        elif self.rule_type == 'territory':
            # Territory-based: use territory mapping from conditions
            # This would need territory data in the deal
            # For now, fallback to round robin
            return self.get_next_assignee_round_robin(assignees_list)
        
        elif self.rule_type == 'value_based':
            # Value-based: assign to users with capacity
            # For now, fallback to round robin
            return self.get_next_assignee_round_robin(assignees_list)
        
        elif self.rule_type == 'source_based':
            # Source-based: assign based on deal source
            # For now, fallback to round robin
            return self.get_next_assignee_round_robin(assignees_list)
        
        return assignees_list[0]
    
    def get_next_assignee_round_robin(self, assignees_list: List):
        """Helper for round robin assignment."""
        next_index = (self.last_assigned_index + 1) % len(assignees_list)
        self.last_assigned_index = next_index
        self.save(update_fields=['last_assigned_index', 'updated_at'])
        return assignees_list[next_index]


class StageAutomation(models.Model):
    """
    Stage automation trigger (DEAL-5).
    
    Defines actions to take when a deal enters a specific stage.
    """
    
    ACTION_TYPE_CHOICES = [
        ('assign_user', 'Assign to User'),
        ('create_task', 'Create Task'),
        ('send_notification', 'Send Notification'),
        ('update_field', 'Update Field'),
        ('run_webhook', 'Run Webhook'),
    ]
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="stage_automations",
        help_text="Firm this automation belongs to"
    )
    
    # Trigger Configuration
    name = models.CharField(max_length=255, help_text="Automation name")
    description = models.TextField(blank=True, help_text="Automation description")
    is_active = models.BooleanField(default=True, help_text="Whether this automation is active")
    
    # Stage Trigger
    pipeline = models.ForeignKey(
        "crm.Pipeline",
        on_delete=models.CASCADE,
        related_name="stage_automations",
        help_text="Pipeline this automation applies to"
    )
    stage = models.ForeignKey(
        "crm.PipelineStage",
        on_delete=models.CASCADE,
        related_name="stage_automations",
        help_text="Stage that triggers this automation"
    )
    
    # Action Configuration
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES)
    action_config = models.JSONField(
        default=dict,
        help_text="Action configuration (user_id, task_template, notification_template, etc.)"
    )
    
    # Execution Delay
    delay_hours = models.IntegerField(
        default=0,
        help_text="Hours to wait before executing action (0 = immediate)"
    )
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_stage_automations"
    )
    
    class Meta:
        db_table = "crm_stage_automations"
        ordering = ["pipeline", "stage", "name"]
        indexes = [
            models.Index(fields=["firm", "is_active"], name="crm_stage_auto_firm_active_idx"),
            models.Index(fields=["pipeline", "stage"], name="crm_stage_auto_pip_stage_idx"),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} - {self.stage.name}"
    
    def execute(self, deal) -> bool:
        """Execute this automation for the given deal."""
        if not self.is_active:
            return False
        
        try:
            if self.action_type == 'assign_user':
                return self._execute_assign_user(deal)
            elif self.action_type == 'create_task':
                return self._execute_create_task(deal)
            elif self.action_type == 'send_notification':
                return self._execute_send_notification(deal)
            elif self.action_type == 'update_field':
                return self._execute_update_field(deal)
            elif self.action_type == 'run_webhook':
                return self._execute_run_webhook(deal)
            
            return False
        except Exception as e:
            logger.error(f"Error executing automation {self.id} for deal {deal.id}: {e}")
            return False
    
    def _execute_assign_user(self, deal) -> bool:
        """Assign deal to a specific user."""
        user_id = self.action_config.get('user_id')
        if not user_id:
            return False
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id, firm=self.firm, is_active=True)
            deal.owner = user
            deal.save(update_fields=['owner', 'updated_at'])
            return True
        except User.DoesNotExist:
            return False
    
    def _execute_create_task(self, deal) -> bool:
        """Create a task for the deal."""
        from modules.crm.models import DealTask
        
        task_data = self.action_config.get('task_template', {})
        if not task_data:
            return False
        
        DealTask.objects.create(
            deal=deal,
            title=task_data.get('title', 'Automated Task'),
            description=task_data.get('description', ''),
            priority=task_data.get('priority', 'medium'),
            assigned_to=deal.owner,
        )
        return True
    
    def _execute_send_notification(self, deal) -> bool:
        """Send a notification about the deal."""
        from modules.crm.models import DealAlert

        if not deal.owner:
            return False

        alert = DealAlert.objects.create(
            deal=deal,
            alert_type="owner_change",
            priority="medium",
            title=f"Deal assigned: {deal.name}",
            message=f"{deal.name} has been assigned to {deal.owner.get_full_name() or deal.owner.email}.",
        )
        alert.recipients.add(deal.owner)
        alert.send_notification()
        return True
    
    def _execute_update_field(self, deal) -> bool:
        """Update a field on the deal."""
        field_name = self.action_config.get('field_name')
        field_value = self.action_config.get('field_value')
        
        if not field_name:
            return False
        
        if hasattr(deal, field_name):
            setattr(deal, field_name, field_value)
            deal.save(update_fields=[field_name, 'updated_at'])
            return True
        
        return False
    
    def _execute_run_webhook(self, deal) -> bool:
        """Run a webhook for the deal."""
        import json
        import uuid

        from django.utils import timezone

        from modules.core.observability import generate_correlation_id
        from modules.webhooks.models import WebhookDelivery, WebhookEndpoint
        from modules.webhooks.queue import queue_webhook_delivery

        webhook_endpoint_id = self.action_config.get("webhook_endpoint_id")
        webhook_url = self.action_config.get("webhook_url")
        webhook_name = self.action_config.get("webhook_name") or f"Stage Automation: {self.name}"

        if not webhook_endpoint_id and not webhook_url:
            logger.warning("Stage automation webhook missing endpoint configuration", extra={"automation_id": self.id})
            return False

        if webhook_endpoint_id:
            endpoint = WebhookEndpoint.objects.filter(id=webhook_endpoint_id, firm=self.firm).first()
        else:
            endpoint, _ = WebhookEndpoint.objects.get_or_create(
                firm=self.firm,
                url=webhook_url,
                defaults={
                    "name": webhook_name,
                    "description": f"Stage automation webhook for {self.name}",
                    "status": "active",
                    "subscribed_events": ["crm.deal.stage_automation"],
                },
            )
            self.action_config["webhook_endpoint_id"] = endpoint.id
            self.save(update_fields=["action_config", "updated_at"])

        if not endpoint:
            logger.warning("Stage automation webhook endpoint not found", extra={"automation_id": self.id})
            return False

        payload = {
            "event_id": f"deal-stage-{deal.id}-{uuid.uuid4()}",
            "event_type": "crm.deal.stage_automation",
            "timestamp": timezone.now().isoformat(),
            "firm_id": self.firm_id,
            "data": {
                "deal": {
                    "id": deal.id,
                    "name": deal.name,
                    "value": str(deal.value),
                    "currency": deal.currency,
                    "stage_id": deal.stage_id,
                    "pipeline_id": deal.pipeline_id,
                    "owner_id": deal.owner_id,
                    "account_id": deal.account_id,
                    "contact_id": deal.contact_id,
                    "expected_close_date": deal.expected_close_date.isoformat()
                    if deal.expected_close_date
                    else None,
                    "actual_close_date": deal.actual_close_date.isoformat() if deal.actual_close_date else None,
                    "is_won": deal.is_won,
                    "is_lost": deal.is_lost,
                    "updated_at": deal.updated_at.isoformat(),
                },
            },
            "metadata": {
                "automation_id": self.id,
                "automation_name": self.name,
                "action_type": self.action_type,
            },
        }

        signature = endpoint.generate_signature(json.dumps(payload, separators=(",", ":"), sort_keys=True))
        delivery = WebhookDelivery.objects.create(
            webhook_endpoint=endpoint,
            event_type=payload["event_type"],
            event_id=payload["event_id"],
            payload=payload,
            status="pending",
            signature=signature,
        )

        correlation_id = generate_correlation_id()
        queue_webhook_delivery(delivery, correlation_id=correlation_id)

        logger.info(
            "Queued stage automation webhook delivery",
            extra={"automation_id": self.id, "delivery_id": delivery.id},
        )
        return True


def auto_assign_deal(deal) -> Optional[object]:
    """
    Automatically assign a deal based on assignment rules (DEAL-5).
    
    Args:
        deal: Deal instance to assign
        
    Returns:
        Assigned user or None
    """
    # Get active assignment rules for this firm, ordered by priority
    rules = AssignmentRule.objects.filter(
        firm=deal.firm,
        is_active=True
    ).prefetch_related('pipelines', 'stages', 'assignees').order_by('priority')
    
    # Find first matching rule
    for rule in rules:
        if rule.matches_deal(deal):
            assignee = rule.get_next_assignee()
            if assignee:
                deal.owner = assignee
                deal.save(update_fields=['owner', 'updated_at'])
                logger.info(f"Auto-assigned deal {deal.id} to {assignee.email} via rule {rule.name}")
                return assignee
    
    logger.info(f"No matching assignment rule for deal {deal.id}")
    return None


def trigger_stage_automations(deal, old_stage_id=None) -> None:
    """
    Trigger stage automations when deal enters a new stage (DEAL-5).
    
    Args:
        deal: Deal instance
        old_stage_id: Previous stage ID (optional)
    """
    # Only trigger if stage changed
    if old_stage_id == deal.stage_id:
        return
    
    # Get automations for this stage
    automations = StageAutomation.objects.filter(
        firm=deal.firm,
        pipeline=deal.pipeline,
        stage=deal.stage,
        is_active=True
    )
    
    for automation in automations:
        if automation.delay_hours == 0:
            # Execute immediately
            automation.execute(deal)
        else:
            # Schedule for later (would need Celery or similar)
            logger.info(f"Would schedule automation {automation.id} for {automation.delay_hours} hours")
