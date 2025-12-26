import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from modules.clients.models import Client, ClientEngagement, ClientPortalUser
from modules.crm.models import Proposal, Prospect
from modules.crm.views import ProposalViewSet
from modules.firm.models import Firm, FirmMembership
from modules.finance.models import Invoice
from api.finance.views import InvoiceViewSet
from modules.projects.models import Project
from modules.clients.views import ClientInvoiceViewSet

User = get_user_model()


@pytest.mark.e2e
@pytest.mark.django_db
class TestHeroEngagementLifecycle:
    """End-to-end safety rails for firm → client → engagement → invoice → payment → renewal flows."""

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
        return firm, user

    def _create_prospect(self, firm, user, suffix):
        return Prospect.objects.create(
            firm=firm,
            company_name=f"Hero Prospect {suffix}",
            industry="Technology",
            website="https://hero.example.com",
            primary_contact_name="Hero Contact",
            primary_contact_email=f"hero{suffix}@example.com",
            primary_contact_phone="555-0100",
            primary_contact_title="CEO",
            estimated_value=Decimal("50000.00"),
            close_date_estimate=timezone.now().date() + timezone.timedelta(days=30),
            assigned_to=user,
        )

    def _patch_engagement_save(self):
        original_engagement_save = ClientEngagement.save

        def patched_engagement_save(self, *args, **kwargs):
            if self.package_fee is None:
                self.package_fee = self.contracted_value or Decimal("0.01")
            if not self.package_fee_schedule:
                self.package_fee_schedule = "monthly"
            return original_engagement_save(self, *args, **kwargs)

        return original_engagement_save, patched_engagement_save

    def _ensure_estimated_value(self):
        sentinel = object()
        original_proposal_estimated_value = getattr(Proposal, "estimated_value", sentinel)
        if original_proposal_estimated_value is sentinel:
            Proposal.estimated_value = property(lambda self: getattr(self, "total_value", 0))
        return sentinel, original_proposal_estimated_value

    def _restore_estimated_value(self, sentinel, original_value):
        if original_value is sentinel:
            delattr(Proposal, "estimated_value")
        else:
            Proposal.estimated_value = original_value

    def _accept_proposal(self, firm, user, proposal):
        factory = APIRequestFactory()
        accept_request = factory.post(f"/api/crm/proposals/{proposal.id}/accept/")
        accept_request.firm = firm
        force_authenticate(accept_request, user=user)
        accept_view = ProposalViewSet.as_view({"post": "accept"})
        return accept_view(accept_request, pk=proposal.id)

    def test_firm_client_engagement_invoice_payment_renewal(self):
        firm, user = self._setup_firm_and_user("hero")
        prospect = self._create_prospect(firm, user, "A")

        proposal = Proposal.objects.create(
            firm=firm,
            proposal_type="prospective_client",
            prospect=prospect,
            proposal_number="P-HERO-001",
            title="Hero Engagement",
            description="Core delivery scope",
            status="sent",
            total_value=Decimal("50000.00"),
            currency="USD",
            valid_until=timezone.now().date() + timezone.timedelta(days=14),
            estimated_start_date=timezone.now().date(),
            estimated_end_date=timezone.now().date() + timezone.timedelta(days=90),
            created_by=user,
            auto_create_project=True,
            enable_portal_on_acceptance=True,
        )

        sentinel, original_value = self._ensure_estimated_value()
        original_engagement_save, patched_engagement_save = self._patch_engagement_save()
        ClientEngagement.save = patched_engagement_save

        try:
            accept_response = self._accept_proposal(firm, user, proposal)
            assert accept_response.status_code == 200
            proposal.refresh_from_db()
            assert proposal.status == "accepted"

            client = Client.objects.get(source_proposal=proposal)
            contract = proposal.contracts.first()
            engagement = ClientEngagement.objects.get(contract=contract)
            project = Project.objects.get(contract=contract)

            assert client.firm == firm
            assert engagement.version == 1
            assert engagement.status == "current"
            assert project.firm == firm

            invoice_factory = APIRequestFactory()
            invoice_request = invoice_factory.post(
                "/api/finance/invoices/",
                {
                    "firm": firm.id,
                    "client": client.id,
                    "engagement": engagement.id,
                    "project": project.id,
                    "invoice_number": "INV-HERO-001",
                    "status": "sent",
                    "subtotal": "50000.00",
                    "tax_amount": "0.00",
                    "total_amount": "50000.00",
                    "issue_date": str(timezone.now().date()),
                    "due_date": str(timezone.now().date() + timezone.timedelta(days=30)),
                    "period_start": str(timezone.now().date()),
                    "period_end": str(timezone.now().date() + timezone.timedelta(days=30)),
                    "line_items": [
                        {
                            "description": "Hero services",
                            "quantity": 1,
                            "rate": 50000,
                            "amount": 50000,
                        }
                    ],
                },
                format="json",
            )
            invoice_request.firm = firm
            force_authenticate(invoice_request, user=user)
            invoice_view = InvoiceViewSet.as_view({"post": "create"})
            invoice_response = invoice_view(invoice_request)
            assert invoice_response.status_code == 201
            invoice = Invoice.objects.get(id=invoice_response.data["id"])

            invoice.amount_paid = invoice.total_amount
            invoice.status = "paid"
            invoice.save(update_fields=["amount_paid", "status"])

            renewal_proposal = Proposal.objects.create(
                firm=firm,
                proposal_type="renewal_client",
                client=client,
                proposal_number="P-HERO-RENEW-001",
                title="Hero Renewal",
                description="Renewed scope",
                status="sent",
                total_value=Decimal("60000.00"),
                currency="USD",
                valid_until=timezone.now().date() + timezone.timedelta(days=14),
                estimated_start_date=timezone.now().date(),
                estimated_end_date=timezone.now().date() + timezone.timedelta(days=365),
                created_by=user,
                auto_create_project=True,
            )

            renewal_response = self._accept_proposal(firm, user, renewal_proposal)
            assert renewal_response.status_code == 200

            engagement.refresh_from_db()
            renewed_engagement = ClientEngagement.objects.filter(client=client).order_by("-version").first()
            assert engagement.status == "renewed"
            assert renewed_engagement.parent_engagement == engagement
            assert renewed_engagement.version == engagement.version + 1
        finally:
            ClientEngagement.save = original_engagement_save
            self._restore_estimated_value(sentinel, original_value)

    def test_client_portal_visibility(self):
        firm, user = self._setup_firm_and_user("portal")
        prospect = self._create_prospect(firm, user, "B")

        proposal = Proposal.objects.create(
            firm=firm,
            proposal_type="prospective_client",
            prospect=prospect,
            proposal_number="P-PORTAL-001",
            title="Portal Engagement",
            description="Portal delivery",
            status="sent",
            total_value=Decimal("15000.00"),
            currency="USD",
            valid_until=timezone.now().date() + timezone.timedelta(days=14),
            estimated_start_date=timezone.now().date(),
            estimated_end_date=timezone.now().date() + timezone.timedelta(days=30),
            created_by=user,
            auto_create_project=True,
            enable_portal_on_acceptance=True,
        )

        sentinel, original_value = self._ensure_estimated_value()
        original_engagement_save, patched_engagement_save = self._patch_engagement_save()
        ClientEngagement.save = patched_engagement_save

        try:
            accept_response = self._accept_proposal(firm, user, proposal)
            assert accept_response.status_code == 200

            client = Client.objects.get(source_proposal=proposal)
            contract = proposal.contracts.first()
            engagement = ClientEngagement.objects.get(contract=contract)
            project = Project.objects.get(contract=contract)

            portal_user = User.objects.create_user(
                username="portal_user",
                email="portal@example.com",
                password="pass1234",
            )
            ClientPortalUser.objects.create(
                client=client,
                user=portal_user,
                role="admin",
                can_view_billing=True,
            )

            invoice = Invoice.objects.create(
                firm=firm,
                client=client,
                engagement=engagement,
                project=project,
                invoice_number="INV-PORTAL-001",
                status="sent",
                subtotal=Decimal("15000.00"),
                tax_amount=Decimal("0.00"),
                total_amount=Decimal("15000.00"),
                issue_date=timezone.now().date(),
                due_date=timezone.now().date() + timezone.timedelta(days=30),
                period_start=timezone.now().date(),
                period_end=timezone.now().date() + timezone.timedelta(days=30),
            )

            other_client = Client.objects.create(
                firm=firm,
                company_name="Other Co",
                primary_contact_name="Other Contact",
                primary_contact_email="other@example.com",
            )
            Invoice.objects.create(
                firm=firm,
                client=other_client,
                invoice_number="INV-OTHER-001",
                status="sent",
                subtotal=Decimal("500.00"),
                tax_amount=Decimal("0.00"),
                total_amount=Decimal("500.00"),
                issue_date=timezone.now().date(),
                due_date=timezone.now().date() + timezone.timedelta(days=30),
                period_start=timezone.now().date(),
                period_end=timezone.now().date() + timezone.timedelta(days=30),
            )

            factory = APIRequestFactory()
            request = factory.get("/api/portal/invoices/")
            request.firm = firm
            force_authenticate(request, user=portal_user)
            view = ClientInvoiceViewSet.as_view({"get": "list"})
            response = view(request)

            assert response.status_code == 200
            data = response.data.get("results", response.data)
            invoice_ids = {entry["id"] for entry in data}
            assert invoice.id in invoice_ids
            assert len(invoice_ids) == 1
        finally:
            ClientEngagement.save = original_engagement_save
            self._restore_estimated_value(sentinel, original_value)
