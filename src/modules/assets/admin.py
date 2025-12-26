"""
Django Admin configuration for Assets models.
"""

from django.contrib import admin

from .models import Asset, MaintenanceLog


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["asset_tag", "name", "category", "status", "assigned_to", "purchase_date", "purchase_price"]
    list_filter = ["category", "status", "purchase_date"]
    search_fields = ["asset_tag", "name", "serial_number", "manufacturer"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Asset Information", {"fields": ("asset_tag", "name", "description", "category", "status", "assigned_to")}),
        ("Financial", {"fields": ("purchase_price", "purchase_date", "vendor", "useful_life_years", "salvage_value")}),
        ("Physical Details", {"fields": ("manufacturer", "model_number", "serial_number", "location")}),
        ("Warranty", {"fields": ("warranty_expiration",)}),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ["asset", "maintenance_type", "status", "scheduled_date", "completed_date", "cost", "performed_by"]
    list_filter = ["maintenance_type", "status", "scheduled_date"]
    search_fields = ["asset__asset_tag", "asset__name", "description", "performed_by"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Maintenance Information", {"fields": ("asset", "maintenance_type", "status", "description")}),
        ("Timeline", {"fields": ("scheduled_date", "completed_date")}),
        ("Service Provider", {"fields": ("performed_by", "vendor", "cost")}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )
