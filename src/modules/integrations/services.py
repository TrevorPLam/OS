from __future__ import annotations

import hashlib
import hmac
from typing import Any, Dict, Iterable
from urllib.parse import urlencode

import requests
from django.utils import timezone

from modules.integrations.models import (
    GoogleAnalyticsConfig,
    SalesforceConnection,
    SalesforceSyncLog,
    SlackIntegration,
    SlackMessageLog,
)


class SalesforceService:
    API_VERSION = "v57.0"
    TOKEN_URL = "https://login.salesforce.com/services/oauth2/token"
    AUTHORIZE_URL = "https://login.salesforce.com/services/oauth2/authorize"

    def __init__(self, connection: SalesforceConnection):
        self.connection = connection

    def authorization_url(self, *, redirect_uri: str, state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self.connection.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    def exchange_code(self, *, code: str, redirect_uri: str) -> Dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.connection.client_id,
            "client_secret": self.connection.client_secret,
            "redirect_uri": redirect_uri,
        }
        response = requests.post(self.TOKEN_URL, data=data, timeout=30)
        if response.status_code != 200:
            error_message = response.text or "Unable to exchange Salesforce code"
            self.connection.mark_error(error_message)
            return {"success": False, "error": error_message}

        payload = response.json()
        self._update_tokens(payload)
        return {"success": True, "payload": payload}

    def refresh_access_token(self) -> Dict[str, Any]:
        if not self.connection.refresh_token:
            return {"success": False, "error": "Refresh token missing"}
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.connection.refresh_token,
            "client_id": self.connection.client_id,
            "client_secret": self.connection.client_secret,
        }
        response = requests.post(self.TOKEN_URL, data=data, timeout=30)
        if response.status_code != 200:
            error_message = response.text or "Unable to refresh Salesforce token"
            self.connection.mark_error(error_message)
            return {"success": False, "error": error_message}

        payload = response.json()
        self._update_tokens(payload)
        return {"success": True, "payload": payload}

    def upsert_lead(self, *, payload: dict[str, Any]) -> SalesforceSyncLog:
        return self._upsert(object_type="Lead", external_id_field="Email", payload=payload)

    def upsert_contact(self, *, payload: dict[str, Any]) -> SalesforceSyncLog:
        return self._upsert(object_type="Contact", external_id_field="Email", payload=payload)

    def sync_opportunity(self, *, payload: dict[str, Any]) -> SalesforceSyncLog:
        return self._upsert(object_type="Opportunity", external_id_field="Name", payload=payload)

    def _upsert(self, *, object_type: str, external_id_field: str, payload: dict[str, Any]) -> SalesforceSyncLog:
        try:
            response = self._request(
                method="patch",
                path=f"sobjects/{object_type}/{external_id_field}/{payload.get(external_id_field, '')}",
                json_body=payload,
            )
            ok = response.status_code in (200, 201, 204)
            message = "Synced" if ok else response.text
            log = SalesforceSyncLog.objects.create(
                connection=self.connection,
                firm=self.connection.firm,
                object_type=object_type.lower(),
                direction="push",
                status="success" if ok else "error",
                message=message[:490],
                payload_snippet={"keys": list(payload.keys())},
            )
            if ok:
                self.connection.last_synced_at = timezone.now()
                self.connection.status = "active"
                self.connection.save(update_fields=["last_synced_at", "status"])
            else:
                self.connection.mark_error(message)
            return log
        except Exception as exc:
            message = str(exc)
            self.connection.mark_error(message)
            return SalesforceSyncLog.objects.create(
                connection=self.connection,
                firm=self.connection.firm,
                object_type=object_type.lower(),
                direction="push",
                status="error",
                message=message[:490],
                payload_snippet={"keys": list(payload.keys())},
            )

    def _request(self, *, method: str, path: str, json_body: dict[str, Any]) -> requests.Response:
        if not self.connection.access_token or not self.connection.instance_url:
            raise ValueError("Salesforce connection missing access_token or instance_url")
        url = f"{self.connection.instance_url}/services/data/{self.API_VERSION}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.connection.access_token}", "Content-Type": "application/json"}
        response = requests.request(method, url, headers=headers, json=json_body, timeout=30)
        if response.status_code == 401:
            refresh_result = self.refresh_access_token()
            if refresh_result.get("success"):
                headers["Authorization"] = f"Bearer {self.connection.access_token}"
                response = requests.request(method, url, headers=headers, json=json_body, timeout=30)
        return response

    def _update_tokens(self, payload: dict[str, Any]) -> None:
        self.connection.access_token = payload.get("access_token", "")
        self.connection.refresh_token = payload.get("refresh_token") or self.connection.refresh_token
        self.connection.instance_url = payload.get("instance_url", "")
        self.connection.scopes = payload.get("scope", "").split(" ") if payload.get("scope") else self.connection.scopes
        expires_in = payload.get("expires_in")
        if expires_in:
            self.connection.expires_at = timezone.now() + timezone.timedelta(seconds=int(expires_in))
        self.connection.status = "active"
        self.connection.last_error = ""
        self.connection.save(update_fields=["access_token", "refresh_token", "instance_url", "scopes", "expires_at", "status", "last_error"])


class SlackService:
    API_URL = "https://slack.com/api/chat.postMessage"

    def __init__(self, integration: SlackIntegration):
        self.integration = integration

    def send_message(self, *, text: str, channel: str | None = None, attachments: Iterable[dict[str, Any]] | None = None) -> bool:
        target_channel = channel or self.integration.default_channel
        if not target_channel or not self.integration.bot_token:
            return False

        payload: dict[str, Any] = {"channel": target_channel, "text": text}
        if attachments:
            payload["attachments"] = list(attachments)

        headers = {
            "Authorization": f"Bearer {self.integration.bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        response = requests.post(self.API_URL, headers=headers, json=payload, timeout=10)
        ok = response.status_code == 200 and response.json().get("ok")

        SlackMessageLog.objects.create(
            integration=self.integration,
            firm=self.integration.firm,
            channel=target_channel,
            status="sent" if ok else "error",
            message=text[:500],
            response_code=response.status_code,
            response_body=response.text[:1000],
        )

        if ok:
            self.integration.status = "active"
            self.integration.last_health_check = timezone.now()
            self.integration.last_error = ""
            self.integration.save(update_fields=["status", "last_health_check", "last_error"])
        else:
            self.integration.mark_error(response.text or "Slack API error")
        return ok

    @staticmethod
    def verify_signature(*, signing_secret: str, timestamp: str, body: bytes, signature: str) -> bool:
        base_string = f"v0:{timestamp}:{body.decode('utf-8')}"
        computed = hmac.new(signing_secret.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"v0={computed}", signature)


class GoogleAnalyticsService:
    COLLECT_URL = "https://www.google-analytics.com/mp/collect"

    def __init__(self, config: GoogleAnalyticsConfig):
        self.config = config

    def send_events(self, *, client_id: str, events: list[dict[str, Any]]) -> Dict[str, Any]:
        params = {"measurement_id": self.config.measurement_id, "api_secret": self.config.api_secret}
        url = f"{self.COLLECT_URL}?{urlencode(params)}"
        payload = {"client_id": client_id, "events": events}
        response = requests.post(url, json=payload, timeout=10)
        ok = response.status_code in (200, 204)
        if ok:
            self.config.last_event_at = timezone.now()
            self.config.status = "active"
            self.config.last_error = ""
            self.config.save(update_fields=["last_event_at", "status", "last_error"])
        else:
            self.config.mark_error(response.text or "Google Analytics error")
        return {"success": ok, "status_code": response.status_code, "body": response.text}
