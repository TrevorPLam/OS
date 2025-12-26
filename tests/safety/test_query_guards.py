"""
Tier 1 Safety Tests - API Query Guardrails

Validates pagination limits and tenant-scoped list filtering.
"""
from datetime import date, timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from modules.crm.models import Lead
from modules.crm.views import LeadViewSet
from modules.clients.models import Client
from modules.firm.models import Firm, FirmMembership
from modules.projects.models import Project, Task
from api.projects.views import TaskViewSet


User = get_user_model()


@pytest.fixture
def firm_users():
    firm_a = Firm.objects.create(name="Firm A", slug="firm-a", status="active")
    firm_b = Firm.objects.create(name="Firm B", slug="firm-b", status="active")

    user_a = User.objects.create_user(
        username="user_a",
        email="user_a@example.com",
        password="testpass123"
    )
    user_b = User.objects.create_user(
        username="user_b",
        email="user_b@example.com",
        password="testpass123"
    )

    FirmMembership.objects.create(firm=firm_a, user=user_a, role="admin")
    FirmMembership.objects.create(firm=firm_b, user=user_b, role="admin")

    return {
        "firm_a": firm_a,
        "firm_b": firm_b,
        "user_a": user_a,
        "user_b": user_b,
    }


@pytest.mark.django_db
def test_pagination_guard_rejects_large_page_size(firm_users):
    lead = Lead.objects.create(
        firm=firm_users["firm_a"],
        company_name="Acme Corp",
        contact_name="Pat Smith",
        contact_email="pat@example.com",
        source="website"
    )

    factory = APIRequestFactory()
    request = factory.get(
        "/api/crm/leads/",
        {"page_size": settings.API_PAGINATION_MAX_PAGE_SIZE + 1}
    )
    request.firm = firm_users["firm_a"]
    force_authenticate(request, user=firm_users["user_a"])

    view = LeadViewSet.as_view({"get": "list"})
    response = view(request)

    assert response.status_code == 400
    assert "page_size" in response.data["error"]["details"]


@pytest.mark.django_db
def test_task_list_is_firm_scoped(firm_users):
    client_a = Client.objects.create(
        firm=firm_users["firm_a"],
        company_name="Client A",
        primary_contact_name="Alex A",
        primary_contact_email="alex.a@example.com"
    )
    client_b = Client.objects.create(
        firm=firm_users["firm_b"],
        company_name="Client B",
        primary_contact_name="Blair B",
        primary_contact_email="blair.b@example.com"
    )

    today = date.today()
    project_a = Project.objects.create(
        firm=firm_users["firm_a"],
        client=client_a,
        project_code="PROJ-A",
        name="Project A",
        status="planning",
        billing_type="time_and_materials",
        start_date=today,
        end_date=today + timedelta(days=30),
    )
    project_b = Project.objects.create(
        firm=firm_users["firm_b"],
        client=client_b,
        project_code="PROJ-B",
        name="Project B",
        status="planning",
        billing_type="time_and_materials",
        start_date=today,
        end_date=today + timedelta(days=30),
    )

    task_a = Task.objects.create(project=project_a, title="Task A")
    task_b = Task.objects.create(project=project_b, title="Task B")

    factory = APIRequestFactory()
    request = factory.get("/api/projects/tasks/")
    request.firm = firm_users["firm_a"]
    force_authenticate(request, user=firm_users["user_a"])

    view = TaskViewSet.as_view({"get": "list"})
    response = view(request)

    assert response.status_code == 200
    result_ids = {item["id"] for item in response.data["results"]}
    assert task_a.id in result_ids
    assert task_b.id not in result_ids
