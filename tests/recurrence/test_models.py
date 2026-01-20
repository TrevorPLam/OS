import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.delivery.models import DeliveryTemplate
from modules.firm.models import Firm
from modules.recurrence.models import RecurrenceGeneration, RecurrenceRule

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
        name="Monthly Reporting",
        code="REP-001",
        version=1,
        created_by=user,
    )


@pytest.fixture
def rule(db, firm, user, template):
    return RecurrenceRule.objects.create(
        firm=firm,
        scope="delivery_template",
        target_delivery_template=template,
        anchor_type="calendar",
        frequency="monthly",
        interval=1,
        timezone="UTC",
        start_at=timezone.now() - timedelta(days=1),
        name="Monthly Report",
        created_by=user,
    )


@pytest.mark.django_db
class TestRecurrenceRule:
    """Test recurrence rule validation and state transitions."""

    def test_invalid_timezone_rejected(self, firm, template, user):
        """Invalid timezones should fail validation."""
        rule = RecurrenceRule(
            firm=firm,
            scope="delivery_template",
            target_delivery_template=template,
            anchor_type="calendar",
            frequency="monthly",
            interval=1,
            timezone="Invalid/Zone",
            start_at=timezone.now(),
            name="Bad TZ",
            created_by=user,
        )

        with pytest.raises(ValidationError):
            rule.full_clean()

    def test_missing_target_rejected(self, firm, user):
        """Rules require exactly one target."""
        rule = RecurrenceRule(
            firm=firm,
            scope="delivery_template",
            anchor_type="calendar",
            frequency="monthly",
            interval=1,
            timezone="UTC",
            start_at=timezone.now(),
            name="No Target",
            created_by=user,
        )

        with pytest.raises(ValidationError):
            rule.full_clean()

    def test_pause_resume_cancel(self, rule, user):
        """Rule status transitions should update audit fields."""
        rule.pause(user)
        rule.refresh_from_db()

        assert rule.status == "paused"
        assert rule.paused_by == user
        assert rule.paused_at is not None

        rule.resume(user)
        rule.refresh_from_db()

        assert rule.status == "active"

        rule.cancel(user)
        rule.refresh_from_db()

        assert rule.status == "canceled"
        assert rule.canceled_by == user
        assert rule.canceled_at is not None


@pytest.mark.django_db
class TestRecurrenceGeneration:
    """Test recurrence generation idempotency."""

    def test_idempotency_key_computed(self, firm, rule):
        """Idempotency key should be computed before save."""
        generation = RecurrenceGeneration.objects.create(
            firm=firm,
            recurrence_rule=rule,
            period_key="2026-01",
            period_starts_at=timezone.now(),
            period_ends_at=timezone.now() + timedelta(days=30),
            target_object_type="work_item",
            status="planned",
        )

        assert generation.idempotency_key
        assert generation.idempotency_key == RecurrenceGeneration.compute_idempotency_key(
            firm.id,
            rule.id,
            generation.period_key,
            generation.target_discriminator,
        )
