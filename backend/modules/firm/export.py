"""
Firm data export helpers for offboarding workflows.

Defines export schema, data domains, integrity checks, and retention sequencing.
"""

import hashlib
import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.clients.models import (
    Client,
    ClientChatThread,
    ClientComment,
    ClientEngagement,
    ClientMessage,
    ClientNote,
    ClientPortalUser,
    Organization,
)
from modules.core.purge import PurgedContent
from modules.finance.models import (
    Bill,
    Chargeback,
    CreditLedgerEntry,
    Invoice,
    LedgerEntry,
    PaymentDispute,
    PaymentFailure,
)
from modules.firm.audit import AuditEvent
from modules.projects.models import Project, Task, TimeEntry

EXPORT_SCHEMA_VERSION = "2025-02-01"
DEFAULT_RETENTION_DAYS = 30
DEFAULT_PURGE_GRACE_DAYS = 7


def _model_field_names(model_class, extra_fields=None):
    extra_fields = extra_fields or []
    return [field.attname for field in model_class._meta.fields] + list(extra_fields)


def export_schema():
    """Return the export schema definition for all supported domains."""
    return {
        "version": EXPORT_SCHEMA_VERSION,
        "domains": {
            "clients": {
                "organizations": {
                    "model": "clients.Organization",
                    "fields": _model_field_names(Organization),
                },
                "clients": {
                    "model": "clients.Client",
                    "fields": _model_field_names(Client, extra_fields=["assigned_team_ids"]),
                },
                "portal_users": {
                    "model": "clients.ClientPortalUser",
                    "fields": _model_field_names(ClientPortalUser),
                },
                "notes": {
                    "model": "clients.ClientNote",
                    "fields": _model_field_names(ClientNote),
                },
                "engagements": {
                    "model": "clients.ClientEngagement",
                    "fields": _model_field_names(ClientEngagement),
                },
                "comments": {
                    "model": "clients.ClientComment",
                    "fields": _model_field_names(ClientComment),
                },
                "chat_threads": {
                    "model": "clients.ClientChatThread",
                    "fields": _model_field_names(ClientChatThread),
                },
                "messages": {
                    "model": "clients.ClientMessage",
                    "fields": _model_field_names(ClientMessage),
                },
            },
            "projects": {
                "projects": {
                    "model": "projects.Project",
                    "fields": _model_field_names(Project),
                },
                "tasks": {
                    "model": "projects.Task",
                    "fields": _model_field_names(Task),
                },
                "time_entries": {
                    "model": "projects.TimeEntry",
                    "fields": _model_field_names(TimeEntry),
                },
            },
            "billing": {
                "invoices": {
                    "model": "finance.Invoice",
                    "fields": _model_field_names(Invoice),
                },
                "payment_disputes": {
                    "model": "finance.PaymentDispute",
                    "fields": _model_field_names(PaymentDispute),
                },
                "payment_failures": {
                    "model": "finance.PaymentFailure",
                    "fields": _model_field_names(PaymentFailure),
                },
                "chargebacks": {
                    "model": "finance.Chargeback",
                    "fields": _model_field_names(Chargeback),
                },
                "bills": {
                    "model": "finance.Bill",
                    "fields": _model_field_names(Bill),
                },
                "ledger_entries": {
                    "model": "finance.LedgerEntry",
                    "fields": _model_field_names(LedgerEntry),
                },
                "credit_ledger_entries": {
                    "model": "finance.CreditLedgerEntry",
                    "fields": _model_field_names(CreditLedgerEntry),
                },
            },
            "audit": {
                "events": {
                    "model": "firm.AuditEvent",
                    "fields": _model_field_names(AuditEvent),
                },
                "purged_content": {
                    "model": "core.PurgedContent",
                    "fields": _model_field_names(PurgedContent),
                },
            },
        },
    }


def _serialize_instances(instances, field_names, extra_field_getter=None):
    data = []
    for instance in instances:
        record = {field: getattr(instance, field) for field in field_names if hasattr(instance, field)}
        if extra_field_getter:
            record.update(extra_field_getter(instance))
        data.append(record)
    return data


def _assigned_team_ids(client):
    return {"assigned_team_ids": list(client.assigned_team.values_list("id", flat=True))}


def _export_domains(firm):
    organizations = Organization.objects.filter(firm=firm)
    clients = Client.objects.filter(firm=firm).prefetch_related("assigned_team")
    portal_users = ClientPortalUser.objects.filter(client__firm=firm)
    notes = ClientNote.objects.filter(client__firm=firm)
    engagements = ClientEngagement.objects.filter(firm=firm)
    comments = ClientComment.objects.filter(client__firm=firm)
    chat_threads = ClientChatThread.objects.filter(client__firm=firm)
    messages = ClientMessage.objects.filter(thread__client__firm=firm)

    projects = Project.objects.filter(firm=firm)
    tasks = Task.objects.filter(project__firm=firm)
    time_entries = TimeEntry.objects.filter(project__firm=firm)

    invoices = Invoice.objects.filter(firm=firm)
    disputes = PaymentDispute.objects.filter(firm=firm)
    failures = PaymentFailure.objects.filter(firm=firm)
    chargebacks = Chargeback.objects.filter(firm=firm)
    bills = Bill.objects.filter(firm=firm)
    ledger_entries = LedgerEntry.objects.filter(firm=firm)
    credit_entries = CreditLedgerEntry.objects.filter(firm=firm)

    audit_events = AuditEvent.objects.filter(firm=firm)
    purged_content = PurgedContent.objects.filter(firm=firm)

    schema = export_schema()
    client_fields = schema["domains"]["clients"]["clients"]["fields"]
    return {
        "clients": {
            "organizations": _serialize_instances(
                organizations, schema["domains"]["clients"]["organizations"]["fields"]
            ),
            "clients": _serialize_instances(clients, client_fields, _assigned_team_ids),
            "portal_users": _serialize_instances(portal_users, schema["domains"]["clients"]["portal_users"]["fields"]),
            "notes": _serialize_instances(notes, schema["domains"]["clients"]["notes"]["fields"]),
            "engagements": _serialize_instances(engagements, schema["domains"]["clients"]["engagements"]["fields"]),
            "comments": _serialize_instances(comments, schema["domains"]["clients"]["comments"]["fields"]),
            "chat_threads": _serialize_instances(chat_threads, schema["domains"]["clients"]["chat_threads"]["fields"]),
            "messages": _serialize_instances(messages, schema["domains"]["clients"]["messages"]["fields"]),
        },
        "projects": {
            "projects": _serialize_instances(projects, schema["domains"]["projects"]["projects"]["fields"]),
            "tasks": _serialize_instances(tasks, schema["domains"]["projects"]["tasks"]["fields"]),
            "time_entries": _serialize_instances(time_entries, schema["domains"]["projects"]["time_entries"]["fields"]),
        },
        "billing": {
            "invoices": _serialize_instances(invoices, schema["domains"]["billing"]["invoices"]["fields"]),
            "payment_disputes": _serialize_instances(
                disputes, schema["domains"]["billing"]["payment_disputes"]["fields"]
            ),
            "payment_failures": _serialize_instances(
                failures, schema["domains"]["billing"]["payment_failures"]["fields"]
            ),
            "chargebacks": _serialize_instances(chargebacks, schema["domains"]["billing"]["chargebacks"]["fields"]),
            "bills": _serialize_instances(bills, schema["domains"]["billing"]["bills"]["fields"]),
            "ledger_entries": _serialize_instances(
                ledger_entries, schema["domains"]["billing"]["ledger_entries"]["fields"]
            ),
            "credit_ledger_entries": _serialize_instances(
                credit_entries, schema["domains"]["billing"]["credit_ledger_entries"]["fields"]
            ),
        },
        "audit": {
            "events": _serialize_instances(audit_events, schema["domains"]["audit"]["events"]["fields"]),
            "purged_content": _serialize_instances(
                purged_content, schema["domains"]["audit"]["purged_content"]["fields"]
            ),
        },
    }


def _build_manifest(domains):
    manifest = {"counts": {}, "total_records": 0}
    for domain_name, datasets in domains.items():
        manifest["counts"][domain_name] = {}
        for dataset_name, records in datasets.items():
            count = len(records)
            manifest["counts"][domain_name][dataset_name] = count
            manifest["total_records"] += count
    return manifest


def _collect_ids(records, key="id"):
    return {record[key] for record in records if record.get(key) is not None}


def _check_fk_membership(records, key, allowed_ids):
    return sorted({record[key] for record in records if record.get(key) not in allowed_ids})


def _integrity_report(firm, domains):
    checks = []
    firm_id = firm.id

    client_ids = _collect_ids(domains["clients"]["clients"])
    organization_ids = _collect_ids(domains["clients"]["organizations"])
    engagement_ids = _collect_ids(domains["clients"]["engagements"])
    project_ids = _collect_ids(domains["projects"]["projects"])
    task_ids = _collect_ids(domains["projects"]["tasks"])
    invoice_ids = _collect_ids(domains["billing"]["invoices"])

    invalid_client_orgs = _check_fk_membership(
        domains["clients"]["clients"], "organization_id", organization_ids | {None}
    )
    checks.append(
        {
            "name": "clients.organization_links",
            "status": "ok" if not invalid_client_orgs else "failed",
            "details": {"invalid_organization_ids": invalid_client_orgs},
        }
    )

    invalid_project_clients = _check_fk_membership(domains["projects"]["projects"], "client_id", client_ids)
    checks.append(
        {
            "name": "projects.client_links",
            "status": "ok" if not invalid_project_clients else "failed",
            "details": {"invalid_client_ids": invalid_project_clients},
        }
    )

    invalid_task_projects = _check_fk_membership(domains["projects"]["tasks"], "project_id", project_ids)
    checks.append(
        {
            "name": "projects.task_links",
            "status": "ok" if not invalid_task_projects else "failed",
            "details": {"invalid_project_ids": invalid_task_projects},
        }
    )

    invalid_time_projects = _check_fk_membership(domains["projects"]["time_entries"], "project_id", project_ids)
    invalid_time_tasks = _check_fk_membership(domains["projects"]["time_entries"], "task_id", task_ids | {None})
    checks.append(
        {
            "name": "projects.time_entry_links",
            "status": "ok" if not invalid_time_projects and not invalid_time_tasks else "failed",
            "details": {
                "invalid_project_ids": invalid_time_projects,
                "invalid_task_ids": invalid_time_tasks,
            },
        }
    )

    invalid_invoice_clients = _check_fk_membership(domains["billing"]["invoices"], "client_id", client_ids)
    invalid_invoice_projects = _check_fk_membership(domains["billing"]["invoices"], "project_id", project_ids | {None})
    invalid_invoice_engagements = _check_fk_membership(
        domains["billing"]["invoices"], "engagement_id", engagement_ids | {None}
    )
    checks.append(
        {
            "name": "billing.invoice_links",
            "status": (
                "ok"
                if not invalid_invoice_clients and not invalid_invoice_projects and not invalid_invoice_engagements
                else "failed"
            ),
            "details": {
                "invalid_client_ids": invalid_invoice_clients,
                "invalid_project_ids": invalid_invoice_projects,
                "invalid_engagement_ids": invalid_invoice_engagements,
            },
        }
    )

    invalid_dispute_invoices = _check_fk_membership(domains["billing"]["payment_disputes"], "invoice_id", invoice_ids)
    invalid_failure_invoices = _check_fk_membership(domains["billing"]["payment_failures"], "invoice_id", invoice_ids)
    invalid_chargeback_invoices = _check_fk_membership(domains["billing"]["chargebacks"], "invoice_id", invoice_ids)
    checks.append(
        {
            "name": "billing.dispute_links",
            "status": (
                "ok"
                if not invalid_dispute_invoices and not invalid_failure_invoices and not invalid_chargeback_invoices
                else "failed"
            ),
            "details": {
                "invalid_dispute_invoice_ids": invalid_dispute_invoices,
                "invalid_failure_invoice_ids": invalid_failure_invoices,
                "invalid_chargeback_invoice_ids": invalid_chargeback_invoices,
            },
        }
    )

    invalid_domain_firms = []
    for domain_name, datasets in domains.items():
        for dataset_name, records in datasets.items():
            for record in records:
                record_firm_id = record.get("firm_id")
                if record_firm_id is not None and record_firm_id != firm_id:
                    invalid_domain_firms.append(
                        {
                            "domain": domain_name,
                            "dataset": dataset_name,
                            "id": record.get("id"),
                            "firm_id": record_firm_id,
                        }
                    )
    checks.append(
        {
            "name": "tenant_isolation.firm_id_match",
            "status": "ok" if not invalid_domain_firms else "failed",
            "details": {"mismatched_firm_records": invalid_domain_firms},
        }
    )

    overall_status = "ok" if all(check["status"] == "ok" for check in checks) else "failed"
    return {"status": overall_status, "checks": checks}


def _retention_plan(retention_days, purge_grace_days):
    now = timezone.now()
    retention_expires_at = now + timedelta(days=retention_days)
    purge_scheduled_at = retention_expires_at + timedelta(days=purge_grace_days)
    return {
        "retention_days": retention_days,
        "purge_grace_days": purge_grace_days,
        "retention_expires_at": retention_expires_at,
        "purge_scheduled_at": purge_scheduled_at,
        "sequence": [
            {
                "step": "export_complete",
                "status": "completed",
                "completed_at": now,
            },
            {
                "step": "retain_data",
                "status": "scheduled",
                "not_before": retention_expires_at,
            },
            {
                "step": "purge_eligible",
                "status": "scheduled",
                "not_before": purge_scheduled_at,
            },
        ],
    }


def _checksum_payload(payload):
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def export_firm_data(
    *,
    firm,
    requested_by=None,
    retention_days=DEFAULT_RETENTION_DAYS,
    purge_grace_days=DEFAULT_PURGE_GRACE_DAYS,
):
    """Export firm data with schema, integrity checks, and retention sequencing."""
    if retention_days is None:
        retention_days = DEFAULT_RETENTION_DAYS
    if purge_grace_days is None:
        purge_grace_days = DEFAULT_PURGE_GRACE_DAYS
    domains = _export_domains(firm)
    manifest = _build_manifest(domains)
    integrity = _integrity_report(firm, domains)
    retention = _retention_plan(retention_days, purge_grace_days)

    payload = {
        "schema": export_schema(),
        "generated_at": timezone.now(),
        "firm": {
            "id": firm.id,
            "name": firm.name,
            "slug": firm.slug,
            "status": firm.status,
        },
        "requested_by": {
            "id": requested_by.id if requested_by else None,
            "email": requested_by.email if requested_by else None,
        },
        "domains": domains,
        "manifest": manifest,
        "integrity": integrity,
        "retention": retention,
    }
    payload["checksum"] = _checksum_payload(payload)
    return payload


def resolve_requested_by(user_id):
    if not user_id:
        return None
    return get_user_model().objects.filter(id=user_id).first()
