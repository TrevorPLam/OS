import pytest

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from modules.delivery.models import DeliveryEdge, DeliveryNode, DeliveryTemplate
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", password="pass1234")


@pytest.fixture
def template(db, firm, user):
    return DeliveryTemplate.objects.create(
        firm=firm,
        name="Implementation",
        code="IMP-001",
        version=1,
        created_by=user,
    )


@pytest.mark.django_db
class TestDeliveryTemplate:
    """Test delivery template DAG behavior."""

    def test_publish_sets_validation_hash(self, template):
        """Publishing should validate and compute hash."""
        DeliveryNode.objects.create(
            firm=template.firm,
            template=template,
            node_id="node_a",
            type="task",
            title="Start",
        )
        DeliveryNode.objects.create(
            firm=template.firm,
            template=template,
            node_id="node_b",
            type="task",
            title="Finish",
        )
        DeliveryEdge.objects.create(
            firm=template.firm,
            template=template,
            from_node_id="node_a",
            to_node_id="node_b",
        )

        template.save()
        template.publish()
        template.refresh_from_db()

        assert template.status == "published"
        assert template.validation_hash

    def test_publish_rejects_cycles(self, template):
        """Cyclic graphs should fail validation."""
        DeliveryNode.objects.create(
            firm=template.firm,
            template=template,
            node_id="node_a",
            type="task",
            title="Start",
        )
        DeliveryNode.objects.create(
            firm=template.firm,
            template=template,
            node_id="node_b",
            type="task",
            title="Finish",
        )
        DeliveryEdge.objects.create(
            firm=template.firm,
            template=template,
            from_node_id="node_a",
            to_node_id="node_b",
        )
        DeliveryEdge.objects.create(
            firm=template.firm,
            template=template,
            from_node_id="node_b",
            to_node_id="node_a",
        )

        with pytest.raises(ValidationError):
            template.publish()

    def test_published_template_is_immutable(self, template):
        """Published templates should reject structural changes."""
        DeliveryNode.objects.create(
            firm=template.firm,
            template=template,
            node_id="node_a",
            type="task",
            title="Start",
        )
        template.save()
        template.publish()

        DeliveryNode.objects.create(
            firm=template.firm,
            template=template,
            node_id="node_b",
            type="task",
            title="Finish",
        )

        with pytest.raises(ValidationError):
            template.full_clean()


@pytest.mark.django_db
class TestDeliveryNode:
    """Test delivery node validation."""

    def test_fixed_assignee_requires_user(self, template):
        """Fixed assignee policy should require a user."""
        node = DeliveryNode(
            firm=template.firm,
            template=template,
            node_id="node_a",
            type="task",
            title="Work",
            assignee_policy="fixed",
        )

        with pytest.raises(ValidationError):
            node.full_clean()


@pytest.mark.django_db
class TestDeliveryEdge:
    """Test delivery edge validation."""

    def test_self_loop_rejected(self, template):
        """Edges should not allow self-loops."""
        edge = DeliveryEdge(
            firm=template.firm,
            template=template,
            from_node_id="node_a",
            to_node_id="node_a",
        )

        with pytest.raises(ValidationError):
            edge.full_clean()
