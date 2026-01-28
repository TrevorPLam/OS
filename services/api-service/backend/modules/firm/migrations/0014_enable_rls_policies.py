from django.db import migrations, models


def _policy_name(table: str) -> str:
    """Generate a deterministic policy name under PostgreSQL's 63 char limit."""
    suffix = "_firm_rls"
    max_table_length = 63 - len(suffix)
    return f"{table[:max_table_length]}{suffix}"


def _tenant_tables(apps, connection):
    """Return managed tables that carry a firm FK and exist in the database."""
    firm_model = apps.get_model("firm", "Firm")
    tables = set()

    for model in apps.get_models():
        if not model._meta.managed:
            continue

        for field in model._meta.fields:
            if isinstance(field, models.ForeignKey) and field.name == "firm" and field.remote_field.model == firm_model:
                tables.add(model._meta.db_table)

    existing_tables = set(connection.introspection.table_names())
    return sorted(table for table in tables if table in existing_tables)


def enable_rls(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        return

    tables = _tenant_tables(apps, connection)
    with connection.cursor() as cursor:
        for table in tables:
            policy_name = _policy_name(table)
            quoted_table = schema_editor.quote_name(table)
            quoted_policy = schema_editor.quote_name(policy_name)

            cursor.execute(f"ALTER TABLE {quoted_table} ENABLE ROW LEVEL SECURITY")
            cursor.execute(f"ALTER TABLE {quoted_table} FORCE ROW LEVEL SECURITY")
            cursor.execute(
                f"""
                CREATE POLICY IF NOT EXISTS {quoted_policy}
                ON {quoted_table}
                USING (firm_id = current_setting('app.current_firm_id', true)::bigint)
                WITH CHECK (firm_id = current_setting('app.current_firm_id', true)::bigint)
                """
            )


def disable_rls(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        return

    tables = _tenant_tables(apps, connection)
    with connection.cursor() as cursor:
        for table in tables:
            policy_name = _policy_name(table)
            quoted_table = schema_editor.quote_name(table)
            quoted_policy = schema_editor.quote_name(policy_name)

            cursor.execute(f"DROP POLICY IF EXISTS {quoted_policy} ON {quoted_table}")
            cursor.execute(f"ALTER TABLE {quoted_table} NO FORCE ROW LEVEL SECURITY")
            cursor.execute(f"ALTER TABLE {quoted_table} DISABLE ROW LEVEL SECURITY")


class Migration(migrations.Migration):
    dependencies = [
        ("accounting_integrations", "0001_initial"),
        ("ad_sync", "0001_initial"),
        ("assets", "0001_initial"),
        ("automation", "0001_initial"),
        ("calendar", "0017_add_group_event_models"),
        ("clients", "0014_add_contact_location_fields"),
        ("core", "0002_erasure_request_model"),
        ("crm", "0009_add_deal_alerts"),
        ("delivery", "0001_initial"),
        ("documents", "0005_add_granular_permissions"),
        ("email_ingestion", "0002_ingestion_retry_safety"),
        ("esignature", "0002_webhookevent_idempotency_key"),
        ("finance", "0014_webhook_idempotency_keys"),
        ("firm", "0013_remove_provisioninglog_firm_and_more"),
        ("integrations", "0001_initial"),
        ("jobs", "0001_initial"),
        ("knowledge", "0001_initial"),
        ("marketing", "0005_segment_memberships"),
        ("onboarding", "0001_initial"),
        ("orchestration", "0001_initial"),
        ("pricing", "0001_initial"),
        ("projects", "0007_utilization_reporting_materialized_views"),
        ("recurrence", "0001_initial"),
        ("sms", "0003_smswebhookevent_idempotency_key"),
        ("snippets", "0001_initial"),
        ("support", "0001_initial"),
        ("tracking", "0003_sitemessageimpression"),
        ("webhooks", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(enable_rls, disable_rls),
    ]
