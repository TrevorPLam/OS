"""Tests for firm configuration updates with audit logging and rollback semantics."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.firm.audit import AuditEvent
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
@pytest.mark.django_db
def actor():
    return User.objects.create_user(
        username="config-admin",
        email="config-admin@example.com",
        password="testpass123",
    )


@pytest.fixture
@pytest.mark.django_db
def firm():
    return Firm.objects.create(
        name="Config Firm",
        slug="config-firm",
        status="trial",
        trial_ends_at=timezone.now() + timedelta(days=7),
    )


@pytest.mark.django_db
def test_config_update_creates_audit_event(firm, actor):
    previous = firm.apply_config_update(
        actor=actor,
        updates={'currency': 'EUR', 'max_users': 10},
        reason='Plan upgrade',
    )

    event = AuditEvent.objects.filter(
        action='firm_settings_updated', target_id=str(firm.id)
    ).first()

    assert event is not None
    assert event.category == AuditEvent.CATEGORY_CONFIG
    assert event.metadata['changes']['currency']['before'] == previous['currency']
    assert event.metadata['changes']['currency']['after'] == 'EUR'


@pytest.mark.django_db
def test_config_rollback_restores_previous_values(firm, actor):
    previous = firm.apply_config_update(
        actor=actor,
        updates={'currency': 'EUR'},
        reason='Currency update',
    )

    firm.rollback_config_update(actor=actor, previous_values=previous, reason='Undo change')
    firm.refresh_from_db()

    assert firm.currency == previous['currency']

    event = AuditEvent.objects.filter(
        action='firm_settings_rolled_back', target_id=str(firm.id)
    ).first()
    assert event is not None


@pytest.mark.django_db
def test_config_update_prevents_unsafe_limits(firm, actor):
    firm.current_users_count = 5
    firm.save(update_fields=['current_users_count'])

    with pytest.raises(ValidationError):
        firm.apply_config_update(
            actor=actor,
            updates={'max_users': 3},
            reason='Unsafe downgrade',
        )


@pytest.mark.django_db
def test_config_update_prevents_invalid_status_transition(firm, actor):
    firm.status = 'canceled'
    firm.trial_ends_at = None
    firm.save(update_fields=['status', 'trial_ends_at'])

    with pytest.raises(ValidationError):
        firm.apply_config_update(
            actor=actor,
            updates={'status': 'active'},
            reason='Invalid transition',
        )
