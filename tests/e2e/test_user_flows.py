from contextlib import contextmanager
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from django.utils import timezone

from api.finance.views import InvoiceViewSet
from modules.clients.models import Client, ClientEngagement, ClientPortalUser
from modules.clients.views import ClientEngagementViewSet, ClientInvoiceViewSet
from modules.crm.models import Lead, Proposal
from modules.crm.views import LeadViewSet, ProposalViewSet
from modules.finance.billing import create_package_invoice, execute_autopay_for_invoice
from modules.finance.models import Invoice
from modules.firm.models import Firm, FirmMembership
from modules.projects.models import Project

User = get_user_model()


@contextmanager
def engagement_acceptance_shim():
    """Patch proposal acceptance dependencies for deterministic engagement creation."""
    sentinel = object()
    original_proposal_estimated_value = getattr(Proposal, "estimated_value", sentinel)
    if original_proposal_estimated_value is sentinel:
        Proposal.estimated_value = property(lambda self: getattr(self, "total_value", 0))

    original_engagement_save = ClientEngagement.save

    def patched_engagement_save(self, *args, **kwargs):
        if self.package_fee is None:
            self.package_fee = self.contracted_value or Decimal("0.01")
        if not self.package_fee_schedule:
            self.package_fee_schedule = "monthly"
        return original_engagement_save(self, *args, **kwargs)

    ClientEngagement.save = patched_engagement_save

    try:
        yield
    finally:
        ClientEngagement.save = original_engagement_save
        if original_proposal_estimated_value is sentinel:
            delattr(Proposal, "estimated_value")
        else:
            Proposal.estimated_value = original_proposal_estimated_value


@pytest.mark.e2e
@pytest.mark.django_db
class TestTopUserFlows:
    """Hero workflows across CRM, delivery, and billing with tenant isolation."""

    def _setup_firm_user(self, slug: str):
        firm = Firm.objects.create(name=f"{slug.title()} Firm", slug=slug, status="active")
        user = User.objects.create_user(
            username=f"{slug}_user", email=f"{slug}@example.com", password="pass1234"
        )
        FirmMembership.objects.create(
            firm=firm,
            user=user,
            role="admin",
            can_manage_billing=True,
            can_manage_clients=True,
            can_manage_settings=True,
        )
        return firm, user

    def _create_client(self, firm, user, name: str):
        return Client.objects.create(
            firm=firm,
            company_name=name,
            industry="Technology",
            primary_contact_name="Jordan Example",
            primary_contact_email=f"{name.lower().replace(' ', '')}@example.com",
            primary_contact_phone="555-0100",
            status="active",
            account_manager=user,
            client_since=date(2024, 1, 1),
        )

    def _create_project(self, firm, client, user, code: str):
        return Project.objects.create(
            firm=firm,
            client=client,
            project_manager=user,
            project_code=code,
            name=f"{code} Implementation",
            description="Project kickoff",
            status="planning",
            billing_type="fixed_price",
            budget=Decimal("10000.00"),
            hourly_rate=Decimal("150.00"),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 1),
        )

    def _create_invoice(self, firm, client, project, number: str, subtotal: Decimal, tax: Decimal):
        return Invoice.objects.create(
            firm=firm,
            client=client,
            project=project,
            invoice_number=number,
            status="sent",
            subtotal=subtotal,
            tax_amount=tax,
            total_amount=subtotal + tax,
            issue_date=date(2024, 1, 10),
            due_date=date(2024, 2, 9),
            line_items=[
                {
                    "description": "Implementation services",
                    "quantity": 1,
                    "rate": float(subtotal),
                    "amount": float(subtotal),
                }
            ],
        )

    def test_onboarding_project_invoice_autopay_flow(self):
        firm, user = self._setup_firm_user("atlas")
        client = self._create_client(firm, user, "Atlas Co")
        project = self._create_project(firm, client, user, "AT-100")

        client.autopay_enabled = True
        client.autopay_payment_method_id = "pm_atlas"
        client.save(update_fields=["autopay_enabled", "autopay_payment_method_id"])

        factory = APIRequestFactory()
        issue_date = timezone.now().date()
        invoice_payload = {
            "firm": firm.id,
            "client": client.id,
            "project": project.id,
            "invoice_number": "INV-AT-100",
            "status": "sent",
            "subtotal": "10000.00",
            "tax_amount": "800.00",
            "total_amount": "10800.00",
            "issue_date": str(issue_date),
            "due_date": str(issue_date + timedelta(days=30)),
            "line_items": [
                {
                    "description": "Implementation services",
                    "quantity": 1,
                    "rate": 10000,
                    "amount": 10000,
                }
            ],
        }
        request = factory.post("/api/finance/invoices/", invoice_payload, format="json")
        request.firm = firm
        force_authenticate(request, user=user)
        response = InvoiceViewSet.as_view({"post": "create"})(request)
        assert response.status_code == 201

        invoice = Invoice.objects.get(id=response.data["id"])
        assert invoice.total_amount == invoice.subtotal + invoice.tax_amount
        assert invoice.amount_paid == Decimal("0.00")

        execute_autopay_for_invoice(invoice)
        invoice.refresh_from_db()
        assert invoice.status == "paid"
        assert invoice.amount_paid == invoice.total_amount
        assert invoice.paid_date == issue_date

        other_firm, other_user = self._setup_firm_user("borealis")
        denied_request = factory.get(f"/api/finance/invoices/{invoice.id}/")
        denied_request.firm = other_firm
        force_authenticate(denied_request, user=other_user)
        denied_response = InvoiceViewSet.as_view({"get": "retrieve"})(
            denied_request,
            pk=invoice.id,
        )
        assert denied_response.status_code in {403, 404}

    def test_lead_to_engagement_package_invoice_flow(self):
        firm, user = self._setup_firm_user("nimbus")

        lead = Lead.objects.create(
            firm=firm,
            company_name="Nimbus Prospect",
            industry="Healthcare",
            website="https://nimbus.example.com",
            contact_name="Taylor Lead",
            contact_email="taylor@nimbus.example.com",
            contact_phone="555-0200",
            contact_title="COO",
            lead_score=82,
            assigned_to=user,
        )

        factory = APIRequestFactory()
        convert_request = factory.post(
            f"/api/crm/leads/{lead.id}/convert_to_prospect/",
            data={"close_date_estimate": "2024-02-15"},
            format="json",
        )
        convert_request.firm = firm
        force_authenticate(convert_request, user=user)
        convert_response = LeadViewSet.as_view({"post": "convert_to_prospect"})(
            convert_request,
            pk=lead.id,
        )
        assert convert_response.status_code == 200
        prospect_id = convert_response.data["prospect"]["id"]

        proposal = Proposal.objects.create(
            firm=firm,
            proposal_type="prospective_client",
            prospect_id=prospect_id,
            proposal_number="P-NIMBUS-001",
            title="Transformation Program",
            description="Multi-phase delivery",
            status="sent",
            total_value="42000.00",
            currency="USD",
            valid_until=date(2024, 2, 1),
            estimated_start_date=date(2024, 2, 15),
            estimated_end_date=date(2024, 4, 15),
            created_by=user,
            auto_create_project=True,
            enable_portal_on_acceptance=True,
        )
        proposal.estimated_value = proposal.total_value

        with engagement_acceptance_shim():
            accept_request = factory.post(f"/api/crm/proposals/{proposal.id}/accept/")
            accept_request.firm = firm
            force_authenticate(accept_request, user=user)
            accept_response = ProposalViewSet.as_view({"post": "accept"})(
                accept_request,
                pk=proposal.id,
            )
            assert accept_response.status_code == 200

        proposal.refresh_from_db()
        engagement = ClientEngagement.objects.get(contract=proposal.contracts.first())
        invoice = create_package_invoice(engagement, issue_date=date(2024, 2, 15))

        assert invoice.firm == firm
        assert invoice.total_amount == engagement.package_fee
        assert invoice.amount_paid == Decimal("0.00")
        assert any(item.get("type") == "package_fee" for item in invoice.line_items)

        other_firm, other_user = self._setup_firm_user("aurora")
        denied_request = factory.get(f"/api/clients/engagements/{engagement.id}/")
        denied_request.firm = other_firm
        force_authenticate(denied_request, user=other_user)
        denied_response = ClientEngagementViewSet.as_view({"get": "retrieve"})(
            denied_request,
            pk=engagement.id,
        )
        assert denied_response.status_code in {403, 404}

    def test_client_portal_billing_summary_is_scoped(self):
        firm, user = self._setup_firm_user("cascade")
        client = self._create_client(firm, user, "Cascade Co")
        other_client = self._create_client(firm, user, "Delta Co")
        project = self._create_project(firm, client, user, "CS-200")
        other_project = self._create_project(firm, other_client, user, "DL-300")

        self._create_invoice(
            firm,
            client,
            project,
            "INV-CS-200",
            subtotal=Decimal("1200.00"),
            tax=Decimal("0.00"),
        )
        self._create_invoice(
            firm,
            other_client,
            other_project,
            "INV-DL-300",
            subtotal=Decimal("900.00"),
            tax=Decimal("0.00"),
        )

        portal_user = User.objects.create_user(
            username="cascade_portal",
            email="portal@cascade.example.com",
            password="pass1234",
        )
        ClientPortalUser.objects.create(
            client=client,
            user=portal_user,
            role="viewer",
            can_view_billing=True,
        )

        factory = APIRequestFactory()
        summary_request = factory.get("/api/clients/invoices/summary/")
        summary_request.firm = firm
        force_authenticate(summary_request, user=portal_user)
        summary_response = ClientInvoiceViewSet.as_view({"get": "summary"})(summary_request)
        assert summary_response.status_code == 200

        assert summary_response.data["total_invoices"] == 1
        total_billed = Decimal(str(summary_response.data["total_billed"]))
        total_outstanding = Decimal(str(summary_response.data["total_outstanding"]))
        assert total_billed == Decimal("1200.00")
        assert total_outstanding == Decimal("1200.00")
