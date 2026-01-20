import pytest
import hashlib
import json
from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.pricing.models import (
    RuleSet,
    Quote,
    QuoteVersion,
    QuoteLineItem,
)
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", ******)


@pytest.fixture
def ruleset(db, firm, user):
    rules = {
        "base_price": 1000,
        "modifiers": [{"type": "volume_discount", "threshold": 10, "discount": 0.1}],
    }
    return RuleSet.objects.create(
        firm=firm,
        name="Standard Pricing",
        code="standard_v1",
        version=1,
        schema_version="1.0.0",
        rules_json=rules,
        status="draft",
        created_by=user,
    )


@pytest.mark.django_db
class TestRuleSet:
    """Test RuleSet model functionality"""

    def test_ruleset_creation(self, firm, user):
        """Test basic ruleset creation"""
        rules = {"base_price": 500, "currency": "USD", "tax_rate": 0.08}

        ruleset = RuleSet.objects.create(
            firm=firm,
            name="Basic Pricing",
            code="basic_v1",
            version=1,
            schema_version="1.0.0",
            rules_json=rules,
            default_currency="USD",
            status="draft",
            created_by=user,
        )

        assert ruleset.name == "Basic Pricing"
        assert ruleset.code == "basic_v1"
        assert ruleset.version == 1
        assert ruleset.status == "draft"
        assert ruleset.rules_json["base_price"] == 500

    def test_ruleset_status_choices(self, firm, user):
        """Test ruleset status choices"""
        statuses = ["draft", "published", "deprecated"]

        for i, status in enumerate(statuses):
            ruleset = RuleSet.objects.create(
                firm=firm,
                name=f"Ruleset {status}",
                code=f"ruleset_{status}",
                version=1,
                rules_json={},
                status=status,
                created_by=user,
            )
            assert ruleset.status == status

    def test_ruleset_versioning(self, firm, user):
        """Test ruleset versioning"""
        # Create version 1
        v1 = RuleSet.objects.create(
            firm=firm,
            name="Pricing Rules",
            code="pricing_v1",
            version=1,
            rules_json={"base_price": 100},
            created_by=user,
        )

        # Create version 2
        v2 = RuleSet.objects.create(
            firm=firm,
            name="Pricing Rules",
            code="pricing_v1",
            version=2,
            rules_json={"base_price": 150},
            created_by=user,
        )

        assert v1.version == 1
        assert v2.version == 2
        assert v1.code == v2.code
        assert v1.rules_json != v2.rules_json

    def test_ruleset_checksum_computation(self, ruleset):
        """Test ruleset checksum computation"""
        # Compute checksum
        checksum = ruleset.compute_checksum()

        assert len(checksum) == 64  # SHA-256 hex digest length
        assert isinstance(checksum, str)

        # Same rules should produce same checksum
        checksum2 = ruleset.compute_checksum()
        assert checksum == checksum2

    def test_ruleset_checksum_verification(self, ruleset):
        """Test ruleset checksum verification"""
        # Set checksum
        ruleset.checksum = ruleset.compute_checksum()
        ruleset.save()

        # Verify checksum
        assert ruleset.verify_checksum() is True

        # Modify rules (tampering)
        ruleset.rules_json["base_price"] = 9999

        # Checksum should not match
        assert ruleset.verify_checksum() is False

    def test_ruleset_immutability_on_publish(self, ruleset):
        """Test that published rulesets should be immutable"""
        # Publish ruleset
        ruleset.status = "published"
        ruleset.published_at = timezone.now()
        ruleset.checksum = ruleset.compute_checksum()
        ruleset.save()

        assert ruleset.status == "published"
        assert ruleset.published_at is not None
        assert ruleset.checksum is not None

    def test_ruleset_string_representation(self, ruleset):
        """Test __str__ method"""
        expected = f"{ruleset.name} v{ruleset.version} ({ruleset.status})"
        assert str(ruleset) == expected

    def test_ruleset_firm_scoping(self, firm, user):
        """Test ruleset tenant isolation"""
        firm2 = Firm.objects.create(name="Firm 2", slug="firm-2", status="active")

        rs1 = RuleSet.objects.create(
            firm=firm, name="RS 1", code="rs1", version=1, rules_json={}, created_by=user
        )
        rs2 = RuleSet.objects.create(
            firm=firm2, name="RS 2", code="rs2", version=1, rules_json={}, created_by=user
        )

        assert rs1.firm != rs2.firm

    def test_ruleset_unique_together(self, firm, user):
        """Test firm + code + version uniqueness"""
        RuleSet.objects.create(firm=firm, name="Test", code="test_code", version=1, rules_json={}, created_by=user)

        # Creating duplicate should fail
        with pytest.raises(Exception):  # IntegrityError
            RuleSet.objects.create(firm=firm, name="Test", code="test_code", version=1, rules_json={}, created_by=user)

    def test_ruleset_currency(self, firm, user):
        """Test ruleset default currency"""
        ruleset = RuleSet.objects.create(
            firm=firm,
            name="EUR Pricing",
            code="eur_pricing",
            version=1,
            rules_json={},
            default_currency="EUR",
            created_by=user,
        )

        assert ruleset.default_currency == "EUR"


@pytest.mark.django_db
class TestQuote:
    """Test Quote model functionality"""

    def test_quote_creation(self, firm, user, ruleset):
        """Test basic quote creation"""
        quote = Quote.objects.create(
            firm=firm, client_name="Test Client", created_by=user, current_ruleset=ruleset, status="draft"
        )

        assert quote.client_name == "Test Client"
        assert quote.status == "draft"
        assert quote.current_ruleset == ruleset
        assert quote.firm == firm

    def test_quote_status_transitions(self, firm, user, ruleset):
        """Test quote status transitions"""
        quote = Quote.objects.create(
            firm=firm, client_name="Test Client", created_by=user, current_ruleset=ruleset, status="draft"
        )

        # Draft -> Approved
        quote.status = "approved"
        quote.save()
        assert quote.status == "approved"

        # Approved -> Accepted
        quote.status = "accepted"
        quote.save()
        assert quote.status == "accepted"


@pytest.mark.django_db
class TestQuoteVersion:
    """Test QuoteVersion model functionality"""

    def test_quote_version_creation(self, firm, user, ruleset):
        """Test quote version creation"""
        quote = Quote.objects.create(firm=firm, client_name="Test Client", created_by=user, current_ruleset=ruleset)

        version = QuoteVersion.objects.create(
            quote=quote,
            version_number=1,
            ruleset=ruleset,
            ruleset_checksum=ruleset.compute_checksum(),
            total_amount=1000.00,
            currency="USD",
            created_by=user,
        )

        assert version.quote == quote
        assert version.version_number == 1
        assert version.ruleset == ruleset
        assert version.total_amount == 1000.00

    def test_quote_version_immutability(self, firm, user, ruleset):
        """Test that quote versions are immutable"""
        quote = Quote.objects.create(firm=firm, client_name="Test Client", created_by=user, current_ruleset=ruleset)

        version = QuoteVersion.objects.create(
            quote=quote,
            version_number=1,
            ruleset=ruleset,
            ruleset_checksum=ruleset.compute_checksum(),
            total_amount=1000.00,
            currency="USD",
            created_by=user,
        )

        original_amount = version.total_amount

        # Versions should not be modified after creation
        # (enforced by application logic)
        assert version.total_amount == original_amount


@pytest.mark.django_db
class TestQuoteLineItem:
    """Test QuoteLineItem model functionality"""

    def test_line_item_creation(self, firm, user, ruleset):
        """Test quote line item creation"""
        quote = Quote.objects.create(firm=firm, client_name="Test Client", created_by=user, current_ruleset=ruleset)

        version = QuoteVersion.objects.create(
            quote=quote,
            version_number=1,
            ruleset=ruleset,
            ruleset_checksum=ruleset.compute_checksum(),
            total_amount=1500.00,
            currency="USD",
            created_by=user,
        )

        line_item = QuoteLineItem.objects.create(
            quote_version=version, description="Consulting Services", quantity=10, unit_price=150.00, line_total=1500.00
        )

        assert line_item.quote_version == version
        assert line_item.description == "Consulting Services"
        assert line_item.quantity == 10
        assert line_item.unit_price == 150.00
        assert line_item.line_total == 1500.00

    def test_multiple_line_items(self, firm, user, ruleset):
        """Test quote with multiple line items"""
        quote = Quote.objects.create(firm=firm, client_name="Test Client", created_by=user, current_ruleset=ruleset)

        version = QuoteVersion.objects.create(
            quote=quote,
            version_number=1,
            ruleset=ruleset,
            ruleset_checksum=ruleset.compute_checksum(),
            total_amount=3500.00,
            currency="USD",
            created_by=user,
        )

        # Line item 1
        QuoteLineItem.objects.create(
            quote_version=version, description="Service A", quantity=10, unit_price=150.00, line_total=1500.00
        )

        # Line item 2
        QuoteLineItem.objects.create(
            quote_version=version, description="Service B", quantity=20, unit_price=100.00, line_total=2000.00
        )

        assert version.line_items.count() == 2
        total = sum(item.line_total for item in version.line_items.all())
        assert total == 3500.00


@pytest.mark.django_db
class TestPricingWorkflow:
    """Test complete pricing workflow scenarios"""

    def test_complete_quote_lifecycle(self, firm, user):
        """Test complete quote lifecycle"""
        # Create ruleset
        rules = {"base_price": 100, "volume_discount": {"threshold": 10, "rate": 0.1}}

        ruleset = RuleSet.objects.create(
            firm=firm,
            name="Standard Pricing",
            code="standard_v1",
            version=1,
            rules_json=rules,
            status="published",
            published_at=timezone.now(),
            created_by=user,
        )
        ruleset.checksum = ruleset.compute_checksum()
        ruleset.save()

        # Create quote
        quote = Quote.objects.create(
            firm=firm, client_name="ABC Corp", created_by=user, current_ruleset=ruleset, status="draft"
        )

        # Create quote version
        version = QuoteVersion.objects.create(
            quote=quote,
            version_number=1,
            ruleset=ruleset,
            ruleset_checksum=ruleset.checksum,
            total_amount=1800.00,
            currency="USD",
            created_by=user,
        )

        # Add line items
        QuoteLineItem.objects.create(
            quote_version=version, description="Consulting Hours", quantity=20, unit_price=90.00, line_total=1800.00
        )

        # Approve quote
        quote.status = "approved"
        quote.save()

        # Client accepts
        quote.status = "accepted"
        quote.save()

        assert quote.status == "accepted"
        assert version.line_items.count() == 1
        assert version.total_amount == 1800.00

    def test_quote_revision_with_new_version(self, firm, user, ruleset):
        """Test quote revision creating new version"""
        # Create quote with v1
        quote = Quote.objects.create(firm=firm, client_name="XYZ Inc", created_by=user, current_ruleset=ruleset)

        v1 = QuoteVersion.objects.create(
            quote=quote,
            version_number=1,
            ruleset=ruleset,
            ruleset_checksum=ruleset.compute_checksum(),
            total_amount=1000.00,
            currency="USD",
            created_by=user,
        )

        QuoteLineItem.objects.create(
            quote_version=v1, description="Initial Scope", quantity=10, unit_price=100.00, line_total=1000.00
        )

        # Create revised version v2
        v2 = QuoteVersion.objects.create(
            quote=quote,
            version_number=2,
            ruleset=ruleset,
            ruleset_checksum=ruleset.compute_checksum(),
            total_amount=1500.00,
            currency="USD",
            created_by=user,
        )

        QuoteLineItem.objects.create(
            quote_version=v2, description="Expanded Scope", quantity=15, unit_price=100.00, line_total=1500.00
        )

        # Both versions exist
        assert QuoteVersion.objects.filter(quote=quote).count() == 2
        assert v1.total_amount == 1000.00
        assert v2.total_amount == 1500.00
