import pytest


@pytest.mark.e2e
@pytest.mark.django_db
class TestHeroEngagementLifecycle:
    """End-to-end safety rails for firm → client → engagement → invoice → payment → renewal flows."""

    @pytest.mark.xfail(reason="Hero lifecycle flow not implemented yet")
    def test_firm_client_engagement_invoice_payment_renewal(self):
        """Placeholder to ensure the full lifecycle is covered once APIs land."""
        pytest.xfail("Pending implementation of hero workflow across firm/client/engagement/invoice/payment/renewal")

    @pytest.mark.xfail(reason="Portal visibility rules not enforced yet")
    def test_client_portal_visibility(self):
        """Placeholder to validate portal access and document exposure once portal surfaces are available."""
        pytest.xfail("Portal visibility assertions pending portal surfaces")
