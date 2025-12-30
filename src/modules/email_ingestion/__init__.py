"""
Email Ingestion Module.

Implements email ingestion from Gmail/Outlook with governed artifact storage,
mapping suggestions, triage workflow, and audit trail.

Complies with docs/15 EMAIL_INGESTION_SPEC.
"""

default_app_config = "modules.email_ingestion.apps.EmailIngestionConfig"
