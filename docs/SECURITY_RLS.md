# Row-Level Security (RLS) Plan

Last Updated: 2026-01-06

## Enforcement mechanics

- **Session guard:** `FirmRLSSessionMiddleware` sets `app.current_firm_id` on PostgreSQL connections for every request and resets it afterward to prevent context bleed between tenants.
- **Background jobs:** Use `firm_db_session(firm)` from `modules.firm.utils` to wrap job handlers so RLS policies see the correct tenant when reading or writing data.
- **Database policy:** Migration `firm/0014_enable_rls_policies.py` enables RLS and installs `firm_id = current_setting('app.current_firm_id', true)::bigint` policies on every managed model that has a `firm` foreign key. Policies are forced so even table owners honor firm isolation.
- **Defaults:** If `app.current_firm_id` is missing, policies evaluate to NULL and reject access—sessions must be scoped explicitly.
- **Validation:** In psql, run `\d+ <table>` to verify `Row security: enabled, forced` and `\dRp+` to confirm `<table>_firm_rls` exists for newly added tables.

## Tenant-scoped tables (managed models)

- accounting_integrations: `accounting_customer_sync_mappings`, `accounting_invoice_sync_mappings`, `accounting_oauth_connections`
- ad_sync: `ad_group_mapping`, `ad_provisioning_rule`, `ad_sync_config`, `ad_sync_log`, `ad_user_mapping`
- assets: `assets_assets`, `assets_maintenance_logs`
- automation: `automation_contact_flow_state`, `automation_workflow`, `automation_workflow_analytics`, `automation_workflow_edge`, `automation_workflow_execution`, `automation_workflow_goal`, `automation_workflow_node`, `automation_workflow_trigger`
- calendar: `calendar_appointment_types`, `calendar_appointments`, `calendar_availability_profiles`, `calendar_booking_links`, `calendar_connections`, `calendar_meeting_polls`, `calendar_meeting_workflows`, `calendar_oauth_authorization_codes`, `calendar_oauth_connections`, `calendar_sync_attempts`
- clients: `clients_client`, `clients_contact_bulk_update`, `clients_contact_import`, `clients_engagement`, `clients_engagement_line`, `clients_organization`, `clients_portal_branding`
- communications: `communications_client_message_thread`, `communications_conversation`, `communications_conversation_link`, `communications_message`, `communications_message_attachment`, `communications_message_notification`, `communications_message_read_receipt`, `communications_message_revision`, `communications_participant`
- core: `core_purged_content`
- crm: `crm_account`, `crm_activities`, `crm_assignment_rules`, `crm_campaigns`, `crm_contracts`, `crm_deal_assignment_rule`, `crm_deal_stage_automation`, `crm_deals`, `crm_enrichment_provider`, `crm_intake_forms`, `crm_leads`, `crm_pipelines`, `crm_product`, `crm_proposals`, `crm_prospects`, `crm_stage_automations`, `scoring_rules`
- delivery: `delivery_edge`, `delivery_node`, `delivery_template`, `delivery_template_instantiation`
- documents: `documents_access_logs`, `documents_comments`, `documents_documents`, `documents_external_shares`, `documents_file_request_reminders`, `documents_file_requests`, `documents_folder_comments`, `documents_folders`, `documents_locks`, `documents_share_accesses`, `documents_share_permissions`, `documents_versions`, `documents_view_logs`
- email_ingestion: `email_ingestion_artifacts`, `email_ingestion_attempts`, `email_ingestion_connections`
- esignature: `esignature_docusign_connections`, `esignature_envelopes`, `esignature_webhook_events`
- finance: `finance_bills`, `finance_chargeback`, `finance_credit_ledger`, `finance_invoices`, `finance_ledger_entries`, `finance_payment_allocations`, `finance_payment_dispute`, `finance_payment_failure`, `finance_payments`, `finance_project_profitability`, `finance_service_line_profitability`, `finance_square_webhook_events`, `finance_stripe_webhook_events`
- firm: `firm_audit_events`, `firm_break_glass_session`, `firm_membership`, `firm_offboarding_record`
- integrations: `integrations_google_analytics`, `integrations_salesforce_connection`, `integrations_salesforce_sync_log`, `integrations_slack`, `integrations_slack_message_log`
- jobs: `job_dlq`, `job_queue`
- knowledge: `knowledge_attachments`, `knowledge_items`, `knowledge_reviews`, `knowledge_versions`
- marketing: `marketing_email_domains`, `marketing_email_templates`, `marketing_segments`, `marketing_tags`
- onboarding: `onboarding_processes`, `onboarding_templates`
- orchestration: `orchestration_definition`, `orchestration_dlq`, `orchestration_execution`, `orchestration_step_execution`
- pricing: `pricing_quote`, `pricing_quote_line_item`, `pricing_quote_version`, `pricing_ruleset`
- projects: `projects_projects`, `projects_resource_capacity`, `projects_templates`
- recurrence: `recurrence_generation`, `recurrence_rule`
- sms: `sms_campaigns`, `sms_conversations`, `sms_messages`, `sms_opt_outs`, `sms_phone_numbers`, `sms_templates`, `sms_webhook_events`
- snippets: `snippet_folders`, `snippets`
- support: `support_sla_policies`, `support_surveys`, `support_tickets`
- tracking: `tracking_abuse_event`, `tracking_event`, `tracking_key`, `tracking_key_audit`, `tracking_session`, `tracking_site_message`, `tracking_site_message_impression`
- webhooks: `webhooks_endpoint`

> Note: The communications module currently lacks migrations in the repo; enable RLS automatically once its schema is present.

## Usage guidance

- Wrap background work that touches tenant data in `with firm_db_session(firm): ...`.
- Request handlers automatically get session scoping via middleware; avoid bypassing the middleware stack when serving HTTP.
- If you see `app.current_firm_id is not set` or permission errors in PostgreSQL, ensure the session context is set before issuing queries.
- For newly added tenant-scoped models, ensure the `firm` FK exists so the RLS migration sweep can attach policies automatically.

## Validation

- Security tests include raw SQL probes to confirm cross-firm SELECT/INSERT attempts fail under RLS (skipped when PostgreSQL is unavailable).
