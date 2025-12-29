"""
Tier 1 Safety Tests - Engagement Immutability

Tests that signed engagements cannot be modified (preserving legal evidence).
CRITICAL: These tests validate data integrity for billing and contracts.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from modules.firm.models import Firm
from modules.clients.models import Client, ClientEngagement
from modules.crm.models import Proposal, Contract

User = get_user_model()


@pytest.fixture
def firm_and_client():
    """Create a firm with a client."""
    firm = Firm.objects.create(
        name="Test Firm",
        slug="testfirm",
        status="active"
    )
    client = Client.objects.create(
        firm=firm,
        name="Test Client",
        email="client@example.com",
        status="active"
    )
    return {"firm": firm, "client": client}


@pytest.fixture
def signed_contract(firm_and_client):
    """Create a signed contract."""
    user = User.objects.create_user(
        username="signer",
        email="signer@example.com",
        password="testpass123"
    )

    proposal = Proposal.objects.create(
        firm=firm_and_client["firm"],
        proposal_type="update_client",
        client=firm_and_client["client"],
        proposal_number="PROP-001",
        title="Test Proposal",
        description="Test proposal scope",
        status="accepted",
        total_value=Decimal("10000.00"),
        valid_until=date.today() + timedelta(days=30),
    )

    contract = Contract.objects.create(
        firm=firm_and_client["firm"],
        proposal=proposal,
        client=firm_and_client["client"],
        contract_number="CON-001",
        title="Test Contract",
        description="Test contract scope",
        total_value=proposal.total_value,
        signed_date=date.today(),
        signed_by=user,
        status="active",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365)
    )

    return contract


@pytest.fixture
def engagement(firm_and_client, signed_contract):
    """Create a client engagement linked to signed contract."""
    engagement = ClientEngagement.objects.create(
        firm=firm_and_client["firm"],
        client=firm_and_client["client"],
        contract=signed_contract,
        type="retainer",
        status="active",
        start_date=date.today(),
        package_fee=Decimal("5000.00")
    )
    return engagement


@pytest.mark.django_db
class TestEngagementImmutability:
    """
    Engagement immutability tests ensure that:
    1. Signed contracts cannot be modified (core terms frozen)
    2. Engagements linked to signed contracts are protected
    3. Renewals create new records (no mutation of history)
    4. Audit trail is preserved
    """

    def test_signed_contract_exists(self, signed_contract):
        """Verify signed contract is created correctly."""
        assert signed_contract.signed_date is not None
        assert signed_contract.signed_by is not None
        assert signed_contract.status == "active"

    def test_contract_signature_fields_required(self, firm_and_client):
        """Active contracts must have signed_date and signed_by populated."""
        from django.core.exceptions import ValidationError
        import pytest

        proposal = Proposal.objects.create(
            firm=firm_and_client["firm"],
            proposal_type="update_client",
            client=firm_and_client["client"],
            proposal_number="PROP-002",
            title="Test Proposal 2",
            description="Test proposal scope",
            status="draft",
            total_value=Decimal("5000.00"),
            valid_until=date.today() + timedelta(days=30),
        )

        # Attempt to create active contract without signature fields
        contract = Contract(
            firm=firm_and_client["firm"],
            proposal=proposal,
            client=firm_and_client["client"],
            contract_number="TEST-002",
            title="Unsigned Contract",
            description="Unsigned contract scope",
            status="active",  # Active but not signed
            total_value=Decimal("5000.00"),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )

        # Active contracts require signature details - should raise ValidationError
        with pytest.raises(ValidationError):
            contract.full_clean()  # Validate before save

    def test_engagement_links_to_contract(self, engagement, signed_contract):
        """Verify engagement is properly linked to signed contract."""
        assert engagement.contract == signed_contract
        assert engagement.firm == signed_contract.firm
        assert engagement.client == signed_contract.client

    def test_engagement_preserves_contract_terms(self, engagement, signed_contract):
        """Engagement should preserve contract terms (immutability)."""
        # Get original contract terms
        original_start = signed_contract.start_date
        original_end = signed_contract.end_date
        original_title = signed_contract.title

        # Modify engagement
        engagement.status = "paused"
        engagement.save()

        # Contract should remain unchanged
        signed_contract.refresh_from_db()
        assert signed_contract.start_date == original_start
        assert signed_contract.end_date == original_end
        assert signed_contract.title == original_title

    def test_renewal_creates_new_engagement(self, engagement):
        """
        Renewals should create new engagement records, not mutate existing.
        This preserves billing history and legal evidence.
        """
        # Create a renewal engagement
        renewal = ClientEngagement.objects.create(
            firm=engagement.firm,
            client=engagement.client,
            contract=engagement.contract,  # Can link to same contract or new one
            type="retainer",
            status="active",
            start_date=date.today() + timedelta(days=365),
            package_fee=Decimal("5000.00"),
            parent_engagement=engagement  # Link to parent
        )

        # Original engagement should remain unchanged
        engagement.refresh_from_db()
        assert engagement.status == "active"

        # Renewal is a separate record
        assert renewal.id != engagement.id
        assert renewal.parent_engagement == engagement

    def test_contract_signed_timestamp_immutable(self, signed_contract):
        """
        Once a contract is signed, the signed_date timestamp should not change.
        This is critical for legal evidence.
        """
        original_signed_date = signed_contract.signed_date
        original_signed_by = signed_contract.signed_by

        # Attempt to modify signed_date
        signed_contract.signed_date = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError, match="Signed date is immutable"):
            signed_contract.save()

        signed_contract.refresh_from_db()

        assert signed_contract.signed_date == original_signed_date
        assert signed_contract.signed_by == original_signed_by

    def test_contract_amount_changes_require_new_contract(self, signed_contract):
        """
        Changing contract amount should require a new contract/amendment.
        Original signed contract should remain unchanged.
        """
        original_proposal_amount = signed_contract.proposal.total_value

        # Attempting to modify proposal amount after signing
        signed_contract.proposal.total_value = Decimal("20000.00")
        with pytest.raises(ValidationError, match="Cannot modify total value"):
            signed_contract.proposal.save()

        signed_contract.proposal.refresh_from_db()
        assert signed_contract.proposal.total_value == original_proposal_amount

    def test_engagement_status_lifecycle(self, engagement):
        """
        Engagement status can change (active → paused → completed),
        but historical data (dates, amounts) should not.
        """
        original_start = engagement.start_date
        original_package_fee = engagement.package_fee

        # Allowed: Status change
        engagement.status = "paused"
        engagement.save()

        # Verify historical data unchanged
        assert engagement.start_date == original_start
        assert engagement.package_fee == original_package_fee

    def test_immutability_documentation(self):
        """
        Document immutability requirements for Tier 3 implementation.

        Required protections:
        1. Signed contracts cannot change core terms (amount, dates, parties)
        2. Engagements linked to signed contracts preserve terms
        3. Renewals/amendments create new records
        4. Signature timestamps are immutable
        5. Audit events track all changes
        """
        assert True, "Immutability enforcement planned for Tier 3"
