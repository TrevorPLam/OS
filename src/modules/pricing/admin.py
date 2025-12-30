"""
Django Admin configuration for Pricing module (DOC-09.2).

Provides admin interface for:
- RuleSet: Versioned pricing rule collections
- Quote: Mutable quote drafts
- QuoteVersion: Immutable quote snapshots
- QuoteLineItem: Line items within quote versions

TIER 0: All admin views respect firm tenancy.
DOC-09.2: QuoteVersion is read-only once accepted.
"""

from django.contrib import admin
from django.utils.html import format_html

from modules.pricing.models import Quote, QuoteLineItem, QuoteVersion, RuleSet


class QuoteLineItemInline(admin.TabularInline):
    """Inline admin for QuoteLineItem."""

    model = QuoteLineItem
    extra = 0
    readonly_fields = ["firm"]
    fields = [
        "line_number",
        "product_code",
        "name",
        "quantity",
        "unit_price",
        "amount",
        "billing_model",
        "billing_unit",
    ]


@admin.register(RuleSet)
class RuleSetAdmin(admin.ModelAdmin):
    """Admin interface for RuleSet model."""

    list_display = [
        "name",
        "code",
        "version",
        "status",
        "schema_version",
        "published_at",
        "firm",
    ]
    list_filter = ["status", "schema_version", "firm"]
    search_fields = ["name", "code", "checksum"]
    readonly_fields = [
        "checksum",
        "published_at",
        "deprecated_at",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        (
            "Identity",
            {
                "fields": [
                    "firm",
                    "name",
                    "code",
                    "version",
                    "schema_version",
                ]
            },
        ),
        (
            "Rules",
            {
                "fields": [
                    "rules_json",
                    "checksum",
                    "default_currency",
                ]
            },
        ),
        (
            "Status",
            {
                "fields": [
                    "status",
                    "published_at",
                    "deprecated_at",
                ]
            },
        ),
        (
            "Audit",
            {
                "fields": [
                    "created_at",
                    "created_by",
                    "updated_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    def get_readonly_fields(self, request, obj=None):
        """Make published rulesets read-only."""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.status == "published":
            readonly.extend(["rules_json", "name", "code", "version", "schema_version"])
        return readonly


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    """Admin interface for Quote model."""

    list_display = [
        "quote_number",
        "client",
        "status",
        "valid_until",
        "created_at",
        "firm",
    ]
    list_filter = ["status", "firm"]
    search_fields = ["quote_number", "client__company_name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (
            "Quote Details",
            {
                "fields": [
                    "firm",
                    "quote_number",
                    "client",
                    "status",
                ]
            },
        ),
        (
            "Versions",
            {
                "fields": [
                    "current_version",
                    "valid_until",
                ]
            },
        ),
        (
            "Audit",
            {
                "fields": [
                    "created_at",
                    "created_by",
                    "updated_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]


@admin.register(QuoteVersion)
class QuoteVersionAdmin(admin.ModelAdmin):
    """Admin interface for QuoteVersion model."""

    list_display = [
        "quote",
        "version_number",
        "status",
        "get_total_amount",
        "currency",
        "issued_at",
        "accepted_at",
    ]
    list_filter = ["status", "currency", "firm"]
    search_fields = ["quote__quote_number", "correlation_id"]
    readonly_fields = [
        "ruleset_checksum",
        "outputs_checksum",
        "created_at",
        "issued_at",
        "issued_by",
        "accepted_at",
        "accepted_by",
        "total_amount",
    ]
    inlines = [QuoteLineItemInline]
    fieldsets = [
        (
            "Version Details",
            {
                "fields": [
                    "firm",
                    "quote",
                    "version_number",
                    "status",
                ]
            },
        ),
        (
            "RuleSet Reference",
            {
                "fields": [
                    "ruleset",
                    "ruleset_checksum",
                ]
            },
        ),
        (
            "Evaluation Context",
            {
                "fields": [
                    "context_snapshot",
                    "correlation_id",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Evaluation Outputs",
            {
                "fields": [
                    "line_items",
                    "totals",
                    "assumptions",
                    "warnings",
                    "outputs_checksum",
                    "total_amount",
                    "currency",
                ]
            },
        ),
        (
            "Evaluation Trace",
            {
                "fields": [
                    "evaluation_trace",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Lifecycle",
            {
                "fields": [
                    "created_at",
                    "issued_at",
                    "issued_by",
                    "accepted_at",
                    "accepted_by",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    def get_total_amount(self, obj):
        """Display total amount with currency."""
        return format_html(
            "<strong>{} {:.2f}</strong>",
            obj.currency,
            obj.total_amount,
        )

    get_total_amount.short_description = "Total Amount"

    def get_readonly_fields(self, request, obj=None):
        """Make accepted quote versions completely read-only."""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.status == "accepted":
            # Make all fields read-only for accepted versions
            readonly.extend([
                "quote",
                "version_number",
                "ruleset",
                "context_snapshot",
                "line_items",
                "totals",
                "assumptions",
                "warnings",
                "evaluation_trace",
                "currency",
                "status",
            ])
        return readonly


@admin.register(QuoteLineItem)
class QuoteLineItemAdmin(admin.ModelAdmin):
    """Admin interface for QuoteLineItem model."""

    list_display = [
        "quote_version",
        "line_number",
        "product_code",
        "name",
        "quantity",
        "unit_price",
        "amount",
        "billing_model",
    ]
    list_filter = ["billing_model", "firm"]
    search_fields = ["name", "product_code", "quote_version__quote__quote_number"]
    readonly_fields = ["firm"]
    fieldsets = [
        (
            "Line Item Details",
            {
                "fields": [
                    "firm",
                    "quote_version",
                    "line_number",
                    "product_code",
                    "name",
                    "description",
                ]
            },
        ),
        (
            "Pricing",
            {
                "fields": [
                    "quantity",
                    "unit_price",
                    "amount",
                ]
            },
        ),
        (
            "Billing Configuration",
            {
                "fields": [
                    "billing_model",
                    "billing_unit",
                    "tax_category",
                ]
            },
        ),
        (
            "Additional Information",
            {
                "fields": [
                    "notes",
                ],
                "classes": ["collapse"],
            },
        ),
    ]
