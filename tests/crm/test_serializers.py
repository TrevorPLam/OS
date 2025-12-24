"""
Tests for CRM Serializers - Validation Logic.

Tests cover:
- Email validation
- Phone number validation
- Website URL validation
- Business logic validation (date ranges, cross-entity relationships)
"""
import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from api.crm.serializers import ClientSerializer, ProposalSerializer, ContractSerializer
from modules.clients.models import Client
from modules.crm.models import Contract, Proposal
from modules.firm.models import Firm


@pytest.mark.unit
@pytest.mark.django_db
class TestClientSerializer:
    """Test suite for ClientSerializer validation."""

    def test_valid_email_format(self):
        """Test that valid email formats are accepted."""
        valid_emails = [
            'test@example.com',
            'user.name@company.co.uk',
            'info+tag@domain.com',
        ]
        serializer = ClientSerializer()
        for email in valid_emails:
            result = serializer.validate_primary_contact_email(email)
            assert result == email.lower()

    def test_invalid_email_format(self):
        """Test that invalid email formats are rejected."""
        invalid_emails = [
            'invalid',
            'missing@domain',
            '@example.com',
            'user@',
        ]
        serializer = ClientSerializer()
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                serializer.validate_primary_contact_email(email)

    def test_valid_phone_numbers(self):
        """Test that valid phone formats are accepted."""
        valid_phones = [
            '+1234567890',
            '123-456-7890',
            '(123) 456-7890',
            '+44 20 1234 5678',
        ]
        serializer = ClientSerializer()
        for phone in valid_phones:
            result = serializer.validate_primary_contact_phone(phone)
            assert result == phone  # Should return unchanged

    def test_invalid_phone_numbers(self):
        """Test that invalid phone formats are rejected."""
        invalid_phones = [
            '123',  # Too short
            'not-a-phone',
            'abc1234567890',
        ]
        serializer = ClientSerializer()
        for phone in invalid_phones:
            with pytest.raises(ValidationError):
                serializer.validate_primary_contact_phone(phone)

    def test_valid_website_urls(self):
        """Test that valid URLs are accepted."""
        valid_urls = [
            'http://example.com',
            'https://www.company.com',
            'https://subdomain.example.org',
        ]
        serializer = ClientSerializer()
        for url in valid_urls:
            result = serializer.validate_website(url)
            assert result == url

    def test_invalid_website_urls(self):
        """Test that invalid URLs are rejected."""
        invalid_urls = [
            'example.com',  # Missing protocol
            'ftp://example.com',  # Wrong protocol
            'just-text',
        ]
        serializer = ClientSerializer()
        for url in invalid_urls:
            with pytest.raises(ValidationError):
                serializer.validate_website(url)


@pytest.mark.unit
@pytest.mark.django_db
class TestProposalSerializer:
    """Test suite for ProposalSerializer validation."""

    def test_positive_total_value(self):
        """Test that total value must be positive."""
        serializer = ProposalSerializer()

        # Valid positive value
        result = serializer.validate_total_value(1000.00)
        assert result == 1000.00

        # Invalid zero or negative
        with pytest.raises(ValidationError):
            serializer.validate_total_value(0)

        with pytest.raises(ValidationError):
            serializer.validate_total_value(-100)

    def test_future_valid_until_date(self):
        """Test that valid_until must be in the future."""
        serializer = ProposalSerializer()

        # Future date is valid
        future_date = (timezone.now() + timedelta(days=30)).date()
        result = serializer.validate_valid_until(future_date)
        assert result == future_date

        # Past date is invalid
        past_date = (timezone.now() - timedelta(days=1)).date()
        with pytest.raises(ValidationError):
            serializer.validate_valid_until(past_date)


@pytest.mark.unit
@pytest.mark.django_db
class TestContractSerializer:
    """Test suite for ContractSerializer validation."""

    def test_positive_contract_value(self):
        """Test that contract value must be positive."""
        serializer = ContractSerializer()

        # Valid positive value
        result = serializer.validate_total_value(50000.00)
        assert result == 50000.00

        # Invalid zero or negative
        with pytest.raises(ValidationError):
            serializer.validate_total_value(0)

    def test_end_date_after_start_date(self):
        """Test that end_date must be after start_date."""
        serializer = ContractSerializer()

        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=365)

        # Valid date range
        data = {
            'start_date': start_date,
            'end_date': end_date,
        }
        result = serializer.validate(data)
        assert result == data

        # Invalid: end_date before start_date
        invalid_data = {
            'start_date': start_date,
            'end_date': start_date - timedelta(days=1),
        }
        with pytest.raises(ValidationError):
            serializer.validate(invalid_data)

    def test_signed_date_before_start_date(self):
        """Test that signed_date cannot be after start_date."""
        serializer = ContractSerializer()

        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=365)

        # Valid: signed_date before start_date
        data = {
            'start_date': start_date,
            'end_date': end_date,
            'signed_date': start_date - timedelta(days=7),
        }
        result = serializer.validate(data)
        assert result == data

        # Invalid: signed_date after start_date
        invalid_data = {
            'start_date': start_date,
            'end_date': end_date,
            'signed_date': start_date + timedelta(days=1),
        }
        with pytest.raises(ValidationError):
            serializer.validate(invalid_data)


@pytest.mark.integration
@pytest.mark.django_db
class TestProposalContractWorkflow:
    """Integration tests for proposal-to-contract workflow."""

    @pytest.fixture
    def user(self):
        """Create a test user."""
        User = get_user_model()
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def firm(self):
        """Create a test firm."""
        return Firm.objects.create(
            name='Test Firm',
            slug='test-firm'
        )

    @pytest.fixture
    def client(self, user, firm):
        """Create a test client."""
        return Client.objects.create(
            company_name='Test Company',
            primary_contact_email='contact@test.com',
            primary_contact_name='Primary Contact',
            client_since=timezone.now().date(),
            firm=firm,
            account_manager=user
        )

    def test_contract_proposal_client_matching(self, client, user, firm):
        """Test that contract proposal must belong to same client."""
        # Create proposal for client
        proposal = Proposal.objects.create(
            firm=firm,
            proposal_type='update_client',
            client=client,
            proposal_number='PROP-2025-001',
            title='Test Proposal',
            description='Test description',
            total_value=1000,
            currency='USD',
            status='draft',
            valid_until=timezone.now().date() + timedelta(days=30),
            created_by=user
        )

        # Create different client
        different_client = Client.objects.create(
            company_name='Different Company',
            primary_contact_email='different@test.com',
            primary_contact_name='Other Contact',
            client_since=timezone.now().date(),
            firm=firm,
            account_manager=user
        )

        serializer = ContractSerializer()

        # Invalid: proposal belongs to different client
        invalid_data = {
            'client': different_client,
            'proposal': proposal,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=365),
        }

        with pytest.raises(ValidationError) as exc_info:
            serializer.validate(invalid_data)

        assert 'proposal' in str(exc_info.value)
