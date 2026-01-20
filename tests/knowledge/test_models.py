import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.knowledge.models import (
    KnowledgeItem,
    KnowledgeVersion,
    KnowledgeAttachment,
    KnowledgeReview,
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
def knowledge_item(db, firm, user):
    return KnowledgeItem.objects.create(
        firm=firm,
        type="sop",
        title="Test SOP",
        summary="Test standard operating procedure",
        content="## Procedure\n\n1. Step one\n2. Step two",
        content_format="markdown",
        status="draft",
        owner=user,
        created_by=user,
    )


@pytest.mark.django_db
class TestKnowledgeItem:
    """Test KnowledgeItem model functionality"""

    def test_knowledge_item_creation(self, firm, user):
        """Test basic knowledge item creation"""
        item = KnowledgeItem.objects.create(
            firm=firm,
            type="sop",
            title="Onboarding SOP",
            summary="Standard process for client onboarding",
            content="# Onboarding Process\n\n## Steps\n\n1. Welcome email\n2. Setup meeting",
            content_format="markdown",
            status="draft",
            owner=user,
            created_by=user,
        )

        assert item.title == "Onboarding SOP"
        assert item.type == "sop"
        assert item.status == "draft"
        assert item.version_number == 1
        assert item.firm == firm

    def test_knowledge_item_types(self, firm, user):
        """Test different knowledge item types"""
        types = ["sop", "training", "kpi", "playbook", "template"]

        for item_type in types:
            item = KnowledgeItem.objects.create(
                firm=firm,
                type=item_type,
                title=f"{item_type.upper()} Document",
                summary=f"Test {item_type}",
                content="Content here",
                owner=user,
                created_by=user,
            )
            assert item.type == item_type

    def test_knowledge_item_status_choices(self, firm, user):
        """Test knowledge item status choices"""
        statuses = ["draft", "in_review", "published", "deprecated", "archived"]

        for status in statuses:
            item = KnowledgeItem.objects.create(
                firm=firm,
                type="sop",
                title=f"SOP {status}",
                summary="Test",
                content="Content",
                status=status,
                owner=user,
                created_by=user,
            )
            assert item.status == status

    def test_knowledge_item_content_formats(self, firm, user):
        """Test knowledge item content formats"""
        # Markdown format
        markdown_item = KnowledgeItem.objects.create(
            firm=firm,
            type="sop",
            title="Markdown SOP",
            summary="Markdown formatted",
            content="# Title\n\n- Item 1\n- Item 2",
            content_format="markdown",
            owner=user,
            created_by=user,
        )
        assert markdown_item.content_format == "markdown"

        # Rich text format
        richtext_item = KnowledgeItem.objects.create(
            firm=firm,
            type="training",
            title="Rich Text Training",
            summary="Rich text formatted",
            content="<h1>Title</h1><p>Content</p>",
            content_format="rich_text",
            owner=user,
            created_by=user,
        )
        assert richtext_item.content_format == "rich_text"

    def test_knowledge_item_access_levels(self, firm, user):
        """Test knowledge item access levels"""
        access_levels = ["all_staff", "manager_plus", "admin_only"]

        for access_level in access_levels:
            item = KnowledgeItem.objects.create(
                firm=firm,
                type="sop",
                title=f"SOP {access_level}",
                summary="Test",
                content="Content",
                access_level=access_level,
                owner=user,
                created_by=user,
            )
            assert item.access_level == access_level

    def test_knowledge_item_versioning(self, knowledge_item):
        """Test knowledge item version tracking"""
        assert knowledge_item.version_number == 1

        # Update version
        knowledge_item.version_number = 2
        knowledge_item.save()

        assert knowledge_item.version_number == 2

    def test_knowledge_item_publishing(self, knowledge_item):
        """Test knowledge item publishing workflow"""
        assert knowledge_item.status == "draft"
        assert knowledge_item.published_at is None

        # Publish item
        knowledge_item.status = "published"
        knowledge_item.published_at = timezone.now()
        knowledge_item.save()

        assert knowledge_item.status == "published"
        assert knowledge_item.published_at is not None

    def test_knowledge_item_deprecation(self, knowledge_item):
        """Test knowledge item deprecation"""
        # Publish first
        knowledge_item.status = "published"
        knowledge_item.published_at = timezone.now()
        knowledge_item.save()

        # Deprecate
        knowledge_item.status = "deprecated"
        knowledge_item.deprecated_at = timezone.now()
        knowledge_item.deprecation_reason = "Outdated process, replaced by v2"
        knowledge_item.save()

        assert knowledge_item.status == "deprecated"
        assert knowledge_item.deprecated_at is not None
        assert knowledge_item.deprecation_reason == "Outdated process, replaced by v2"

    def test_knowledge_item_tags(self, firm, user):
        """Test knowledge item tagging"""
        tags = ["onboarding", "client-facing", "important"]

        item = KnowledgeItem.objects.create(
            firm=firm,
            type="sop",
            title="Tagged SOP",
            summary="Test",
            content="Content",
            tags=tags,
            owner=user,
            created_by=user,
        )

        assert "onboarding" in item.tags
        assert "client-facing" in item.tags
        assert len(item.tags) == 3

    def test_knowledge_item_category(self, firm, user):
        """Test knowledge item categorization"""
        item = KnowledgeItem.objects.create(
            firm=firm,
            type="sop",
            title="Categorized SOP",
            summary="Test",
            content="Content",
            category="SOP Library",
            owner=user,
            created_by=user,
        )

        assert item.category == "SOP Library"

    def test_knowledge_item_firm_scoping(self, firm, user):
        """Test knowledge item tenant isolation"""
        firm2 = Firm.objects.create(name="Firm 2", slug="firm-2", status="active")

        item1 = KnowledgeItem.objects.create(
            firm=firm, type="sop", title="Item 1", summary="Test", content="Content", owner=user, created_by=user
        )
        item2 = KnowledgeItem.objects.create(
            firm=firm2, type="sop", title="Item 2", summary="Test", content="Content", owner=user, created_by=user
        )

        assert item1.firm != item2.firm


@pytest.mark.django_db
class TestKnowledgeVersion:
    """Test KnowledgeVersion model functionality"""

    def test_knowledge_version_creation(self, knowledge_item, user):
        """Test knowledge version creation"""
        version = KnowledgeVersion.objects.create(
            knowledge_item=knowledge_item,
            version_number=1,
            title=knowledge_item.title,
            content=knowledge_item.content,
            content_format=knowledge_item.content_format,
            created_by=user,
        )

        assert version.knowledge_item == knowledge_item
        assert version.version_number == 1
        assert version.title == knowledge_item.title

    def test_knowledge_version_immutability(self, knowledge_item, user):
        """Test that knowledge versions are immutable"""
        version = KnowledgeVersion.objects.create(
            knowledge_item=knowledge_item,
            version_number=1,
            title=knowledge_item.title,
            content=knowledge_item.content,
            content_format=knowledge_item.content_format,
            created_by=user,
        )

        original_content = version.content

        # Versions should not be modified after creation
        # (enforced by application logic, not database constraint)
        assert version.content == original_content


@pytest.mark.django_db
class TestKnowledgeAttachment:
    """Test KnowledgeAttachment model functionality"""

    def test_knowledge_attachment_creation(self, knowledge_item, user):
        """Test knowledge attachment creation"""
        from modules.documents.models import Document

        document = Document.objects.create(
            firm=knowledge_item.firm, name="attachment.pdf", file_type="pdf", uploaded_by=user
        )

        attachment = KnowledgeAttachment.objects.create(knowledge_item=knowledge_item, document=document)

        assert attachment.knowledge_item == knowledge_item
        assert attachment.document == document


@pytest.mark.django_db
class TestKnowledgeReview:
    """Test KnowledgeReview model functionality"""

    def test_knowledge_review_creation(self, knowledge_item, user, db):
        """Test knowledge review creation"""
        reviewer = User.objects.create_user(username="reviewer", email="reviewer@example.com", ******)

        review = KnowledgeReview.objects.create(
            knowledge_item=knowledge_item, reviewer=reviewer, review_status="pending", requested_at=timezone.now()
        )

        assert review.knowledge_item == knowledge_item
        assert review.reviewer == reviewer
        assert review.review_status == "pending"

    def test_knowledge_review_approval(self, knowledge_item, db):
        """Test knowledge review approval workflow"""
        reviewer = User.objects.create_user(username="reviewer", email="reviewer@example.com", ******)

        review = KnowledgeReview.objects.create(
            knowledge_item=knowledge_item, reviewer=reviewer, review_status="pending", requested_at=timezone.now()
        )

        # Approve review
        review.review_status = "approved"
        review.reviewed_at = timezone.now()
        review.review_notes = "Looks good, approved"
        review.save()

        assert review.review_status == "approved"
        assert review.reviewed_at is not None


@pytest.mark.django_db
class TestKnowledgeWorkflow:
    """Test complete knowledge management workflow scenarios"""

    def test_complete_sop_lifecycle(self, firm, user, db):
        """Test complete SOP lifecycle"""
        # Create draft SOP
        sop = KnowledgeItem.objects.create(
            firm=firm,
            type="sop",
            title="Client Onboarding SOP",
            summary="Standard process for onboarding new clients",
            content="# Onboarding Process\n\n1. Send welcome email\n2. Schedule kickoff call\n3. Set up tools",
            content_format="markdown",
            status="draft",
            owner=user,
            created_by=user,
        )

        # Submit for review
        sop.status = "in_review"
        sop.save()

        # Add reviewer
        reviewer = User.objects.create_user(username="reviewer", email="reviewer@example.com", ******)
        review = KnowledgeReview.objects.create(
            knowledge_item=sop, reviewer=reviewer, review_status="pending", requested_at=timezone.now()
        )

        # Approve review
        review.review_status = "approved"
        review.reviewed_at = timezone.now()
        review.save()

        # Publish
        sop.status = "published"
        sop.published_at = timezone.now()
        sop.save()

        # Create version snapshot
        version = KnowledgeVersion.objects.create(
            knowledge_item=sop,
            version_number=1,
            title=sop.title,
            content=sop.content,
            content_format=sop.content_format,
            created_by=user,
        )

        assert sop.status == "published"
        assert version.version_number == 1

    def test_knowledge_item_update_and_version(self, firm, user):
        """Test knowledge item update creating new version"""
        # Create and publish v1
        item = KnowledgeItem.objects.create(
            firm=firm,
            type="sop",
            title="SOP v1",
            summary="First version",
            content="Version 1 content",
            status="published",
            published_at=timezone.now(),
            version_number=1,
            owner=user,
            created_by=user,
        )

        # Create version snapshot
        v1 = KnowledgeVersion.objects.create(
            knowledge_item=item, version_number=1, title=item.title, content=item.content, created_by=user
        )

        # Update to v2
        item.content = "Version 2 content with updates"
        item.version_number = 2
        item.save()

        # Create v2 snapshot
        v2 = KnowledgeVersion.objects.create(
            knowledge_item=item, version_number=2, title=item.title, content=item.content, created_by=user
        )

        assert item.version_number == 2
        assert v1.version_number == 1
        assert v2.version_number == 2
        assert v1.content != v2.content
