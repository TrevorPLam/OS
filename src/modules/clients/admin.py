"""
Django Admin configuration for Clients module.
"""

from django.contrib import admin

from modules.clients.models import (
    Client,
    ClientChatThread,
    ClientComment,
    ClientEngagement,
    ClientMessage,
    ClientNote,
    ClientPortalUser,
    ClientHealthScore,
    Contact,
    EngagementLine,
    Organization,
)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "status",
        "account_manager",
        "portal_enabled",
        "active_projects_count",
        "total_lifetime_value",
        "client_since",
    )
    list_filter = ("status", "portal_enabled", "client_since")
    search_fields = ("company_name", "primary_contact_name", "primary_contact_email")
    readonly_fields = ("created_at", "updated_at", "source_prospect", "source_proposal")
    filter_horizontal = ("assigned_team",)

    fieldsets = (
        (
            "Origin Tracking",
            {
                "fields": ("source_prospect", "source_proposal"),
                "classes": ("collapse",),
            },
        ),
        (
            "Company Information",
            {
                "fields": ("company_name", "industry", "website", "employee_count"),
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "primary_contact_name",
                    "primary_contact_email",
                    "primary_contact_phone",
                ),
            },
        ),
        (
            "Address",
            {
                "fields": ("street_address", "city", "state", "postal_code", "country"),
                "classes": ("collapse",),
            },
        ),
        (
            "Status & Team",
            {
                "fields": ("status", "account_manager", "assigned_team"),
            },
        ),
        (
            "Portal",
            {
                "fields": ("portal_enabled",),
            },
        ),
        (
            "Metrics",
            {
                "fields": ("total_lifetime_value", "active_projects_count", "client_since"),
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ClientPortalUser)
class ClientPortalUserAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "client",
        "role",
        "can_upload_documents",
        "can_view_billing",
        "invited_at",
        "last_login",
    )
    list_filter = ("role", "can_upload_documents", "can_view_billing")
    search_fields = ("user__username", "user__email", "client__company_name")
    readonly_fields = ("invited_at", "invited_by")

    fieldsets = (
        (
            "User & Client",
            {
                "fields": ("client", "user", "role"),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "can_upload_documents",
                    "can_view_billing",
                    "can_message_team",
                    "can_view_projects",
                ),
            },
        ),
        (
            "Audit",
            {
                "fields": ("invited_by", "invited_at", "last_login"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ClientNote)
class ClientNoteAdmin(admin.ModelAdmin):
    list_display = ("client", "author", "is_pinned", "created_at")
    list_filter = ("is_pinned", "created_at")
    search_fields = ("client__company_name", "note", "author__username")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            None,
            {
                "fields": ("client", "author", "note", "is_pinned"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ClientEngagement)
class ClientEngagementAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "contract",
        "version",
        "status",
        "start_date",
        "end_date",
        "contracted_value",
        "actual_revenue",
    )
    list_filter = ("status", "start_date")
    search_fields = ("client__company_name", "contract__contract_number")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Client & Contract",
            {
                "fields": ("client", "contract", "status"),
            },
        ),
        (
            "Versioning",
            {
                "fields": ("version", "parent_engagement"),
            },
        ),
        (
            "Timeline",
            {
                "fields": ("start_date", "end_date", "actual_end_date"),
            },
        ),
        (
            "Financial",
            {
                "fields": ("contracted_value", "actual_revenue"),
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ClientComment)
class ClientCommentAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "client",
        "author",
        "is_read_by_firm",
        "read_by",
        "created_at",
    )
    list_filter = ("is_read_by_firm", "created_at", "client")
    search_fields = (
        "comment",
        "task__title",
        "client__company_name",
        "author__username",
        "author__email",
    )
    readonly_fields = ("created_at", "updated_at", "read_at")

    fieldsets = (
        (
            "Comment Details",
            {
                "fields": ("client", "task", "author", "comment"),
            },
        ),
        (
            "Attachments",
            {
                "fields": ("has_attachment",),
            },
        ),
        (
            "Read Status",
            {
                "fields": ("is_read_by_firm", "read_by", "read_at"),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ClientChatThread)
class ClientChatThreadAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "date",
        "is_active",
        "message_count",
        "last_message_at",
        "last_message_by",
    )
    list_filter = ("is_active", "date", "client")
    search_fields = ("client__company_name",)
    readonly_fields = ("created_at", "updated_at", "archived_at", "message_count", "last_message_at", "last_message_by")

    fieldsets = (
        (
            "Thread Details",
            {
                "fields": ("client", "date", "is_active"),
            },
        ),
        (
            "Statistics",
            {
                "fields": ("message_count", "last_message_at", "last_message_by"),
            },
        ),
        (
            "Archive",
            {
                "fields": ("archived_at",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ClientMessage)
class ClientMessageAdmin(admin.ModelAdmin):
    list_display = (
        "sender",
        "thread",
        "message_type",
        "is_from_client",
        "is_read",
        "created_at",
    )
    list_filter = ("message_type", "is_from_client", "is_read", "created_at")
    search_fields = (
        "content",
        "sender__username",
        "sender__email",
        "thread__client__company_name",
    )
    readonly_fields = ("created_at", "updated_at", "read_at")

    fieldsets = (
        (
            "Message Details",
            {
                "fields": ("thread", "sender", "is_from_client", "message_type", "content"),
            },
        ),
        (
            "Attachment",
            {
                "fields": ("attachment_url", "attachment_filename", "attachment_size_bytes"),
                "classes": ("collapse",),
            },
        ),
        (
            "Read Status",
            {
                "fields": ("is_read", "read_by", "read_at"),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "client",
        "email",
        "phone",
        "job_title",
        "is_primary_contact",
        "is_active",
    )
    list_filter = (
        "is_active",
        "is_primary_contact",
        "can_approve_invoices",
        "preferred_contact_method",
    )
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "mobile_phone",
        "client__company_name",
    )
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("client", "portal_user", "created_by")

    fieldsets = (
        (
            "Client",
            {
                "fields": ("client",),
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "mobile_phone",
                ),
            },
        ),
        (
            "Professional Information",
            {
                "fields": ("job_title", "department"),
            },
        ),
        (
            "Contact Preferences",
            {
                "fields": (
                    "is_primary_contact",
                    "can_approve_invoices",
                    "receives_billing_emails",
                    "receives_project_updates",
                    "preferred_contact_method",
                ),
            },
        ),
        (
            "Communication Opt-Outs",
            {
                "fields": ("opt_out_marketing", "opt_out_sms"),
            },
        ),
        (
            "Portal Access",
            {
                "fields": ("portal_user",),
            },
        ),
        (
            "Status",
            {
                "fields": ("is_active",),
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(EngagementLine)
class EngagementLineAdmin(admin.ModelAdmin):
    list_display = (
        "engagement",
        "line_number",
        "description",
        "line_type",
        "status",
        "net_amount",
        "completion_percentage",
    )
    list_filter = ("line_type", "status", "is_billable")
    search_fields = (
        "description",
        "service_code",
        "engagement__client__company_name",
    )
    readonly_fields = ("created_at", "updated_at", "total_price", "net_amount")
    raw_id_fields = ("engagement",)

    fieldsets = (
        (
            "Engagement",
            {
                "fields": ("engagement", "line_number"),
            },
        ),
        (
            "Line Details",
            {
                "fields": (
                    "line_type",
                    "description",
                    "detailed_description",
                    "service_code",
                ),
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "quantity",
                    "unit_price",
                    "total_price",
                    "discount_percent",
                    "discount_amount",
                    "net_amount",
                ),
            },
        ),
        (
            "Timeline",
            {
                "fields": ("start_date", "end_date"),
            },
        ),
        (
            "Status & Progress",
            {
                "fields": ("status", "completion_percentage"),
            },
        ),
        (
            "Delivery",
            {
                "fields": ("delivery_template_code",),
            },
        ),
        (
            "Billing",
            {
                "fields": ("is_billable", "invoice_schedule"),
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "firm",
        "enable_cross_client_visibility",
        "created_at",
    )
    list_filter = ("firm", "enable_cross_client_visibility")
    search_fields = ("name", "description", "firm__name")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("created_by",)

    fieldsets = (
        (
            "Organization",
            {
                "fields": ("firm", "name", "description"),
            },
        ),
        (
            "Settings",
            {
                "fields": ("enable_cross_client_visibility",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ClientHealthScore)
class ClientHealthScoreAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "score",
        "score_trend",
        "engagement_score",
        "payment_score",
        "communication_score",
        "delivery_score",
        "is_at_risk",
        "last_calculated_at",
    )
    list_filter = ("is_at_risk", "score_trend", "last_calculated_at")
    search_fields = ("client__company_name",)
    readonly_fields = (
        "client",
        "score",
        "score_trend",
        "days_since_last_activity",
        "overdue_invoice_count",
        "overdue_invoice_amount",
        "avg_payment_delay_days",
        "email_response_rate",
        "project_completion_rate",
        "is_at_risk",
        "alert_sent_at",
        "previous_score",
        "score_history",
        "last_calculated_at",
        "created_at",
    )

    fieldsets = (
        (
            "Client",
            {
                "fields": ("client",),
            },
        ),
        (
            "Overall Score",
            {
                "fields": ("score", "score_trend", "previous_score", "is_at_risk"),
            },
        ),
        (
            "Factor Scores",
            {
                "fields": (
                    "engagement_score",
                    "payment_score",
                    "communication_score",
                    "delivery_score",
                ),
            },
        ),
        (
            "Factor Weights",
            {
                "fields": (
                    "engagement_weight",
                    "payment_weight",
                    "communication_weight",
                    "delivery_weight",
                ),
            },
        ),
        (
            "Metrics",
            {
                "fields": (
                    "days_since_last_activity",
                    "overdue_invoice_count",
                    "overdue_invoice_amount",
                    "avg_payment_delay_days",
                    "email_response_rate",
                    "project_completion_rate",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Alert Settings",
            {
                "fields": ("alert_threshold", "alert_sent_at"),
            },
        ),
        (
            "History",
            {
                "fields": ("score_history",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("last_calculated_at", "created_at"),
                "classes": ("collapse",),
            },
        ),
    )
