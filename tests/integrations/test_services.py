import uuid

import pytest
from django.utils import timezone

from modules.firm.models import Firm
from modules.integrations.models import GoogleAnalyticsConfig, SalesforceConnection, SlackIntegration, SlackMessageLog
from modules.integrations.services import GoogleAnalyticsService, SalesforceService, SlackService


@pytest.mark.django_db
def test_salesforce_service_exchange_and_upsert(monkeypatch):
    firm = Firm.objects.create(name="SF Firm", slug="sf-firm")
    connection = SalesforceConnection.objects.create(firm=firm, client_id="abc123")

    def fake_post(url, data=None, timeout=None):
        class Resp:
            status_code = 200

            def json(self):
                return {
                    "access_token": "token-123",
                    "refresh_token": "refresh-123",
                    "instance_url": "https://example.my.salesforce.com",
                    "expires_in": 3600,
                    "scope": "api refresh_token",
                }

            @property
            def text(self):
                return ""

        return Resp()

    def fake_request(method, url, headers=None, json=None, timeout=None):
        class Resp:
            status_code = 201
            text = "created"

        return Resp()

    monkeypatch.setattr("modules.integrations.services.requests.post", fake_post)
    service = SalesforceService(connection)
    exchange = service.exchange_code(code="abc", redirect_uri="http://localhost/callback")
    assert exchange["success"] is True
    assert connection.access_token == "token-123"

    monkeypatch.setattr("modules.integrations.services.requests.request", fake_request)
    log = service.upsert_contact(payload={"Email": "prospect@example.com", "FirstName": "Prospect"})
    assert log.status == "success"
    assert log.object_type == "contact"


@pytest.mark.django_db
def test_slack_service_send_message(monkeypatch):
    firm = Firm.objects.create(name="Slack Firm", slug="slack-firm")
    integration = SlackIntegration.objects.create(
        firm=firm, bot_token="xoxb-test", default_channel="#alerts", status="active"
    )

    def fake_post(url, headers=None, json=None, timeout=None):
        class Resp:
            status_code = 200

            def json(self):
                return {"ok": True}

            @property
            def text(self):
                return "ok"

        return Resp()

    monkeypatch.setattr("modules.integrations.services.requests.post", fake_post)
    service = SlackService(integration)
    ok = service.send_message(text="Integration test ping")
    assert ok is True
    assert SlackMessageLog.objects.filter(integration=integration, status="sent").exists()


@pytest.mark.django_db
def test_google_analytics_service(monkeypatch):
    firm = Firm.objects.create(name="GA Firm", slug="ga-firm")
    config = GoogleAnalyticsConfig.objects.create(
        firm=firm, measurement_id="G-123", api_secret="secret", status="active"
    )

    def fake_post(url, json=None, timeout=None):
        class Resp:
            status_code = 204
            text = ""

        return Resp()

    monkeypatch.setattr("modules.integrations.services.requests.post", fake_post)
    service = GoogleAnalyticsService(config)
    now = timezone.now()
    result = service.send_events(client_id=str(uuid.uuid4()), events=[{"name": "test_event", "params": {"at": now.isoformat()}}])
    assert result["success"] is True
    assert config.last_event_at is not None
