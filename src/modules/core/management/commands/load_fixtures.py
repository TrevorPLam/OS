"""
Management command to seed development fixtures for local environments.

Creates a deterministic, multi-tenant dataset so developers can explore the
full product surface without manual data entry.

Meta-commentary:
- **Current Status:** Focused on deterministic dev fixtures; no destructive reset mode.
- **Follow-up (T-054):** If reset behavior is needed, add a guarded --reset flag.
- **Assumption:** Local dev databases can accept synthetic data without tenant side effects.
- **Limitation:** Designed for local/dev usage only; not intended for production use.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from modules.clients.models import Client
from modules.core.encryption import field_encryption_service
from modules.documents.models import Document, Folder
from modules.finance.models import Invoice
from modules.firm.models import Firm, FirmMembership
from modules.projects.models import Project


@dataclass(frozen=True)
class FixtureSummary:
    """Tracks created fixture counts for reporting."""

    firms_created: int = 0
    users_created: int = 0
    memberships_created: int = 0
    clients_created: int = 0
    projects_created: int = 0
    folders_created: int = 0
    documents_created: int = 0
    invoices_created: int = 0


class Command(BaseCommand):
    help = "Load deterministic sample data for local development (T-054)"

    def handle(self, *args, **options):
        """
        Seed deterministic fixture data.

        Data mapping:
        - 3 firms (active, trial, suspended) for tenant boundary coverage.
        - 10 users and firm memberships across the 3 firms (role mix).
        - 20 clients with status and autopay edge cases.
        - 30 projects with status variety and acceptance gates.
        - 50 documents tied to folders/clients/projects with lifecycle edge cases.
        - 10 invoices with paid/partial/overdue scenarios.
        """
        summary = FixtureSummary()
        now = timezone.now()

        # Commentary: keep everything deterministic for repeatable local runs.
        firm_specs = [
            {
                "name": "Fixture Firm Alpha",
                "slug": "fixture-firm-alpha",
                "status": "active",
                "subscription_tier": "professional",
            },
            {
                "name": "Fixture Firm Beta",
                "slug": "fixture-firm-beta",
                "status": "trial",
                "subscription_tier": "starter",
                "trial_ends_at": now + timedelta(days=14),
            },
            {
                "name": "Fixture Firm Gamma",
                "slug": "fixture-firm-gamma",
                "status": "suspended",
                "subscription_tier": "enterprise",
            },
        ]

        user_specs = [
            ("fixture_admin_1", "firm_admin", 0),
            ("fixture_manager_1", "manager", 0),
            ("fixture_staff_1", "staff", 0),
            ("fixture_billing_1", "billing", 0),
            ("fixture_admin_2", "firm_admin", 1),
            ("fixture_manager_2", "manager", 1),
            ("fixture_staff_2", "staff", 1),
            ("fixture_admin_3", "firm_admin", 2),
            ("fixture_staff_3", "staff", 2),
            ("fixture_readonly_3", "readonly", 2),
        ]

        with transaction.atomic():
            firms, firm_summary = self._create_firms(firm_specs)
            summary = self._merge_summary(summary, firm_summary)

            users, user_summary = self._create_users(user_specs, firms)
            summary = self._merge_summary(summary, user_summary)

            clients, client_summary = self._create_clients(firms, users, now)
            summary = self._merge_summary(summary, client_summary)

            projects, project_summary = self._create_projects(firms, clients, users, now)
            summary = self._merge_summary(summary, project_summary)

            folders, folder_summary = self._create_folders(firms, clients, users)
            summary = self._merge_summary(summary, folder_summary)

            document_summary = self._create_documents(firms, clients, projects, folders, users, now)
            summary = self._merge_summary(summary, document_summary)

            invoice_summary = self._create_invoices(firms, clients, projects, users, now)
            summary = self._merge_summary(summary, invoice_summary)

            # Commentary: update firm counters after all fixtures are created.
            self._refresh_firm_counters(firms, clients)

        self._report_summary(summary)

    def _create_firms(self, firm_specs: Iterable[dict]) -> tuple[list[Firm], FixtureSummary]:
        created = 0
        firms: list[Firm] = []
        for spec in firm_specs:
            firm, was_created = Firm.objects.get_or_create(
                name=spec["name"],
                defaults={
                    "slug": spec["slug"],
                    "status": spec["status"],
                    "subscription_tier": spec["subscription_tier"],
                    "trial_ends_at": spec.get("trial_ends_at"),
                    "timezone": "America/New_York",
                    "currency": "USD",
                },
            )
            if was_created:
                created += 1
            firms.append(firm)
        return firms, FixtureSummary(firms_created=created)

    def _create_users(
        self,
        user_specs: Iterable[tuple[str, str, int]],
        firms: list[Firm],
    ) -> tuple[list, FixtureSummary]:
        created_users = 0
        created_memberships = 0
        users = []
        user_model = get_user_model()

        for username, role, firm_index in user_specs:
            email = f"{username}@fixture.local"
            user, was_created = user_model.objects.get_or_create(
                username=username,
                defaults={"email": email, "is_staff": True},
            )
            if was_created:
                user.set_password(os.environ.get("FIXTURE_USER_PASSWORD", "fixture-password"))
                user.save(update_fields=["password"])
                created_users += 1
            users.append(user)

            firm = firms[firm_index]
            membership, membership_created = FirmMembership.objects.get_or_create(
                firm=firm,
                user=user,
                defaults={"role": role},
            )
            if membership_created:
                created_memberships += 1
            elif membership.role != role:
                membership.role = role
                membership.save()

        return users, FixtureSummary(users_created=created_users, memberships_created=created_memberships)

    def _create_clients(
        self,
        firms: list[Firm],
        users: list,
        now: timezone.datetime,
    ) -> tuple[list[Client], FixtureSummary]:
        created = 0
        clients: list[Client] = []
        total_clients = 20
        firm_distribution = [8, 6, 6]
        client_counter = 0

        for firm_index, client_count in enumerate(firm_distribution):
            firm = firms[firm_index]
            firm_users = self._users_for_firm(users, firm)

            for _ in range(client_count):
                client_counter += 1
                company_name = f"Fixture Client {firm_index + 1}-{client_counter}"
                status = "active"
                if client_counter % 7 == 0:
                    status = "inactive"
                elif client_counter % 11 == 0:
                    status = "terminated"

                defaults = {
                    "primary_contact_name": f"Contact {client_counter}",
                    "primary_contact_email": f"contact{client_counter}@fixture.local",
                    "primary_contact_phone": f"+1-555-010{client_counter:02d}",
                    "city": "Austin",
                    "state": "TX",
                    "postal_code": "73301",
                    "country": "USA",
                    "status": status,
                    "client_since": (now - timedelta(days=30 + client_counter)).date(),
                    "account_manager": firm_users[client_counter % len(firm_users)],
                    "portal_enabled": client_counter % 4 == 0,
                }

                client, was_created = Client.objects.get_or_create(
                    firm=firm,
                    company_name=company_name,
                    defaults=defaults,
                )

                if was_created:
                    created += 1
                    # Edge cases: autopay + consent tracking for a subset of clients.
                    if client_counter % 5 == 0:
                        client.autopay_enabled = True
                        client.autopay_payment_method_id = f"pm_fixture_{client_counter:04d}"
                        client.autopay_activated_at = now
                        client.autopay_activated_by = client.account_manager
                    if client_counter % 6 == 0:
                        client.marketing_opt_in = True
                        client.consent_timestamp = now - timedelta(days=7)
                        client.consent_source = "fixture_seed"
                    if client.portal_enabled:
                        client.tos_accepted = True
                        client.tos_accepted_at = now - timedelta(days=2)
                        client.tos_version = "fixture-v1"
                    client.save(update_fields=[
                        "autopay_enabled",
                        "autopay_payment_method_id",
                        "autopay_activated_at",
                        "autopay_activated_by",
                        "marketing_opt_in",
                        "consent_timestamp",
                        "consent_source",
                        "tos_accepted",
                        "tos_accepted_at",
                        "tos_version",
                    ])

                clients.append(client)

        if created < total_clients:
            self.stdout.write(
                self.style.WARNING(
                    f"Clients already exist; created {created} of {total_clients} requested."
                )
            )

        return clients, FixtureSummary(clients_created=created)

    def _create_projects(
        self,
        firms: list[Firm],
        clients: list[Client],
        users: list,
        now: timezone.datetime,
    ) -> tuple[list[Project], FixtureSummary]:
        created = 0
        projects: list[Project] = []
        project_counter = 0
        status_cycle = ["planning", "in_progress", "on_hold", "completed"]

        for client in clients:
            firm_users = self._users_for_firm(users, client.firm)
            for _ in range(2 if project_counter < 10 else 1):
                project_counter += 1
                status = status_cycle[project_counter % len(status_cycle)]
                start_date = (now - timedelta(days=60 + project_counter)).date()
                end_date = start_date + timedelta(days=90)

                project, was_created = Project.objects.get_or_create(
                    firm=client.firm,
                    project_code=f"F{client.firm_id}-PRJ-{project_counter:03d}",
                    defaults={
                        "client": client,
                        "name": f"{client.company_name} Engagement {project_counter}",
                        "description": "Fixture project for development workflows.",
                        "status": status,
                        "billing_type": "time_and_materials",
                        "project_manager": firm_users[project_counter % len(firm_users)],
                        "start_date": start_date,
                        "end_date": end_date,
                        "budget": Decimal("25000.00"),
                        "hourly_rate": Decimal("150.00"),
                    },
                )

                if was_created:
                    created += 1
                    if status == "completed":
                        project.actual_completion_date = end_date
                        project.client_accepted = True
                        project.acceptance_date = end_date
                        project.accepted_by = project.project_manager
                        project.acceptance_notes = "Fixture acceptance confirmation."
                        project.save(
                            update_fields=[
                                "actual_completion_date",
                                "client_accepted",
                                "acceptance_date",
                                "accepted_by",
                                "acceptance_notes",
                            ]
                        )

                projects.append(project)

                if project_counter >= 30:
                    break
            if project_counter >= 30:
                break

        return projects, FixtureSummary(projects_created=created)

    def _create_folders(
        self,
        firms: list[Firm],
        clients: list[Client],
        users: list,
    ) -> tuple[dict[int, Folder], FixtureSummary]:
        created = 0
        folders: dict[int, Folder] = {}

        for client in clients:
            firm_users = self._users_for_firm(users, client.firm)
            folder, was_created = Folder.objects.get_or_create(
                firm=client.firm,
                client=client,
                parent=None,
                name="Root",
                defaults={
                    "description": "Root folder created by fixtures seed.",
                    "visibility": "internal",
                    "created_by": firm_users[0] if firm_users else None,
                },
            )
            if was_created:
                created += 1
            folders[client.id] = folder

        return folders, FixtureSummary(folders_created=created)

    def _create_documents(
        self,
        firms: list[Firm],
        clients: list[Client],
        projects: list[Project],
        folders: dict[int, Folder],
        users: list,
        now: timezone.datetime,
    ) -> FixtureSummary:
        created = 0
        document_counter = 0
        project_lookup = {project.client_id: project for project in projects}
        document_field_names = {field.name for field in Document._meta.get_fields()}

        for client in clients:
            firm_users = self._users_for_firm(users, client.firm)
            folder = folders[client.id]
            for _ in range(3 if document_counter < 10 else 2):
                document_counter += 1
                if document_counter > 50:
                    break

                s3_bucket = f"{client.firm.slug}-fixtures"
                s3_key = f"{client.id}/documents/doc-{document_counter:03d}.pdf"
                fingerprint = field_encryption_service.fingerprint_for_firm(
                    client.firm_id,
                    f"{s3_bucket}:{s3_key}",
                )

                if fingerprint and Document.objects.filter(
                    firm=client.firm, s3_fingerprint=fingerprint
                ).exists():
                    continue

                status_cycle = ["draft", "review", "approved", "published"]
                status = status_cycle[document_counter % len(status_cycle)]

                document_data = {
                    "firm": client.firm,
                    "client": client,
                    "folder": folder,
                    "project": project_lookup.get(client.id),
                    "name": f"{client.company_name} Document {document_counter}",
                    "description": "Fixture document for workflows and search.",
                    "visibility": "client" if document_counter % 4 == 0 else "internal",
                    "status": status,
                    "classification": "CONF",
                    "file_type": "application/pdf",
                    "file_size_bytes": 1024 * (document_counter + 1),
                    "s3_bucket": s3_bucket,
                    "s3_key": s3_key,
                    "uploaded_by": firm_users[0] if firm_users else None,
                }
                document = Document(**{key: value for key, value in document_data.items() if key in document_field_names})

                if document_counter % 9 == 0:
                    document.legal_hold = True
                    document.legal_hold_reason = "Fixture legal hold scenario."
                    document.legal_hold_applied_by = firm_users[0] if firm_users else None
                    document.legal_hold_applied_at = now

                if document_counter % 7 == 0:
                    document.retention_period_years = 7

                if status in {"approved", "published"} and firm_users:
                    document.reviewed_by = firm_users[0]
                    document.reviewed_at = now - timedelta(days=1)

                if status == "published" and firm_users:
                    document.published_by = firm_users[0]
                    document.published_at = now

                document.save()
                created += 1

            if document_counter >= 50:
                break

        return FixtureSummary(documents_created=created)

    def _create_invoices(
        self,
        firms: list[Firm],
        clients: list[Client],
        projects: list[Project],
        users: list,
        now: timezone.datetime,
    ) -> FixtureSummary:
        created = 0
        invoice_counter = 0
        project_lookup = {project.client_id: project for project in projects}

        for client in clients[:10]:
            invoice_counter += 1
            firm_users = self._users_for_firm(users, client.firm)
            status = "draft"
            if invoice_counter % 4 == 0:
                status = "paid"
            elif invoice_counter % 3 == 0:
                status = "overdue"
            elif invoice_counter % 5 == 0:
                status = "partial"

            issue_date = (now - timedelta(days=30 + invoice_counter)).date()
            due_date = issue_date + timedelta(days=30)

            invoice, was_created = Invoice.objects.get_or_create(
                firm=client.firm,
                invoice_number=f"F{client.firm_id}-INV-{invoice_counter:04d}",
                defaults={
                    "client": client,
                    "project": project_lookup.get(client.id),
                    "created_by": firm_users[0] if firm_users else None,
                    "status": status,
                    "subtotal": Decimal("5000.00"),
                    "tax_amount": Decimal("400.00"),
                    "total_amount": Decimal("5400.00"),
                    "amount_paid": Decimal("0.00"),
                    "issue_date": issue_date,
                    "due_date": due_date,
                    "line_items": [
                        {
                            "description": "Discovery workshop",
                            "quantity": 10,
                            "rate": "500.00",
                            "amount": "5000.00",
                        }
                    ],
                },
            )

            if was_created:
                created += 1
                if status == "paid":
                    invoice.amount_paid = invoice.total_amount
                    invoice.paid_date = due_date
                elif status == "partial":
                    invoice.amount_paid = Decimal("2500.00")
                elif status == "overdue":
                    invoice.due_date = now.date() - timedelta(days=5)
                invoice.save(update_fields=["amount_paid", "paid_date", "due_date"])

        return FixtureSummary(invoices_created=created)

    def _refresh_firm_counters(self, firms: list[Firm], clients: list[Client]) -> None:
        for firm in firms:
            firm.current_users_count = FirmMembership.objects.filter(firm=firm, is_active=True).count()
            firm.current_clients_count = Client.objects.filter(firm=firm).count()
            firm.save(update_fields=["current_users_count", "current_clients_count", "updated_at"])

    def _users_for_firm(self, users: list, firm: Firm) -> list:
        return [
            user
            for user in users
            if FirmMembership.objects.filter(user=user, firm=firm, is_active=True).exists()
        ]

    def _merge_summary(self, base: FixtureSummary, delta: FixtureSummary) -> FixtureSummary:
        return FixtureSummary(
            firms_created=base.firms_created + delta.firms_created,
            users_created=base.users_created + delta.users_created,
            memberships_created=base.memberships_created + delta.memberships_created,
            clients_created=base.clients_created + delta.clients_created,
            projects_created=base.projects_created + delta.projects_created,
            folders_created=base.folders_created + delta.folders_created,
            documents_created=base.documents_created + delta.documents_created,
            invoices_created=base.invoices_created + delta.invoices_created,
        )

    def _report_summary(self, summary: FixtureSummary) -> None:
        self.stdout.write(self.style.SUCCESS("Fixture load complete."))
        self.stdout.write(f"Firms created: {summary.firms_created}")
        self.stdout.write(f"Users created: {summary.users_created}")
        self.stdout.write(f"Memberships created: {summary.memberships_created}")
        self.stdout.write(f"Clients created: {summary.clients_created}")
        self.stdout.write(f"Projects created: {summary.projects_created}")
        self.stdout.write(f"Folders created: {summary.folders_created}")
        self.stdout.write(f"Documents created: {summary.documents_created}")
        self.stdout.write(f"Invoices created: {summary.invoices_created}")
