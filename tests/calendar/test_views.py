"""Tests for calendar appointment type view helpers."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from modules.calendar.models import AppointmentType
from modules.calendar.serializers import AppointmentTypeSerializer
from modules.calendar.views import AppointmentTypeViewSet
from modules.firm.models import Firm
from tests.utils.query_budget import assert_max_queries

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="staffer", email="staffer@example.com", password="pass1234")


@pytest.fixture
def host_user(db):
    return User.objects.create_user(username="hoster", email="hoster@example.com", password="pass1234")


def create_appointment_type(firm, name, required_hosts, optional_hosts, round_robin_pool):
    appointment_type = AppointmentType.objects.create(
        firm=firm,
        name=name,
        duration_minutes=30,
        location_mode="video",
        status="active",
    )
    appointment_type.required_hosts.set(required_hosts)
    appointment_type.optional_hosts.set(optional_hosts)
    appointment_type.round_robin_pool.set(round_robin_pool)
    return appointment_type


@pytest.mark.django_db
def test_list_appointment_types_prefetches_hosts(firm, user, host_user):
    """Ensure list serialization stays within a stable query budget with many hosts."""
    for index in range(5):
        create_appointment_type(
            firm=firm,
            name=f"Type {index}",
            required_hosts=[user],
            optional_hosts=[host_user],
            round_robin_pool=[user, host_user],
        )

    viewset = AppointmentTypeViewSet()
    request = APIRequestFactory().get("/api/v1/calendar/appointment-types/")
    request.user = user
    request.firm = firm
    viewset.request = request

    with assert_max_queries(6):
        data = AppointmentTypeSerializer(viewset.get_queryset(), many=True).data

    assert len(data) == 5
    assert data[0]["required_hosts_display"][0]["email"] == "staffer@example.com"


@pytest.mark.django_db
def test_list_appointment_types_empty_returns_empty_list(firm, user):
    """Ensure empty appointment type lists serialize cleanly."""
    viewset = AppointmentTypeViewSet()
    request = APIRequestFactory().get("/api/v1/calendar/appointment-types/")
    request.user = user
    request.firm = firm
    viewset.request = request

    with assert_max_queries(2):
        data = AppointmentTypeSerializer(viewset.get_queryset(), many=True).data

    assert data == []


@pytest.mark.django_db
def test_group_event_requires_max_attendees(firm):
    """Ensure group events enforce max attendee validation."""
    serializer = AppointmentTypeSerializer(
        data={
            "name": "Group Event",
            "description": "Test group event",
            "event_category": "group",
            "duration_minutes": 45,
            "location_mode": "video",
            "status": "active",
        }
    )

    assert serializer.is_valid() is False
    assert "max_attendees" in serializer.errors
