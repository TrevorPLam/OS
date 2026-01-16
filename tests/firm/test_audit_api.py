import csv
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from rest_framework.test import APIClient

from modules.firm.audit import AuditEvent
from modules.firm.models import Firm, FirmMembership
from tests.utils.query_assertions import assert_max_queries


@pytest.fixture
def audit_api_client(db):
    user = get_user_model().objects.create_user(username="auditor", email="auditor@example.com", password="pass1234")
    firm = Firm.objects.create(name="Audit Firm", slug="audit-firm")
    FirmMembership.objects.create(firm=firm, user=user, role="owner")
    perms = Permission.objects.filter(codename__in=["review_audit_events", "export_audit_events"])
    user.user_permissions.add(*perms)

    client = APIClient()
    client.force_authenticate(user=user)
    session = client.session
    session["active_firm_id"] = firm.id
    session.save()

    return client, firm, user


@pytest.mark.django_db
@pytest.mark.performance
def test_audit_events_filter_by_category_and_severity(audit_api_client):
    client, firm, user = audit_api_client
    other_firm = Firm.objects.create(name="Other", slug="other")

    AuditEvent.objects.create(
        firm=firm,
        category=AuditEvent.CATEGORY_AUTH,
        action="login_success",
        severity=AuditEvent.SEVERITY_INFO,
        actor=user,
    )
    matching = AuditEvent.objects.create(
        firm=firm,
        category=AuditEvent.CATEGORY_AUTH,
        action="password_reset",
        severity=AuditEvent.SEVERITY_CRITICAL,
        actor=user,
    )
    AuditEvent.objects.create(
        firm=other_firm,
        category=AuditEvent.CATEGORY_AUTH,
        action="login_failed",
        severity=AuditEvent.SEVERITY_CRITICAL,
    )

    # Guard the filtered list endpoint against N+1 regressions.
    with assert_max_queries(15):
        response = client.get("/api/v1/firm/audit-events/?category=AUTH&severity=CRITICAL")
    assert response.status_code == 200

    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == matching.id
    assert results[0]["action"] == "password_reset"


@pytest.mark.django_db
def test_audit_events_filter_by_time_range(audit_api_client):
    client, firm, user = audit_api_client
    earlier = timezone.now() - timezone.timedelta(days=2)

    AuditEvent.objects.create(
        firm=firm,
        category=AuditEvent.CATEGORY_SYSTEM,
        action="old_event",
        severity=AuditEvent.SEVERITY_INFO,
        actor=user,
        timestamp=earlier,
    )
    recent = AuditEvent.objects.create(
        firm=firm,
        category=AuditEvent.CATEGORY_SYSTEM,
        action="recent_event",
        severity=AuditEvent.SEVERITY_INFO,
        actor=user,
    )

    start = (earlier + timezone.timedelta(days=1)).isoformat()
    response = client.get("/api/v1/firm/audit-events/", {"occurred_after": start})
    assert response.status_code == 200

    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == recent.id


@pytest.mark.django_db
def test_audit_events_export_csv_respects_limit(audit_api_client):
    client, firm, user = audit_api_client
    AuditEvent.objects.create(

    # Create more events than the requested export limit
    for i in range(15):
        AuditEvent.objects.create(
            firm=firm,
            category=AuditEvent.CATEGORY_CONFIG,
            action=f"extra_config_{i}",
            severity=AuditEvent.SEVERITY_WARNING,
            actor=user,
        )

    # Create a specific event we will assert is present in the limited results
    AuditEvent.objects.create(
        firm=firm,
        category=AuditEvent.CATEGORY_CONFIG,
        action="config_changed",
        severity=AuditEvent.SEVERITY_WARNING,
        actor=user,
        request_id="req-123",
        metadata={"field": "timezone"},
    )

    response = client.get("/api/v1/firm/audit-events/export/?format=csv&limit=10")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")

    content = response.content.decode("utf-8")
    rows = list(csv.DictReader(StringIO(content)))
    assert len(rows) == 10
    assert any(row["action"] == "config_changed" and row["request_id"] == "req-123" for row in rows)


@pytest.mark.django_db
def test_audit_events_export_json_returns_results(audit_api_client):
    client, firm, user = audit_api_client
    AuditEvent.objects.create(
        firm=firm,
        category=AuditEvent.CATEGORY_CONFIG,
        action="config_saved",
        severity=AuditEvent.SEVERITY_INFO,
        actor=user,
    )

    response = client.get("/api/v1/firm/audit-events/export/?format=json")
    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["results"][0]["action"] == "config_saved"
