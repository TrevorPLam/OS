"""
Tests for automation workflow executor, specifically date string parsing (T-009).
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.automation.executor import WorkflowExecutor
from modules.automation.models import (
    ContactFlowState,
    Workflow,
    WorkflowExecution,
    WorkflowNode,
)
from modules.crm.models import Contact
from modules.firm.models import Firm


@pytest.mark.django_db
class TestDateStringParsing:
    """Test date string parsing in automation executor (T-009)."""

    @pytest.fixture
    def setup_data(self):
        """Create test data."""
        user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        firm = Firm.objects.create(
            name="Test Firm", slug="test-firm", created_by=user
        )
        contact = Contact.objects.create(
            firm=firm,
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        workflow = Workflow.objects.create(
            firm=firm,
            name="Test Workflow",
            trigger_type="manual",
            created_by=user,
        )
        wait_node = WorkflowNode.objects.create(
            workflow=workflow,
            node_type="wait",
            name="Wait Node",
            position_x=0,
            position_y=0,
        )
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            contact=contact,
            firm=firm,
            status="active",
            triggered_by=user,
        )
        flow_state = ContactFlowState.objects.create(
            execution=execution,
            node=wait_node,
            status="pending",
        )

        return {
            "user": user,
            "firm": firm,
            "contact": contact,
            "workflow": workflow,
            "wait_node": wait_node,
            "execution": execution,
            "flow_state": flow_state,
        }

    def test_parse_iso8601_datetime_with_timezone(self, setup_data):
        """Test parsing ISO 8601 datetime string with timezone."""
        wait_node = setup_data["wait_node"]
        flow_state = setup_data["flow_state"]
        execution = setup_data["execution"]

        # Set configuration with ISO 8601 datetime string
        wait_node.config = {
            "wait_type": "until_date",
            "wait_until_date": "2026-06-15T14:30:00+00:00",
        }
        wait_node.save()

        executor = WorkflowExecutor(execution)
        result = executor._execute_wait(wait_node, flow_state)

        assert result["status"] == "wait"
        assert "wait_until" in result
        assert isinstance(result["wait_until"], datetime)
        # Verify it's timezone-aware
        assert result["wait_until"].tzinfo is not None

    def test_parse_iso8601_datetime_without_timezone(self, setup_data):
        """Test parsing ISO 8601 datetime string without timezone."""
        wait_node = setup_data["wait_node"]
        flow_state = setup_data["flow_state"]
        execution = setup_data["execution"]

        wait_node.config = {
            "wait_type": "until_date",
            "wait_until_date": "2026-06-15T14:30:00",
        }
        wait_node.save()

        executor = WorkflowExecutor(execution)
        result = executor._execute_wait(wait_node, flow_state)

        assert result["status"] == "wait"
        assert "wait_until" in result
        assert isinstance(result["wait_until"], datetime)
        # Should be made timezone-aware
        assert result["wait_until"].tzinfo is not None

    def test_parse_date_only_string(self, setup_data):
        """Test parsing date-only string (no time component)."""
        wait_node = setup_data["wait_node"]
        flow_state = setup_data["flow_state"]
        execution = setup_data["execution"]

        wait_node.config = {
            "wait_type": "until_date",
            "wait_until_date": "2026-06-15",
        }
        wait_node.save()

        executor = WorkflowExecutor(execution)
        result = executor._execute_wait(wait_node, flow_state)

        assert result["status"] == "wait"
        assert "wait_until" in result
        assert isinstance(result["wait_until"], datetime)
        # Should be converted to datetime at start of day
        assert result["wait_until"].hour == 0
        assert result["wait_until"].minute == 0
        assert result["wait_until"].second == 0
        # Should be timezone-aware
        assert result["wait_until"].tzinfo is not None

    def test_parse_invalid_date_format(self, setup_data):
        """Test handling of invalid date format."""
        wait_node = setup_data["wait_node"]
        flow_state = setup_data["flow_state"]
        execution = setup_data["execution"]

        wait_node.config = {
            "wait_type": "until_date",
            "wait_until_date": "invalid-date-string",
        }
        wait_node.save()

        executor = WorkflowExecutor(execution)
        result = executor._execute_wait(wait_node, flow_state)

        assert result["status"] == "failed"
        assert "error" in result
        assert "Invalid date format" in result["error"]
        
        # Verify flow state was updated
        flow_state.refresh_from_db()
        assert flow_state.status == "failed"
        assert flow_state.error_message is not None

    def test_parse_datetime_already_parsed(self, setup_data):
        """Test handling when datetime object is already provided."""
        wait_node = setup_data["wait_node"]
        flow_state = setup_data["flow_state"]
        execution = setup_data["execution"]

        # Provide an actual datetime object instead of string
        future_date = timezone.now() + timedelta(days=7)
        wait_node.config = {
            "wait_type": "until_date",
            "wait_until_date": future_date,
        }
        wait_node.save()

        executor = WorkflowExecutor(execution)
        result = executor._execute_wait(wait_node, flow_state)

        assert result["status"] == "wait"
        assert "wait_until" in result
        assert result["wait_until"] == future_date

    def test_parse_various_iso8601_formats(self, setup_data):
        """Test parsing various valid ISO 8601 formats."""
        wait_node = setup_data["wait_node"]
        flow_state = setup_data["flow_state"]
        execution = setup_data["execution"]

        test_formats = [
            "2026-06-15T14:30:00Z",  # UTC with Z
            "2026-06-15T14:30:00+05:30",  # With timezone offset
            "2026-06-15T14:30:00.123456+00:00",  # With microseconds
            "2026-06-15 14:30:00",  # Space separator
        ]

        for date_string in test_formats:
            wait_node.config = {
                "wait_type": "until_date",
                "wait_until_date": date_string,
            }
            wait_node.save()

            # Create a new flow state for each test
            flow_state = ContactFlowState.objects.create(
                execution=execution,
                node=wait_node,
                status="pending",
            )

            executor = WorkflowExecutor(execution)
            result = executor._execute_wait(wait_node, flow_state)

            assert result["status"] == "wait", f"Failed for format: {date_string}"
            assert "wait_until" in result
            assert isinstance(result["wait_until"], datetime)
            assert result["wait_until"].tzinfo is not None

    def test_parse_with_different_timezones(self, setup_data):
        """Test parsing dates with different timezone offsets."""
        wait_node = setup_data["wait_node"]
        flow_state = setup_data["flow_state"]
        execution = setup_data["execution"]

        # UTC
        wait_node.config = {
            "wait_type": "until_date",
            "wait_until_date": "2026-06-15T12:00:00+00:00",
        }
        wait_node.save()

        executor = WorkflowExecutor(execution)
        result_utc = executor._execute_wait(wait_node, flow_state)

        # Create new flow state
        flow_state = ContactFlowState.objects.create(
            execution=execution,
            node=wait_node,
            status="pending",
        )

        # EST (UTC-5)
        wait_node.config = {
            "wait_type": "until_date",
            "wait_until_date": "2026-06-15T07:00:00-05:00",
        }
        wait_node.save()

        result_est = executor._execute_wait(wait_node, flow_state)

        # Both should represent the same point in time
        assert result_utc["status"] == "wait"
        assert result_est["status"] == "wait"
        # When converted to UTC, they should be equal
        utc_time = result_utc["wait_until"].astimezone(timezone.utc)
        est_time = result_est["wait_until"].astimezone(timezone.utc)
        assert utc_time == est_time

    def test_error_handling_for_none_value(self, setup_data):
        """Test handling when wait_until_date is None."""
        wait_node = setup_data["wait_node"]
        flow_state = setup_data["flow_state"]
        execution = setup_data["execution"]

        wait_node.config = {
            "wait_type": "until_date",
            "wait_until_date": None,
        }
        wait_node.save()

        executor = WorkflowExecutor(execution)
        result = executor._execute_wait(wait_node, flow_state)

        # Should handle None gracefully
        assert result["status"] == "wait"
        assert result["wait_until"] is None
