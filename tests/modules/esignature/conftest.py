"""Pytest fixtures for esignature tests."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.esignature.models import DocuSignConnection, Envelope
from modules.firm.models import Firm, FirmMembership

User = get_user_model()


@pytest.fixture
def firm(db):
    """Create a test firm."""
    return Firm.objects.create(
        name="Test Firm",
        slug="test-firm",
    )


@pytest.fixture
def user(db, firm):
    """Create a test user."""
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )
    # Create firm membership
    FirmMembership.objects.create(
        user=user,
        firm=firm,
        role="firm_admin",
    )
    return user


@pytest.fixture
def docusign_connection(db, firm, user):
    """Create a test DocuSign connection."""
    return DocuSignConnection.objects.create(
        firm=firm,
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expires_at=timezone.now() + timedelta(hours=1),
        account_id="test_account_id",
        account_name="Test Account",
        base_uri="https://demo.docusign.net",
        is_active=True,
        connected_by=user,
    )


@pytest.fixture
def envelope(db, firm, docusign_connection, user):
    """Create a test envelope."""
    return Envelope.objects.create(
        firm=firm,
        connection=docusign_connection,
        envelope_id="test_envelope_id",
        status="sent",
        subject="Test Envelope",
        message="Please sign this test document",
        recipients=[
            {
                "email": "signer@example.com",
                "name": "Test Signer",
                "recipient_id": 1,
            }
        ],
        created_by=user,
    )
