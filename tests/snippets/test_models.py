import pytest

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from modules.firm.models import Firm
from modules.snippets.models import Snippet, SnippetFolder

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", password="pass1234")


@pytest.mark.django_db
class TestSnippet:
    """Test snippet validation and rendering."""

    def test_invalid_shortcut_rejected(self, firm, user):
        """Shortcuts must match allowed pattern."""
        snippet = Snippet(
            firm=firm,
            created_by=user,
            shortcut="Bad Shortcut!",
            name="Bad",
            content="Hello",
            context="email",
        )

        with pytest.raises(ValidationError):
            snippet.full_clean()

    def test_duplicate_shortcut_personal(self, firm, user):
        """Personal snippets should not duplicate shortcuts."""
        Snippet.objects.create(
            firm=firm,
            created_by=user,
            shortcut="meeting",
            name="Meeting",
            content="Let's meet",
            context="email",
        )

        duplicate = Snippet(
            firm=firm,
            created_by=user,
            shortcut="meeting",
            name="Duplicate",
            content="Follow up",
            context="email",
        )

        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_extract_and_render(self, firm, user):
        """Snippets should extract and render variables."""
        snippet = Snippet.objects.create(
            firm=firm,
            created_by=user,
            shortcut="hello",
            name="Hello",
            content="Hi {{contact_name}}",
            context="email",
        )

        assert snippet.extract_variables() == ["contact_name"]
        assert snippet.render({"contact_name": "Sam"}) == "Hi Sam"

    def test_increment_usage(self, firm, user):
        """Usage tracking should update counts and timestamps."""
        snippet = Snippet.objects.create(
            firm=firm,
            created_by=user,
            shortcut="status",
            name="Status",
            content="Status update",
            context="note",
        )

        snippet.increment_usage()
        snippet.refresh_from_db()

        assert snippet.usage_count == 1
        assert snippet.last_used_at is not None


@pytest.mark.django_db
class TestSnippetFolder:
    """Test snippet folder behaviors."""

    def test_snippet_count(self, firm, user):
        """Folder should count attached snippets."""
        folder = SnippetFolder.objects.create(
            firm=firm,
            name="General",
            created_by=user,
        )

        Snippet.objects.create(
            firm=firm,
            created_by=user,
            shortcut="one",
            name="One",
            content="One",
            folder=folder,
        )
        Snippet.objects.create(
            firm=firm,
            created_by=user,
            shortcut="two",
            name="Two",
            content="Two",
            folder=folder,
        )

        assert folder.snippet_count() == 2
