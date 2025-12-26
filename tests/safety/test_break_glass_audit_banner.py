"""Integration tests for break-glass impersonation banner and audit events."""
import json
import time
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone

from modules.firm.audit import AuditEvent
from modules.firm.middleware import BreakGlassImpersonationMiddleware
from modules.firm.models import BreakGlassSession, Firm, PlatformUserProfile

User = get_user_model()


@pytest.fixture
@pytest.mark.django_db
def firm():
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
@pytest.mark.django_db
def platform_operator(firm):
    operator = User.objects.create_user(
        username="operator",
        email="operator@example.com",
        password="testpass123",
    )
    PlatformUserProfile.objects.create(
        user=operator,
        platform_role=PlatformUserProfile.ROLE_BREAK_GLASS_OPERATOR,
        can_activate_break_glass=True,
        is_platform_active=True,
    )
    return operator


@pytest.fixture
@pytest.mark.django_db
def impersonated_user(firm):
    user = User.objects.create_user(
        username="impersonated",
        email="impersonated@example.com",
        password="testpass123",
    )
    return user


@pytest.fixture
@pytest.mark.django_db
def active_session(firm, platform_operator, impersonated_user):
    return BreakGlassSession.objects.create(
        firm=firm,
        operator=platform_operator,
        impersonated_user=impersonated_user,
        reason="Customer support incident",
        expires_at=timezone.now() + timedelta(minutes=5),
    )


@pytest.mark.django_db
class TestBreakGlassAuditAndBanner:
    def test_activation_logs_audit_event(self, active_session):
        """Creating a break-glass session should create an immutable audit event."""
        event = AuditEvent.objects.filter(
            action='break_glass_activated', target_id=str(active_session.id)
        ).first()
        assert event is not None
        assert event.category == AuditEvent.CATEGORY_BREAK_GLASS
        assert event.actor == active_session.operator

    def test_expiration_logs_audit_event(self, active_session):
        """When a session expires, an audit event should be persisted."""
        # Fast-forward past expiry
        active_session.expires_at = timezone.now() + timedelta(seconds=1)
        active_session.save()
        time.sleep(1.1)
        active_session.save()

        expired = AuditEvent.objects.filter(
            action='break_glass_expired', target_id=str(active_session.id)
        ).first()
        assert expired is not None
        assert expired.metadata.get('impersonated_user_id') == active_session.impersonated_user_id

    def test_revocation_logs_audit_event(self, active_session):
        """When a session is revoked, an audit event should be created."""
        revocation_reason = "Support incident resolved"
        active_session.revoke(revocation_reason)
        active_session.save()

        revoked = AuditEvent.objects.filter(
            action='break_glass_revoked', target_id=str(active_session.id)
        ).first()
        assert revoked is not None
        assert revoked.category == AuditEvent.CATEGORY_BREAK_GLASS
        assert revoked.severity == AuditEvent.SEVERITY_CRITICAL
        assert revoked.reason == revocation_reason
        assert revoked.metadata.get('impersonated_user_id') == active_session.impersonated_user_id
        assert revoked.metadata.get('revoked_at') is not None

    def test_impersonation_banner_header_and_audit(self, firm, platform_operator, active_session):
        """Middleware should emit banner headers and log impersonated requests."""
        request = RequestFactory().get('/api/projects/')
        request.user = platform_operator
        request.firm = firm
        request.firm_context_source = 'session'

        middleware = BreakGlassImpersonationMiddleware(lambda req: HttpResponse("ok", status=200))
        response = middleware(request)

        assert response.status_code == 200
        assert response.headers.get('X-Break-Glass-Impersonation') is not None

        payload = json.loads(response.headers['X-Break-Glass-Impersonation'])
        assert payload['impersonated_user'] == (
            active_session.impersonated_user.get_full_name()
            or active_session.impersonated_user.email
        )

        event = AuditEvent.objects.filter(
            action='break_glass_impersonated_request', target_id=str(active_session.id)
        ).first()
        assert event is not None
        assert event.metadata.get('path') == '/api/projects/'
