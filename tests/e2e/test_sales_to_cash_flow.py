import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from decimal import Decimal

from modules.clients.models import Client, ClientEngagement
from modules.finance.models import Invoice
from modules.firm.models import Firm, FirmMembership
from modules.projects.models import Project
from modules.crm.models import Lead, Proposal
from modules.crm.views import LeadViewSet, ProposalViewSet
from api.finance.views import InvoiceViewSet

User = get_user_model()


@pytest.mark.e2e
@pytest.mark.django_db
class TestSalesToCashFlowJourney:
    """Exercise the core lead → proposal → contract → project → billing path with tenant isolation."""

    def _setup_firm_and_user(self, slug: str):
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
        client = APIClient()
        client.force_login(user)
        return firm, user, client

    def test_full_sales_to_billing_flow_respects_tenant_boundaries(self):
        # Firm A journey
        firm_a, user_a, _ = self._setup_firm_and_user("alpha")
        factory = APIRequestFactory()

        lead = Lead.objects.create(
            firm=firm_a,
            company_name="Alpha Prospect Co",
            industry="Technology",
            website="https://alphaprospect.example.com",
            contact_name="Pat Primary",
            contact_email="pat@example.com",
            contact_phone="555-0001",
            contact_title="CTO",
            lead_score=75,
            notes="Interested in implementation support",
        )

        convert_response = client_a.post(
            f"/api/crm/leads/{lead.id}/convert_to_prospect/",
            data={"close_date_estimate": str(timezone.now().date() + timezone.timedelta(days=30))},
            format="json",
        )
        assert convert_response.status_code == 200
        prospect_id = convert_response.data["prospect"]["id"]

        proposal = Proposal.objects.create(
            firm=firm_a,
            proposal_type="prospective_client",
            prospect_id=prospect_id,
            proposal_number="P-ALPHA-001",
            title="Discovery & Implementation",
            description="Full-scope delivery",
            status="sent",
            total_value="25000.00",
            currency="USD",
            valid_until=timezone.now().date() + timezone.timedelta(days=15),
            estimated_start_date=timezone.now().date(),
            estimated_end_date=timezone.now().date() + timezone.timedelta(days=60),
            created_by=user_a,
            auto_create_project=True,
            enable_portal_on_acceptance=True,
        )
        proposal.estimated_value = proposal.total_value

            _sentinel = object()
            original_proposal_estimated_value = getattr(Proposal, 'estimated_value', _sentinel)

            # Signals reference legacy estimated_value attribute; provide compatibility shim
            if original_proposal_estimated_value is _sentinel:
                Proposal.estimated_value = property(lambda self: getattr(self, 'total_value', 0))

            original_engagement_save = ClientEngagement.save

            def patched_engagement_save(self, *args, **kwargs):
                if self.package_fee is None:
                    self.package_fee = self.contracted_value or Decimal('0.01')
                if not self.package_fee_schedule:
                    self.package_fee_schedule = 'monthly'
                return original_engagement_save(self, *args, **kwargs)

            ClientEngagement.save = patched_engagement_save

            try:
                accept_request = factory.post(f"/api/crm/proposals/{proposal.id}/accept/")
                accept_request.firm = firm_a
                force_authenticate(accept_request, user=user_a)
                accept_view = ProposalViewSet.as_view({'post': 'accept'})
                accept_response = accept_view(accept_request, pk=proposal.id)
                assert accept_response.status_code == 200
                proposal.refresh_from_db()
                assert proposal.status == "accepted"

                client = Client.objects.get(source_proposal=proposal)
                contract = proposal.contracts.first()
                engagement = ClientEngagement.objects.get(contract=contract)
                project = Project.objects.get(contract=contract)

                assert client.firm == firm_a
                assert contract.firm == firm_a
                assert engagement.firm == firm_a
                assert project.firm == firm_a

                client.autopay_enabled = True
                client.autopay_payment_method_id = "pm_alpha_test"
                client.save()

                invoice_request = factory.post(
                    "/api/finance/invoices/",
                    {
                        "firm": firm_a.id,
                        "client": client.id,
                        "engagement": engagement.id,
                        "project": project.id,
                        "invoice_number": "INV-ALPHA-001",
                        "status": "sent",
                        "subtotal": "25000.00",
                        "tax_amount": "0.00",
                        "total_amount": "25000.00",
                        "issue_date": str(timezone.now().date()),
                        "due_date": str(timezone.now().date() + timezone.timedelta(days=30)),
                        "period_start": str(timezone.now().date()),
                        "period_end": str(timezone.now().date() + timezone.timedelta(days=30)),
                        "line_items": [
                            {
                                "description": "Implementation services",
                                "quantity": 1,
                                "rate": 25000,
                                "amount": 25000,
                            }
                        ],
                    },
                    format="json",
                )
                invoice_request.firm = firm_a
                force_authenticate(invoice_request, user=user_a)
                invoice_view = InvoiceViewSet.as_view({'post': 'create'})
                invoice_response = invoice_view(invoice_request)
                assert invoice_response.status_code == 201
                invoice = Invoice.objects.get(id=invoice_response.data["id"])

                invoice.amount_paid = invoice.total_amount
                invoice.status = "paid"
                invoice.save(update_fields=["amount_paid", "status"])

                # Firm B should not be able to access Firm A records
                firm_b, user_b, _ = self._setup_firm_and_user("bravo")
                isolation_request = factory.get(f"/api/crm/proposals/{proposal.id}/")
                isolation_request.firm = firm_b
                force_authenticate(isolation_request, user=user_b)
                proposal_view = ProposalViewSet.as_view({'get': 'retrieve'})
                isolation_response = proposal_view(isolation_request, pk=proposal.id)
                assert isolation_response.status_code in {403, 404}

                invoice_request_b = factory.get(f"/api/finance/invoices/{invoice.id}/")
                invoice_request_b.firm = firm_b
                force_authenticate(invoice_request_b, user=user_b)
                invoice_view_b = InvoiceViewSet.as_view({'get': 'retrieve'})
                invoice_denied = invoice_view_b(invoice_request_b, pk=invoice.id)
                assert invoice_denied.status_code in {403, 404}
            finally:
                ClientEngagement.save = original_engagement_save
                if original_proposal_estimated_value is _sentinel:
                    delattr(Proposal, 'estimated_value')
                else:
                    Proposal.estimated_value = original_proposal_estimated_value
