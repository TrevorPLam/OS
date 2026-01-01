"""
Tests for Document Approval Workflow (Medium Feature 2.7).

Tests the draft → review → approved → published workflow.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.clients.models import Client
from modules.documents.models import Document, Folder
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    """Create a test firm."""
    return Firm.objects.create(
        name="Test Consulting Firm",
        slug="test-firm",
        subdomain="test",
    )


@pytest.fixture
def user(db, firm):
    """Create a test user."""
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        firm=firm,
    )


@pytest.fixture
def reviewer(db, firm):
    """Create a reviewer user."""
    return User.objects.create_user(
        email="reviewer@example.com",
        password="testpass123",
        firm=firm,
    )


@pytest.fixture
def client(db, firm):
    """Create a test client."""
    return Client.objects.create(
        firm=firm,
        company_name="Test Client Co",
        email="client@example.com",
    )


@pytest.fixture
def folder(db, firm, client):
    """Create a test folder."""
    return Folder.objects.create(
        firm=firm,
        client=client,
        name="Test Folder",
    )


@pytest.fixture
def document(db, firm, client, folder, user):
    """Create a test document in draft status."""
    return Document.objects.create(
        firm=firm,
        client=client,
        folder=folder,
        name="Test Document",
        status="draft",
        file_type="application/pdf",
        file_size_bytes=1024,
        s3_bucket="test-bucket",
        s3_key="test-key",
        uploaded_by=user,
    )


@pytest.mark.django_db
class TestDocumentApprovalWorkflow:
    """Test document approval workflow (draft → review → approved → published)."""

    def test_submit_for_review_success(self, document, user):
        """Test submitting a draft document for review."""
        assert document.status == "draft"
        assert document.submitted_for_review_by is None
        assert document.submitted_for_review_at is None

        document.submit_for_review(user)

        assert document.status == "review"
        assert document.submitted_for_review_by == user
        assert document.submitted_for_review_at is not None

    def test_submit_for_review_non_draft_fails(self, document, user):
        """Test that only draft documents can be submitted for review."""
        document.status = "review"
        document.save()

        with pytest.raises(ValidationError, match="must be 'draft'"):
            document.submit_for_review(user)

    def test_approve_document_success(self, document, user, reviewer):
        """Test approving a document under review."""
        # Submit for review first
        document.submit_for_review(user)

        # Approve
        notes = "Looks good, approved"
        document.approve(reviewer, notes)

        assert document.status == "approved"
        assert document.reviewed_by == reviewer
        assert document.reviewed_at is not None
        assert document.review_notes == notes

    def test_approve_non_review_status_fails(self, document, reviewer):
        """Test that only documents under review can be approved."""
        assert document.status == "draft"

        with pytest.raises(ValidationError, match="must be 'review'"):
            document.approve(reviewer, "Notes")

    def test_reject_document_success(self, document, user, reviewer):
        """Test rejecting a document and returning it to draft."""
        # Submit for review first
        document.submit_for_review(user)

        # Reject
        rejection_notes = "Needs more details"
        document.reject(reviewer, rejection_notes)

        assert document.status == "draft"
        assert document.reviewed_by == reviewer
        assert document.reviewed_at is not None
        assert document.review_notes == rejection_notes
        # Submission fields should be cleared for resubmission
        assert document.submitted_for_review_by is None
        assert document.submitted_for_review_at is None

    def test_reject_without_notes_fails(self, document, user, reviewer):
        """Test that rejection requires notes."""
        document.submit_for_review(user)

        with pytest.raises(ValidationError, match="notes are required"):
            document.reject(reviewer, "")

    def test_publish_document_success(self, document, user, reviewer):
        """Test publishing an approved document."""
        # Go through approval workflow
        document.submit_for_review(user)
        document.approve(reviewer, "Approved")

        # Publish
        document.publish(user)

        assert document.status == "published"
        assert document.published_by == user
        assert document.published_at is not None

    def test_publish_non_approved_fails(self, document, user):
        """Test that only approved documents can be published."""
        assert document.status == "draft"

        with pytest.raises(ValidationError, match="must be 'approved' or 'active'"):
            document.publish(user)

    def test_deprecate_published_document(self, document, user, reviewer):
        """Test deprecating a published document."""
        # Go through full workflow to published
        document.submit_for_review(user)
        document.approve(reviewer, "Approved")
        document.publish(user)

        # Deprecate
        deprecation_reason = "Outdated information"
        document.deprecate(user, deprecation_reason)

        assert document.status == "deprecated"
        assert document.deprecated_by == user
        assert document.deprecated_at is not None
        assert document.deprecation_reason == deprecation_reason

    def test_deprecate_without_reason_fails(self, document, user, reviewer):
        """Test that deprecation requires a reason."""
        document.submit_for_review(user)
        document.approve(reviewer, "Approved")
        document.publish(user)

        with pytest.raises(ValidationError, match="reason is required"):
            document.deprecate(user, "")

    def test_archive_document(self, document, user, reviewer):
        """Test archiving a document."""
        # Archive can happen from any status, but typically from deprecated
        document.submit_for_review(user)
        document.approve(reviewer, "Approved")
        document.publish(user)
        document.deprecate(user, "Outdated")

        document.archive()

        assert document.status == "archived"

    def test_full_workflow_lifecycle(self, document, user, reviewer):
        """Test the complete document lifecycle."""
        # 1. Draft (initial state)
        assert document.status == "draft"

        # 2. Submit for review
        document.submit_for_review(user)
        assert document.status == "review"

        # 3. Approve
        document.approve(reviewer, "Looks good")
        assert document.status == "approved"

        # 4. Publish
        document.publish(user)
        assert document.status == "published"

        # 5. Deprecate
        document.deprecate(user, "No longer current")
        assert document.status == "deprecated"

        # 6. Archive
        document.archive()
        assert document.status == "archived"

    def test_resubmit_after_rejection(self, document, user, reviewer):
        """Test that a rejected document can be resubmitted."""
        # Submit, reject, resubmit
        document.submit_for_review(user)
        document.reject(reviewer, "Needs changes")

        assert document.status == "draft"

        # Can resubmit
        document.submit_for_review(user)
        assert document.status == "review"
        assert document.submitted_for_review_by == user

    def test_legacy_active_status_publish(self, document, user):
        """Test that legacy 'active' status can be published."""
        document.status = "active"
        document.save()

        # Should be able to publish
        document.publish(user)
        assert document.status == "published"

    def test_legacy_active_status_deprecate(self, document, user):
        """Test that legacy 'active' status can be deprecated."""
        document.status = "active"
        document.save()

        # Should be able to deprecate
        document.deprecate(user, "Outdated")
        assert document.status == "deprecated"
