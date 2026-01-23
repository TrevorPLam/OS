"""
Migration for DOC-27.1: Role-based views.

Adds new role choices and updates existing roles to match docs/03-reference/requirements/DOC-27.md.
"""

from django.db import migrations, models


def migrate_legacy_roles(apps, schema_editor):
    """
    Migrate legacy roles to DOC-27.1 roles.

    owner -> firm_admin
    admin -> firm_admin
    contractor -> staff
    staff -> staff (no change)
    """
    FirmMembership = apps.get_model("firm", "FirmMembership")

    # Migrate owner and admin to firm_admin
    FirmMembership.objects.filter(role__in=["owner", "admin"]).update(role="firm_admin")

    # contractor already maps to staff in model logic, but let's be explicit
    FirmMembership.objects.filter(role="contractor").update(role="staff")


class Migration(migrations.Migration):
    dependencies = [
        ("firm", "0010_firm_provisioning"),  # Update to actual latest migration
    ]

    operations = [
        migrations.AlterField(
            model_name="firmmembership",
            name="role",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("firm_admin", "Firm Admin"),
                    ("partner", "Partner/Owner"),
                    ("manager", "Manager"),
                    ("staff", "Staff"),
                    ("billing", "Billing"),
                    ("readonly", "Read-Only"),
                    # Legacy roles (backward compatibility)
                    ("owner", "Legacy Owner"),
                    ("admin", "Legacy Admin"),
                    ("contractor", "Contractor"),
                ],
                default="staff",
            ),
        ),
        migrations.RunPython(migrate_legacy_roles, migrations.RunPython.noop),
    ]
