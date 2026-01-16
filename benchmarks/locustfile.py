"""
Locust load tests for core API performance baselines.

Document Type: Benchmark Specification
Last Updated: 2026-01-16

Meta-commentary:
- Functionality: exercises authentication, CRUD, list, and search flows for core APIs.
- Mapping: targets /api/v1/auth/login/ for auth, /api/v1/crm/leads/ for CRUD/list/search.
- Reasoning: keeps benchmarks close to real endpoints while allowing env overrides to
  point at seeded data or staging fixtures. Missing identifiers are skipped rather than
  failing the run, so benchmarks stay safe and configurable.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

from locust import HttpUser, between, task
from locust.exception import StopUser


@dataclass(frozen=True)
class BenchmarkConfig:
    """Runtime configuration sourced from environment variables."""

    api_prefix: str
    auth_login_path: str
    crm_leads_path: str
    username: str | None
    password: str | None
    firm_id: str | None
    lead_id: str | None
    search_query: str


def load_config() -> BenchmarkConfig:
    """Load configuration with defaults that mirror the repo's API routes."""

    api_prefix = os.getenv("LOCUST_API_PREFIX", "/api/v1")
    return BenchmarkConfig(
        api_prefix=api_prefix,
        auth_login_path=os.getenv("LOCUST_AUTH_LOGIN_PATH", f"{api_prefix}/auth/login/"),
        crm_leads_path=os.getenv("LOCUST_CRM_LEADS_PATH", f"{api_prefix}/crm/leads/"),
        username=os.getenv("LOCUST_USERNAME"),
        password=os.getenv("LOCUST_PASSWORD"),
        firm_id=os.getenv("LOCUST_FIRM_ID"),
        lead_id=os.getenv("LOCUST_LEAD_ID"),
        search_query=os.getenv("LOCUST_SEARCH_QUERY", "acme"),
    )


class AuthLoginUser(HttpUser):
    """Isolated auth benchmark for login latency and throughput."""

    wait_time = between(1, 3)
    config = load_config()

    def on_start(self) -> None:
        if not (self.config.username and self.config.password):
            raise StopUser("LOCUST_USERNAME and LOCUST_PASSWORD are required for auth benchmarks.")

    @task
    def login(self) -> None:
        payload = {
            "username": self.config.username,
            "password": self.config.password,
        }
        self.client.post(self.config.auth_login_path, json=payload, name="auth:login")


class CRMBenchmarkUser(HttpUser):
    """Authenticated CRM benchmark covering CRUD, list, and search endpoints."""

    wait_time = between(1, 5)
    config = load_config()

    def on_start(self) -> None:
        if not (self.config.username and self.config.password):
            raise StopUser("LOCUST_USERNAME and LOCUST_PASSWORD are required for CRM benchmarks.")
        self._login()

    def _login(self) -> None:
        payload = {
            "username": self.config.username,
            "password": self.config.password,
        }
        response = self.client.post(self.config.auth_login_path, json=payload, name="auth:login")
        if response.status_code != 200:
            raise StopUser("Login failed; cannot run authenticated benchmarks.")

    def _lead_payload(self, *, require_firm: bool) -> dict[str, Any]:
        """Generate a minimal lead payload for create/update operations."""

        if require_firm and not self.config.firm_id:
            raise StopUser("LOCUST_FIRM_ID is required for CRM create benchmarks.")

        unique_suffix = uuid.uuid4().hex[:8]
        payload = {
            "company_name": f"Locust Bench Co {unique_suffix}",
            "contact_name": f"Load Tester {unique_suffix}",
            "contact_email": f"locust-{unique_suffix}@example.com",
        }
        if require_firm and self.config.firm_id:
            payload["firm"] = self.config.firm_id
        return payload

    @task(2)
    def list_leads(self) -> None:
        """List benchmark for CRM leads."""

        self.client.get(self.config.crm_leads_path, name="crm:leads:list")

    @task(1)
    def search_leads(self) -> None:
        """Search benchmark using query string filtering."""

        params = {"search": self.config.search_query}
        self.client.get(self.config.crm_leads_path, params=params, name="crm:leads:search")

    @task(1)
    def create_lead(self) -> None:
        """CRUD benchmark: create a lead (requires LOCUST_FIRM_ID)."""

        if not self.config.firm_id:
            return
        payload = self._lead_payload(require_firm=True)
        self.client.post(self.config.crm_leads_path, json=payload, name="crm:leads:create")

    @task(1)
    def update_lead(self) -> None:
        """CRUD benchmark: update a lead (requires LOCUST_LEAD_ID)."""

        if not self.config.lead_id:
            return
        payload = self._lead_payload(require_firm=False)
        self.client.patch(
            f"{self.config.crm_leads_path}{self.config.lead_id}/",
            json=payload,
            name="crm:leads:update",
        )

    @task(1)
    def delete_lead(self) -> None:
        """CRUD benchmark: delete a lead (requires LOCUST_LEAD_ID)."""

        if not self.config.lead_id:
            return
        self.client.delete(
            f"{self.config.crm_leads_path}{self.config.lead_id}/",
            name="crm:leads:delete",
        )
