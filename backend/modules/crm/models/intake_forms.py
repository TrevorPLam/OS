from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager

from .leads import Lead
from .prospects import Prospect

class IntakeForm(models.Model):
    """
    Intake Form for lead qualification (Task 3.4).
    
    Customizable forms to collect information from prospects and qualify them
    based on predefined criteria. Can be embedded on websites or sent as links.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("archived", "Archived"),
    ]
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="intake_forms",
        help_text="Firm this form belongs to"
    )
    
    # Form Details
    name = models.CharField(
        max_length=200,
        help_text="Internal name for this form"
    )
    title = models.CharField(
        max_length=255,
        help_text="Form title shown to users"
    )
    description = models.TextField(
        blank=True,
        help_text="Form description/instructions"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )
    
    # Configuration
    qualification_enabled = models.BooleanField(
        default=True,
        help_text="Enable automatic lead qualification based on responses"
    )
    qualification_threshold = models.IntegerField(
        default=50,
        help_text="Minimum score (0-100) to qualify as a prospect"
    )
    auto_create_lead = models.BooleanField(
        default=True,
        help_text="Automatically create Lead record from submission"
    )
    auto_create_prospect = models.BooleanField(
        default=False,
        help_text="Automatically create Prospect record if qualified"
    )
    
    # Assignment
    default_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_intake_forms",
        help_text="Default owner for leads created from this form"
    )
    
    # Notifications
    notify_on_submission = models.BooleanField(
        default=True,
        help_text="Send notification when form is submitted"
    )
    notification_emails = models.TextField(
        blank=True,
        help_text="Comma-separated list of emails to notify (in addition to owner)"
    )
    
    # Thank You Page
    thank_you_title = models.CharField(
        max_length=255,
        default="Thank You!",
        help_text="Title shown after submission"
    )
    thank_you_message = models.TextField(
        default="We've received your information and will be in touch soon.",
        help_text="Message shown after submission"
    )
    redirect_url = models.URLField(
        blank=True,
        validators=[validate_safe_url],
        help_text="Optional URL to redirect to after submission"
    )
    
    # Metadata
    submission_count = models.IntegerField(
        default=0,
        help_text="Total number of submissions"
    )
    qualified_count = models.IntegerField(
        default=0,
        help_text="Number of qualified submissions"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_intake_forms",
        help_text="User who created this form"
    )
    
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "crm_intake_forms"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="crm_intake_firm_status_idx"),
            models.Index(fields=["firm", "created_at"], name="crm_intake_firm_created_idx"),
        ]
        verbose_name = "Intake Form"
        verbose_name_plural = "Intake Forms"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.status})"


class IntakeFormField(models.Model):
    """
    Field definition for IntakeForm (Task 3.4).
    
    Defines individual fields in an intake form with qualification scoring.
    """
    
    FIELD_TYPE_CHOICES = [
        ("text", "Short Text"),
        ("textarea", "Long Text"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("url", "URL"),
        ("number", "Number"),
        ("select", "Single Select"),
        ("multiselect", "Multi Select"),
        ("checkbox", "Checkbox"),
        ("date", "Date"),
        ("file", "File Upload"),
    ]
    
    # Relationships
    form = models.ForeignKey(
        IntakeForm,
        on_delete=models.CASCADE,
        related_name="fields",
        help_text="Form this field belongs to"
    )
    
    # Field Configuration
    label = models.CharField(
        max_length=255,
        help_text="Field label shown to users"
    )
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        default="text"
    )
    placeholder = models.CharField(
        max_length=255,
        blank=True,
        help_text="Placeholder text"
    )
    help_text = models.TextField(
        blank=True,
        help_text="Help text shown below field"
    )
    required = models.BooleanField(
        default=False,
        help_text="Is this field required?"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )
    
    # Options for select/multiselect
    options = models.JSONField(
        default=list,
        blank=True,
        help_text="Options for select/multiselect fields (list of strings)"
    )
    
    # Qualification Scoring
    scoring_enabled = models.BooleanField(
        default=False,
        help_text="Enable qualification scoring for this field"
    )
    scoring_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Scoring rules: {value: points, ...}"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = models.Manager()
    
    class Meta:
        db_table = "crm_intake_form_fields"
        ordering = ["form", "order", "id"]
        indexes = [
            models.Index(fields=["form", "order"], name="crm_intake_field_order_idx"),
        ]
        verbose_name = "Intake Form Field"
        verbose_name_plural = "Intake Form Fields"
    
    def __str__(self) -> str:
        return f"{self.form.name} - {self.label}"


class IntakeFormSubmission(models.Model):
    """
    Submission of an IntakeForm (Task 3.4).
    
    Stores responses to intake forms along with qualification score
    and automatically creates Lead/Prospect records based on configuration.
    
    TIER 0: Belongs to firm through IntakeForm relationship.
    """
    
    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("qualified", "Qualified"),
        ("disqualified", "Disqualified"),
        ("converted", "Converted to Lead/Prospect"),
        ("spam", "Marked as Spam"),
    ]
    
    # Relationships
    form = models.ForeignKey(
        IntakeForm,
        on_delete=models.CASCADE,
        related_name="submissions",
        help_text="Form that was submitted"
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intake_submissions",
        help_text="Lead created from this submission (if applicable)"
    )
    prospect = models.ForeignKey(
        Prospect,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intake_submissions",
        help_text="Prospect created from this submission (if qualified)"
    )
    
    # Response Data
    responses = models.JSONField(
        default=dict,
        help_text="Field responses: {field_id: value, ...}"
    )
    
    # Qualification
    qualification_score = models.IntegerField(
        default=0,
        help_text="Calculated qualification score (0-100)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    is_qualified = models.BooleanField(
        default=False,
        help_text="Whether submission meets qualification threshold"
    )
    
    # Submitter Information
    submitter_email = models.EmailField(
        blank=True,
        help_text="Email address from submission"
    )
    submitter_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name from submission"
    )
    submitter_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Phone number from submission"
    )
    submitter_company = models.CharField(
        max_length=255,
        blank=True,
        help_text="Company name from submission"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of submitter"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string"
    )
    referrer = models.URLField(
        blank=True,
        validators=[validate_safe_url],
        help_text="Referring URL"
    )
    
    # Review
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_intake_submissions",
        help_text="User who reviewed this submission"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When submission was reviewed"
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Internal notes from review"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = models.Manager()
    
    class Meta:
        db_table = "crm_intake_form_submissions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["form", "status"], name="crm_intake_sub_status_idx"),
            models.Index(fields=["form", "created_at"], name="crm_intake_sub_created_idx"),
            models.Index(fields=["form", "is_qualified"], name="crm_intake_sub_qualified_idx"),
            models.Index(fields=["submitter_email"], name="crm_intake_sub_email_idx"),
        ]
        verbose_name = "Intake Form Submission"
        verbose_name_plural = "Intake Form Submissions"
    
    def __str__(self) -> str:
        return f"{self.form.name} - {self.submitter_email or 'Anonymous'} ({self.created_at})"
    
    def calculate_qualification_score(self) -> int:
        """Calculate qualification score based on field responses and scoring rules."""
        total_score = 0
        max_score = 0
        
        # Iterate through form fields with scoring enabled
        for field in self.form.fields.filter(scoring_enabled=True):
            if not field.scoring_rules:
                continue
            
            # Get the response for this field
            field_id = str(field.id)
            response_value = self.responses.get(field_id)
            
            if response_value is None:
                continue
            
            # Calculate score based on scoring rules
            # Scoring rules format: {value: points, ...} or {"ranges": [{"min": 0, "max": 10, "points": 5}]}
            if isinstance(field.scoring_rules, dict):
                # Check for exact match
                if str(response_value) in field.scoring_rules:
                    points = field.scoring_rules[str(response_value)]
                    total_score += points
                    # Safely get max score
                    if field.scoring_rules.values():
                        max_score += max(field.scoring_rules.values())
                # Check for range-based scoring (for number fields)
                elif "ranges" in field.scoring_rules:
                    try:
                        value = float(response_value)
                        for range_def in field.scoring_rules.get("ranges", []):
                            min_val = range_def.get("min", float("-inf"))
                            max_val = range_def.get("max", float("inf"))
                            if min_val <= value <= max_val:
                                total_score += range_def.get("points", 0)
                                # Track max possible score from ranges
                                max_score += range_def.get("points", 0)
                                break
                    except (ValueError, TypeError):
                        pass
        
        # Normalize to 0-100 scale
        if max_score > 0:
            normalized_score = int((total_score / max_score) * 100)
        else:
            normalized_score = 0
        
        self.qualification_score = normalized_score
        self.is_qualified = normalized_score >= self.form.qualification_threshold
        
        if self.is_qualified and self.status == "pending":
            self.status = "qualified"
        elif not self.is_qualified and self.status == "pending":
            self.status = "disqualified"
        
        self.save()
        return normalized_score
    
    def create_lead(self) -> "Lead":
        """Create a Lead record from this submission."""
        if self.lead:
            return self.lead
        
        # Extract information from responses
        email = self.submitter_email
        name = self.submitter_name
        phone = self.submitter_phone
        company = self.submitter_company
        
        # Safely parse name into first and last
        name_parts = name.split() if name else []
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # Create lead
        lead = Lead.objects.create(
            firm=self.form.firm,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            company=company,
            source="intake_form",
            status="new",
            assigned_to=self.form.default_owner,
            notes=f"Created from intake form: {self.form.name}\nQualification Score: {self.qualification_score}",
        )
        
        self.lead = lead
        self.status = "converted"
        self.save()
        
        # Update form submission count
        self.form.submission_count += 1
        if self.is_qualified:
            self.form.qualified_count += 1
        self.form.save()
        
        return lead


# ============================================================================
# CPQ (Configure-Price-Quote) System - Task 3.5
# ============================================================================

