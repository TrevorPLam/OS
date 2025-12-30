from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("firm", "0011_role_based_views"),
        ("crm", "0002_add_performance_indexes"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Tag name", max_length=100)),
                ("slug", models.SlugField(help_text="URL-friendly tag identifier", max_length=100)),
                ("description", models.TextField(blank=True, help_text="Tag description")),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("general", "General"),
                            ("industry", "Industry"),
                            ("service", "Service Type"),
                            ("status", "Status"),
                            ("behavior", "Behavior"),
                            ("campaign", "Campaign"),
                            ("custom", "Custom"),
                        ],
                        default="general",
                        help_text="Tag category",
                        max_length=20,
                    ),
                ),
                ("color", models.CharField(blank=True, help_text="Hex color code for tag display (e.g., #FF5733)", max_length=7)),
                ("usage_count", models.IntegerField(default=0, help_text="Number of entities tagged with this tag")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="created_tags",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "firm",
                    models.ForeignKey(
                        help_text="Firm this tag belongs to",
                        on_delete=models.CASCADE,
                        related_name="tags",
                        to="firm.firm",
                    ),
                ),
            ],
            options={
                "db_table": "marketing_tags",
                "ordering": ["name"],
                "indexes": [
                    models.Index(fields=["firm", "category"], name="mkt_idx"),
                    models.Index(fields=["firm", "slug"], name="mkt_idx"),
                ],
                "unique_together": {("firm", "slug")},
            },
        ),
        migrations.CreateModel(
            name="Segment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Segment name", max_length=255)),
                ("description", models.TextField(blank=True, help_text="Segment description")),
                ("criteria", models.JSONField(default=dict, help_text="Segmentation rules (tags, lead_score range, status, etc.)")),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("paused", "Paused"), ("archived", "Archived")],
                        default="active",
                        help_text="Segment status",
                        max_length=20,
                    ),
                ),
                (
                    "auto_update",
                    models.BooleanField(
                        default=True, help_text="Automatically update segment membership based on criteria"
                    ),
                ),
                (
                    "last_refreshed_at",
                    models.DateTimeField(blank=True, help_text="When segment membership was last calculated", null=True),
                ),
                ("member_count", models.IntegerField(default=0, help_text="Cached count of current members")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="created_segments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "firm",
                    models.ForeignKey(
                        help_text="Firm this segment belongs to",
                        on_delete=models.CASCADE,
                        related_name="segments",
                        to="firm.firm",
                    ),
                ),
            ],
            options={
                "db_table": "marketing_segments",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["firm", "status"], name="mkt_idx"),
                    models.Index(fields=["firm", "-created_at"], name="mkt_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="EmailTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Template name (internal)", max_length=255)),
                ("description", models.TextField(blank=True, help_text="Template description")),
                (
                    "template_type",
                    models.CharField(
                        choices=[
                            ("campaign", "Marketing Campaign"),
                            ("transactional", "Transactional"),
                            ("nurture", "Nurture Sequence"),
                            ("announcement", "Announcement"),
                            ("newsletter", "Newsletter"),
                            ("custom", "Custom"),
                        ],
                        default="campaign",
                        help_text="Template type",
                        max_length=20,
                    ),
                ),
                (
                    "subject_line",
                    models.CharField(
                        help_text="Email subject (supports merge fields like {{company_name}})", max_length=500
                    ),
                ),
                (
                    "preheader_text",
                    models.CharField(blank=True, help_text="Preheader text shown in email preview", max_length=200),
                ),
                ("html_content", models.TextField(help_text="HTML email content (supports merge fields)")),
                (
                    "plain_text_content",
                    models.TextField(blank=True, help_text="Plain text version (auto-generated if blank)"),
                ),
                (
                    "design_json",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Design structure for visual editor (blocks, styles, etc.)",
                    ),
                ),
                (
                    "available_merge_fields",
                    models.JSONField(
                        default=list,
                        help_text="List of available merge fields (contact_name, company_name, etc.)",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("active", "Active"), ("archived", "Archived")],
                        default="draft",
                        help_text="Template status",
                        max_length=20,
                    ),
                ),
                ("times_used", models.IntegerField(default=0, help_text="Number of times this template has been used")),
                (
                    "last_used_at",
                    models.DateTimeField(blank=True, help_text="When this template was last used", null=True),
                ),
                (
                    "avg_open_rate",
                    models.DecimalField(
                        blank=True, decimal_places=2, help_text="Average open rate percentage", max_digits=5, null=True
                    ),
                ),
                (
                    "avg_click_rate",
                    models.DecimalField(
                        blank=True, decimal_places=2, help_text="Average click-through rate percentage", max_digits=5, null=True
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="created_email_templates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "firm",
                    models.ForeignKey(
                        help_text="Firm this template belongs to",
                        on_delete=models.CASCADE,
                        related_name="email_templates",
                        to="firm.firm",
                    ),
                ),
            ],
            options={
                "db_table": "marketing_email_templates",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["firm", "status"], name="mkt_idx"),
                    models.Index(fields=["firm", "template_type"], name="mkt_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="CampaignExecution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recipient_count", models.IntegerField(default=0, help_text="Number of recipients")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("scheduled", "Scheduled"),
                            ("sending", "Sending"),
                            ("sent", "Sent"),
                            ("paused", "Paused"),
                            ("cancelled", "Cancelled"),
                            ("failed", "Failed"),
                        ],
                        default="draft",
                        help_text="Execution status",
                        max_length=20,
                    ),
                ),
                ("scheduled_for", models.DateTimeField(blank=True, help_text="When to send this campaign", null=True)),
                ("started_at", models.DateTimeField(blank=True, help_text="When campaign started sending", null=True)),
                ("completed_at", models.DateTimeField(blank=True, help_text="When campaign finished sending", null=True)),
                ("emails_sent", models.IntegerField(default=0, help_text="Emails successfully sent")),
                ("emails_failed", models.IntegerField(default=0, help_text="Failed sends")),
                ("emails_opened", models.IntegerField(default=0, help_text="Unique opens")),
                ("emails_clicked", models.IntegerField(default=0, help_text="Unique clicks")),
                ("emails_bounced", models.IntegerField(default=0, help_text="Bounces")),
                ("emails_unsubscribed", models.IntegerField(default=0, help_text="Unsubscribes")),
                (
                    "open_rate",
                    models.DecimalField(blank=True, decimal_places=2, help_text="Open rate percentage", max_digits=5, null=True),
                ),
                (
                    "click_rate",
                    models.DecimalField(
                        blank=True, decimal_places=2, help_text="Click-through rate percentage", max_digits=5, null=True
                    ),
                ),
                (
                    "bounce_rate",
                    models.DecimalField(blank=True, decimal_places=2, help_text="Bounce rate percentage", max_digits=5, null=True),
                ),
                ("is_ab_test", models.BooleanField(default=False, help_text="Is this an A/B test campaign?")),
                ("ab_variant", models.CharField(blank=True, help_text="Variant identifier (A, B, C, etc.)", max_length=10)),
                ("error_message", models.TextField(blank=True, help_text="Error message if execution failed")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "campaign",
                    models.ForeignKey(
                        help_text="Campaign being executed",
                        on_delete=models.CASCADE,
                        related_name="executions",
                        to="crm.campaign",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="created_campaign_executions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "email_template",
                    models.ForeignKey(
                        blank=True,
                        help_text="Email template used for this execution",
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="campaign_executions",
                        to="marketing.emailtemplate",
                    ),
                ),
                (
                    "segment",
                    models.ForeignKey(
                        blank=True,
                        help_text="Target segment for this campaign",
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="campaign_executions",
                        to="marketing.segment",
                    ),
                ),
            ],
            options={
                "db_table": "marketing_campaign_executions",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["campaign", "status"], name="mkt_idx"),
                    models.Index(fields=["status", "scheduled_for"], name="mkt_idx"),
                    models.Index(fields=["-created_at"], name="mkt_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="EntityTag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "entity_type",
                    models.CharField(
                        choices=[
                            ("lead", "Lead"),
                            ("prospect", "Prospect"),
                            ("client", "Client"),
                            ("campaign", "Campaign"),
                            ("contact", "Contact"),
                            ("account", "Account"),
                        ],
                        help_text="Type of entity being tagged",
                        max_length=20,
                    ),
                ),
                ("entity_id", models.BigIntegerField(help_text="ID of the entity being tagged")),
                (
                    "applied_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "auto_applied",
                    models.BooleanField(default=False, help_text="Was this tag automatically applied by a rule?"),
                ),
                (
                    "auto_rule_id",
                    models.BigIntegerField(blank=True, help_text="ID of automation rule that applied this tag", null=True),
                ),
                (
                    "applied_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="applied_tags",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "tag",
                    models.ForeignKey(
                        help_text="Tag being applied",
                        on_delete=models.CASCADE,
                        related_name="entity_tags",
                        to="marketing.tag",
                    ),
                ),
            ],
            options={
                "db_table": "marketing_entity_tags",
                "ordering": ["-applied_at"],
                "indexes": [
                    models.Index(fields=["tag", "entity_type"], name="mkt_idx"),
                    models.Index(fields=["entity_type", "entity_id"], name="mkt_idx"),
                    models.Index(fields=["applied_by", "-applied_at"], name="mkt_idx"),
                ],
                "unique_together": {("tag", "entity_type", "entity_id")},
            },
        ),
    ]
