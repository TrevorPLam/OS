from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


class Pipeline(models.Model):
    """
    Pipeline model with configurable stages (DEAL-1).
    
    Represents a customizable sales pipeline with stages that deals progress through.
    Each firm can have multiple pipelines for different types of deals.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="pipelines",
        help_text="Firm (workspace) this pipeline belongs to"
    )
    
    # Pipeline Details
    name = models.CharField(max_length=255, help_text="Pipeline name (e.g., 'Sales', 'Consulting', 'Enterprise')")
    description = models.TextField(blank=True, help_text="Pipeline description and purpose")
    is_active = models.BooleanField(default=True, help_text="Whether this pipeline is currently active")
    is_default = models.BooleanField(default=False, help_text="Whether this is the default pipeline for new deals")
    
    # Ordering
    display_order = models.IntegerField(default=0, help_text="Display order for sorting pipelines")
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_pipelines",
        help_text="User who created this pipeline"
    )
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "crm_pipelines"
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["firm", "is_active"], name="crm_pip_firm_active_idx"),
            models.Index(fields=["firm", "is_default"], name="crm_pip_firm_default_idx"),
        ]
        unique_together = [["firm", "name"]]
    
    def __str__(self) -> str:
        return f"{self.name}"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to ensure only one default pipeline per firm."""
        if self.is_default:
            # Use database transaction to prevent race conditions
            from django.db import transaction
            with transaction.atomic():
                # Lock the rows to prevent concurrent updates
                Pipeline.objects.select_for_update().filter(
                    firm=self.firm, 
                    is_default=True
                ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class PipelineStage(models.Model):
    """
    Pipeline Stage model (DEAL-1).
    
    Represents a stage within a pipeline. Stages have a specific order
    and probability associated with them.
    
    TIER 0: Belongs to exactly one Firm via Pipeline relationship.
    """
    
    # Pipeline relationship
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name="stages",
        help_text="Pipeline this stage belongs to"
    )
    
    # Stage Details
    name = models.CharField(max_length=100, help_text="Stage name (e.g., 'Discovery', 'Proposal', 'Negotiation')")
    description = models.TextField(blank=True, help_text="Stage description")
    
    # Stage Configuration
    probability = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Default win probability percentage (0-100) for deals in this stage"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this stage is currently active")
    is_closed_won = models.BooleanField(default=False, help_text="Mark as won stage")
    is_closed_lost = models.BooleanField(default=False, help_text="Mark as lost stage")
    
    # Ordering
    display_order = models.IntegerField(default=0, help_text="Display order within the pipeline")
    
    # Automation (future)
    auto_tasks = models.JSONField(
        default=list,
        blank=True,
        help_text="Tasks to auto-create when deal enters this stage"
    )
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "crm_pipeline_stages"
        ordering = ["pipeline", "display_order", "name"]
        indexes = [
            models.Index(fields=["pipeline", "display_order"], name="crm_pip_stg_pip_ord_idx"),
            models.Index(fields=["pipeline", "is_active"], name="crm_pip_stg_pip_act_idx"),
        ]
        unique_together = [["pipeline", "name"]]
    
    def __str__(self) -> str:
        return f"{self.pipeline.name} - {self.name}"
    
    @property
    def firm(self):
        """Get the firm through the pipeline relationship."""
        return self.pipeline.firm


