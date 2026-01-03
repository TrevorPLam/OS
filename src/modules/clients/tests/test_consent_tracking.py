"""
Tests for ConsentRecord model and consent chain tracking (CRM-INT-4).

Tests cover:
- Consent record creation (grant/revoke/update)
- Immutability (cannot modify or delete records)
- Chain verification (cryptographic hash linking)
- GDPR/CCPA compliance tracking
- Consent proof export
- Audit trail completeness
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.clients.models import Client, Contact, ConsentRecord
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    """Create a test firm."""
    return Firm.objects.create(
        name="Test Firm",
        subdomain="testfirm",
        plan="professional",
    )


@pytest.fixture
def firm_user(db, firm):
    """Create a test user belonging to the firm."""
    user = User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
    )
    user.firm = firm
    user.save()
    return user


@pytest.fixture
def client(db, firm):
    """Create a test client."""
    return Client.objects.create(
        firm=firm,
        company_name="Test Company",
        primary_contact_name="John Doe",
        primary_contact_email="john@testcompany.com",
        status="active",
        client_since=timezone.now().date(),
    )


@pytest.fixture
def contact(db, client, firm_user):
    """Create a test contact."""
    return Contact.objects.create(
        client=client,
        first_name="Jane",
        last_name="Smith",
        email="jane@testcompany.com",
        phone="555-0100",
        job_title="Manager",
        created_by=firm_user,
    )


class TestConsentRecordCreation:
    """Test consent record creation with different types and actions."""

    def test_create_marketing_consent_granted(self, contact, firm_user):
        """Test creating a marketing consent grant record."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            legal_basis=ConsentRecord.LEGAL_BASIS_CONSENT,
            data_categories=[ConsentRecord.DATA_CATEGORY_CONTACT],
            consent_text="I agree to receive marketing communications",
            consent_version="v1.0",
            source="signup_form",
            source_url="https://example.com/signup",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            actor=firm_user,
            metadata={"campaign_id": "123"},
        )
        
        assert record.id is not None
        assert record.contact == contact
        assert record.consent_type == ConsentRecord.CONSENT_TYPE_MARKETING
        assert record.action == ConsentRecord.ACTION_GRANTED
        assert record.timestamp is not None
        assert record.record_hash is not None
        assert len(record.record_hash) == 64  # SHA-256 hash
        assert record.previous_record_hash == "0" * 64  # First record (genesis)

    def test_create_email_consent_revoked(self, contact, firm_user):
        """Test creating an email consent revocation record."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_EMAIL,
            action=ConsentRecord.ACTION_REVOKED,
            legal_basis=ConsentRecord.LEGAL_BASIS_CONSENT,
            source="unsubscribe_link",
            ip_address="192.168.1.2",
            actor=firm_user,
        )
        
        assert record.action == ConsentRecord.ACTION_REVOKED
        assert record.timestamp is not None

    def test_create_sms_consent_with_multiple_data_categories(self, contact):
        """Test creating SMS consent with multiple data categories."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_SMS,
            action=ConsentRecord.ACTION_GRANTED,
            data_categories=[
                ConsentRecord.DATA_CATEGORY_CONTACT,
                ConsentRecord.DATA_CATEGORY_BEHAVIORAL,
            ],
            source="mobile_app",
        )
        
        assert len(record.data_categories) == 2
        assert ConsentRecord.DATA_CATEGORY_CONTACT in record.data_categories
        assert ConsentRecord.DATA_CATEGORY_BEHAVIORAL in record.data_categories

    def test_create_data_processing_consent_with_legal_basis(self, contact):
        """Test creating data processing consent with different legal basis."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_DATA_PROCESSING,
            action=ConsentRecord.ACTION_GRANTED,
            legal_basis=ConsentRecord.LEGAL_BASIS_CONTRACT,
            source="contract_signing",
            consent_text="Data processing necessary for contract performance",
        )
        
        assert record.legal_basis == ConsentRecord.LEGAL_BASIS_CONTRACT

    def test_automatic_hash_computation(self, contact):
        """Test that record hash is automatically computed on save."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="test",
        )
        
        # Verify hash was computed
        assert record.record_hash is not None
        assert len(record.record_hash) == 64
        
        # Verify it's deterministic (recomputing should give same hash)
        import hashlib
        import json
        
        hash_data = {
            "contact_id": record.contact_id,
            "consent_type": record.consent_type,
            "action": record.action,
            "timestamp": record.timestamp.isoformat(),
            "previous_hash": record.previous_record_hash,
            "legal_basis": record.legal_basis,
            "data_categories": sorted(record.data_categories) if record.data_categories else [],
            "source": record.source,
        }
        hash_string = json.dumps(hash_data, sort_keys=True)
        expected_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        
        assert record.record_hash == expected_hash


class TestConsentRecordImmutability:
    """Test that consent records cannot be modified or deleted."""

    def test_cannot_modify_existing_record(self, contact):
        """Test that attempting to modify a consent record raises an error."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="test",
        )
        
        # Attempt to modify the record
        record.action = ConsentRecord.ACTION_REVOKED
        
        with pytest.raises(ValueError, match="immutable"):
            record.save()

    def test_cannot_delete_consent_record(self, contact):
        """Test that attempting to delete a consent record raises an error."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="test",
        )
        
        with pytest.raises(ValueError, match="immutable"):
            record.delete()


class TestConsentChainVerification:
    """Test cryptographic chain verification for consent records."""

    def test_chain_verification_single_record(self, contact):
        """Test chain verification with a single record."""
        ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="test",
        )
        
        verification = ConsentRecord.verify_chain(contact, ConsentRecord.CONSENT_TYPE_MARKETING)
        
        assert verification["valid"] is True
        assert verification["records_verified"] == 1
        assert len(verification["errors"]) == 0

    def test_chain_verification_multiple_records(self, contact):
        """Test chain verification with multiple linked records."""
        # Create first record
        record1 = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="signup",
        )
        
        # Create second record (should link to first)
        record2 = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_REVOKED,
            source="unsubscribe",
        )
        
        # Create third record (should link to second)
        record3 = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="resubscribe",
        )
        
        # Verify chain
        verification = ConsentRecord.verify_chain(contact, ConsentRecord.CONSENT_TYPE_MARKETING)
        
        assert verification["valid"] is True
        assert verification["records_verified"] == 3
        assert len(verification["errors"]) == 0
        
        # Verify hash linking
        assert record2.previous_record_hash == record1.record_hash
        assert record3.previous_record_hash == record2.record_hash

    def test_chain_verification_different_consent_types(self, contact):
        """Test that different consent types have separate chains."""
        # Create marketing consent
        marketing_record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="test",
        )
        
        # Create email consent (different type, should start new chain)
        email_record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_EMAIL,
            action=ConsentRecord.ACTION_GRANTED,
            source="test",
        )
        
        # Both should be genesis records (first in their chain)
        assert marketing_record.previous_record_hash == "0" * 64
        assert email_record.previous_record_hash == "0" * 64
        
        # Verify each chain separately
        marketing_verification = ConsentRecord.verify_chain(contact, ConsentRecord.CONSENT_TYPE_MARKETING)
        email_verification = ConsentRecord.verify_chain(contact, ConsentRecord.CONSENT_TYPE_EMAIL)
        
        assert marketing_verification["valid"] is True
        assert email_verification["valid"] is True


class TestConsentCurrentStatus:
    """Test getting current consent status for a contact."""

    def test_get_current_consent_no_records(self, contact):
        """Test getting current consent when no records exist."""
        status = ConsentRecord.get_current_consent(contact, ConsentRecord.CONSENT_TYPE_MARKETING)
        
        assert status["has_consent"] is False
        assert status["latest_action"] is None
        assert status["timestamp"] is None
        assert status["record"] is None

    def test_get_current_consent_granted(self, contact):
        """Test getting current consent status when consent is granted."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="test",
        )
        
        status = ConsentRecord.get_current_consent(contact, ConsentRecord.CONSENT_TYPE_MARKETING)
        
        assert status["has_consent"] is True
        assert status["latest_action"] == ConsentRecord.ACTION_GRANTED
        assert status["timestamp"] == record.timestamp
        assert status["record"] == record

    def test_get_current_consent_revoked(self, contact):
        """Test getting current consent status when consent is revoked."""
        # Grant consent
        ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="signup",
        )
        
        # Revoke consent
        revoke_record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_REVOKED,
            source="unsubscribe",
        )
        
        status = ConsentRecord.get_current_consent(contact, ConsentRecord.CONSENT_TYPE_MARKETING)
        
        assert status["has_consent"] is False
        assert status["latest_action"] == ConsentRecord.ACTION_REVOKED
        assert status["timestamp"] == revoke_record.timestamp


class TestConsentProofExport:
    """Test consent proof export for GDPR compliance."""

    def test_export_consent_proof_single_type(self, contact):
        """Test exporting consent proof for a single consent type."""
        # Create some consent records
        ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="signup",
            ip_address="192.168.1.1",
        )
        
        ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_REVOKED,
            source="unsubscribe",
            ip_address="192.168.1.2",
        )
        
        # Export proof
        proof = ConsentRecord.export_consent_proof(contact, ConsentRecord.CONSENT_TYPE_MARKETING)
        
        assert proof["contact"]["id"] == contact.id
        assert proof["contact"]["name"] == contact.full_name
        assert proof["contact"]["email"] == contact.email
        assert "export_timestamp" in proof
        assert proof["chain_verification"]["valid"] is True
        assert len(proof["consent_records"]) == 2
        
        # Verify record details
        record1 = proof["consent_records"][0]
        assert record1["consent_type"] == ConsentRecord.CONSENT_TYPE_MARKETING
        assert record1["action"] == ConsentRecord.ACTION_GRANTED
        assert record1["ip_address"] == "192.168.1.1"
        assert "record_hash" in record1
        assert "previous_record_hash" in record1

    def test_export_consent_proof_all_types(self, contact):
        """Test exporting consent proof for all consent types."""
        # Create records of different types
        ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="test",
        )
        
        ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_EMAIL,
            action=ConsentRecord.ACTION_GRANTED,
            source="test",
        )
        
        ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_SMS,
            action=ConsentRecord.ACTION_GRANTED,
            source="test",
        )
        
        # Export all consents (no type filter)
        proof = ConsentRecord.export_consent_proof(contact)
        
        assert len(proof["consent_records"]) == 3
        consent_types = [r["consent_type"] for r in proof["consent_records"]]
        assert ConsentRecord.CONSENT_TYPE_MARKETING in consent_types
        assert ConsentRecord.CONSENT_TYPE_EMAIL in consent_types
        assert ConsentRecord.CONSENT_TYPE_SMS in consent_types


class TestConsentAuditTrail:
    """Test audit trail completeness for consent records."""

    def test_audit_trail_with_all_fields(self, contact, firm_user):
        """Test that all audit trail fields are captured."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="signup_form",
            source_url="https://example.com/signup",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            actor=firm_user,
            metadata={
                "campaign_id": "summer_2024",
                "utm_source": "email",
                "utm_medium": "newsletter",
            },
            notes="User clicked checkbox during signup",
        )
        
        # Verify all audit fields are present
        assert record.timestamp is not None
        assert record.ip_address == "192.168.1.1"
        assert "Mozilla/5.0" in record.user_agent
        assert record.actor == firm_user
        assert record.metadata["campaign_id"] == "summer_2024"
        assert "checkbox" in record.notes
        assert record.source_url == "https://example.com/signup"

    def test_audit_trail_minimal_fields(self, contact):
        """Test that only required fields are necessary."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            source="api",
        )
        
        # Should still be valid with minimal fields
        assert record.id is not None
        assert record.timestamp is not None
        assert record.record_hash is not None


class TestGDPRCompliance:
    """Test GDPR compliance features."""

    def test_legal_basis_tracking(self, contact):
        """Test that legal basis is properly tracked for GDPR compliance."""
        # Consent-based processing
        consent_record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_MARKETING,
            action=ConsentRecord.ACTION_GRANTED,
            legal_basis=ConsentRecord.LEGAL_BASIS_CONSENT,
            source="opt_in_form",
        )
        
        # Contract-based processing
        contract_record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_DATA_PROCESSING,
            action=ConsentRecord.ACTION_GRANTED,
            legal_basis=ConsentRecord.LEGAL_BASIS_CONTRACT,
            source="contract_signing",
        )
        
        assert consent_record.legal_basis == ConsentRecord.LEGAL_BASIS_CONSENT
        assert contract_record.legal_basis == ConsentRecord.LEGAL_BASIS_CONTRACT

    def test_data_categories_tracking(self, contact):
        """Test that data categories are tracked for GDPR compliance."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_DATA_PROCESSING,
            action=ConsentRecord.ACTION_GRANTED,
            data_categories=[
                ConsentRecord.DATA_CATEGORY_PERSONAL,
                ConsentRecord.DATA_CATEGORY_CONTACT,
                ConsentRecord.DATA_CATEGORY_FINANCIAL,
            ],
            source="onboarding",
        )
        
        assert len(record.data_categories) == 3
        assert ConsentRecord.DATA_CATEGORY_PERSONAL in record.data_categories
        assert ConsentRecord.DATA_CATEGORY_FINANCIAL in record.data_categories

    def test_consent_text_versioning(self, contact):
        """Test that consent text and version are tracked."""
        record = ConsentRecord.objects.create(
            contact=contact,
            consent_type=ConsentRecord.CONSENT_TYPE_TOS,
            action=ConsentRecord.ACTION_GRANTED,
            consent_text="I agree to the Terms of Service and Privacy Policy",
            consent_version="v2.1",
            source="signup",
        )
        
        assert record.consent_text == "I agree to the Terms of Service and Privacy Policy"
        assert record.consent_version == "v2.1"
