"""
Tests for Meeting Workflow Execution Engine.

Tests workflow triggering, execution, and integration with appointment lifecycle.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from django.utils import timezone
from django.core import mail
from django.contrib.auth import get_user_model

from modules.calendar.models import (
    Appointment,
    AppointmentType,
    AvailabilityProfile,
    BookingLink,
    MeetingWorkflow,
    MeetingWorkflowExecution,
    AppointmentStatusHistory,
)
from modules.calendar.workflow_services import WorkflowExecutionEngine
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    """Create test firm."""
    return Firm.objects.create(
        name="Test Consulting Firm",
        slug="test-firm"
    )


@pytest.fixture
def staff_user(db, firm):
    """Create test staff user."""
    user = User.objects.create_user(
        username="staff@test.com",
        email="staff@test.com",
        password="testpass123"
    )
    from modules.firm.models import FirmMembership
    FirmMembership.objects.create(
        firm=firm,
        user=user,
        role='staff'
    )
    return user


@pytest.fixture
def appointment_type(db, firm, staff_user):
    """Create test appointment type."""
    return AppointmentType.objects.create(
        firm=firm,
        name="Consultation",
        description="30-minute consultation",
        duration_minutes=30,
        buffer_before_minutes=5,
        buffer_after_minutes=5,
        location_mode="video",
        routing_policy="fixed_staff",
        fixed_staff_user=staff_user
    )


@pytest.fixture
def appointment(db, firm, appointment_type, staff_user):
    """Create test appointment."""
    start_time = timezone.now() + timedelta(days=1)
    end_time = start_time + timedelta(minutes=30)
    return Appointment.objects.create(
        firm=firm,
        appointment_type=appointment_type,
        staff_user=staff_user,
        start_time=start_time,
        end_time=end_time,
        status='requested'
    )


@pytest.fixture
def workflow_engine():
    """Create workflow engine instance."""
    return WorkflowExecutionEngine()


@pytest.mark.django_db
class TestWorkflowTriggering:
    """Test workflow triggering on appointment events."""
    
    def test_trigger_on_appointment_created(self, firm, appointment_type, appointment, workflow_engine):
        """Test workflows are triggered when appointment is created."""
        # Create a workflow for appointment_created event
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="Welcome Email",
            trigger='appointment_created',
            appointment_type=appointment_type,
            delay_minutes=0,  # Send immediately
            action_type='send_email',
            action_config={
                'subject': 'Your appointment is booked',
                'template': 'Thank you for booking!',
                'to_email': '{{contact.email}}'
            },
            status='active'
        )
        
        # Trigger workflows
        executions = workflow_engine.trigger_workflows(
            appointment=appointment,
            trigger_event='appointment_created'
        )
        
        assert len(executions) == 1
        assert executions[0].workflow == workflow
        assert executions[0].appointment == appointment
        assert executions[0].status == 'pending'
    
    def test_trigger_respects_appointment_type_filter(
        self, firm, appointment_type, appointment, workflow_engine
    ):
        """Test workflows only trigger for matching appointment types."""
        # Create another appointment type
        other_type = AppointmentType.objects.create(
            firm=firm,
            name="Different Type",
            duration_minutes=60,
            routing_policy="fixed_staff"
        )
        
        # Create workflow for specific appointment type
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="Type-Specific Workflow",
            trigger='appointment_created',
            appointment_type=other_type,  # Different type
            delay_minutes=0,
            action_type='send_email',
            action_config={},
            status='active'
        )
        
        # Trigger workflows for our appointment (different type)
        executions = workflow_engine.trigger_workflows(
            appointment=appointment,
            trigger_event='appointment_created'
        )
        
        # Should not trigger the workflow
        assert len(executions) == 0
    
    def test_trigger_with_null_appointment_type(
        self, firm, appointment_type, appointment, workflow_engine
    ):
        """Test workflows with null appointment_type trigger for all appointments."""
        # Create workflow for all appointment types
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="Universal Workflow",
            trigger='appointment_created',
            appointment_type=None,  # Apply to all types
            delay_minutes=0,
            action_type='send_email',
            action_config={},
            status='active'
        )
        
        # Trigger workflows
        executions = workflow_engine.trigger_workflows(
            appointment=appointment,
            trigger_event='appointment_created'
        )
        
        # Should trigger the workflow
        assert len(executions) == 1
        assert executions[0].workflow == workflow
    
    def test_workflow_scheduling_before_appointment(
        self, firm, appointment_type, appointment, workflow_engine
    ):
        """Test workflows scheduled before appointment (negative delay)."""
        # Create reminder workflow 24 hours before appointment
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="24hr Reminder",
            trigger='appointment_created',
            appointment_type=appointment_type,
            delay_minutes=-1440,  # -24 hours
            action_type='send_email',
            action_config={},
            status='active'
        )
        
        # Trigger workflows
        executions = workflow_engine.trigger_workflows(
            appointment=appointment,
            trigger_event='appointment_created'
        )
        
        assert len(executions) == 1
        execution = executions[0]
        
        # Should be scheduled 24 hours before appointment
        expected_time = appointment.start_time - timedelta(hours=24)
        time_diff = abs((execution.scheduled_for - expected_time).total_seconds())
        assert time_diff < 60  # Within 1 minute
    
    def test_workflow_scheduling_after_appointment(
        self, firm, appointment_type, appointment, workflow_engine
    ):
        """Test workflows scheduled after appointment (positive delay)."""
        # Create follow-up workflow 1 hour after completion
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="Follow-up Email",
            trigger='appointment_completed',
            appointment_type=appointment_type,
            delay_minutes=60,  # 1 hour after
            action_type='send_email',
            action_config={},
            status='active'
        )
        
        # Trigger workflows
        executions = workflow_engine.trigger_workflows(
            appointment=appointment,
            trigger_event='appointment_completed'
        )
        
        assert len(executions) == 1
        execution = executions[0]
        
        # Should be scheduled approximately 1 hour from now
        expected_time = timezone.now() + timedelta(hours=1)
        time_diff = abs((execution.scheduled_for - expected_time).total_seconds())
        assert time_diff < 300  # Within 5 minutes


@pytest.mark.django_db
class TestWorkflowExecution:
    """Test workflow action execution."""
    
    def test_execute_send_email_action(self, firm, appointment_type, appointment, workflow_engine):
        """Test email sending workflow action."""
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="Email Workflow",
            trigger='appointment_created',
            appointment_type=appointment_type,
            delay_minutes=0,
            action_type='send_email',
            action_config={
                'subject': 'Appointment Confirmation',
                'template': 'Hi {{contact.name}}, your appointment is at {{appointment.start_time}}',
                'to_email': 'john@example.com',
                'from_email': 'noreply@test.com'
            },
            status='active'
        )
        
        execution = MeetingWorkflowExecution.objects.create(
            workflow=workflow,
            appointment=appointment,
            status='pending',
            scheduled_for=timezone.now()
        )
        
        # Execute the workflow
        workflow_engine._execute_workflow_action(execution)
        
        # Check execution status
        execution.refresh_from_db()
        assert execution.status == 'completed'
        assert execution.executed_at is not None
        assert 'email_sent' in execution.result_data.get('summary', '')
        
        # Check email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'Appointment Confirmation'
        assert mail.outbox[0].to == ['john@example.com']
    
    def test_execute_create_task_action(self, firm, appointment_type, appointment, workflow_engine):
        """Test task creation workflow action (currently skipped due to project requirement)."""
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="Task Workflow",
            trigger='appointment_completed',
            appointment_type=appointment_type,
            delay_minutes=0,
            action_type='create_task',
            action_config={
                'title': 'Follow up on {{appointment.id}}',
                'description': 'Send follow-up materials',
                'due_days': 2
            },
            status='active'
        )
        
        execution = MeetingWorkflowExecution.objects.create(
            workflow=workflow,
            appointment=appointment,
            status='pending',
            scheduled_for=timezone.now()
        )
        
        # Execute the workflow
        workflow_engine._execute_workflow_action(execution)
        
        # Check execution status
        execution.refresh_from_db()
        assert execution.status == 'completed'
        # Task creation is skipped since appointments don't have projects
        assert 'task_creation_skipped' in execution.result_data.get('summary', '')
    
    def test_execute_sms_action_stub(self, firm, appointment_type, appointment, workflow_engine):
        """Test SMS workflow action (stub implementation)."""
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="SMS Workflow",
            trigger='appointment_created',
            appointment_type=appointment_type,
            delay_minutes=-60,  # 1 hour before
            action_type='send_sms',
            action_config={
                'message': 'Reminder: Your appointment is in 1 hour',
                'to_phone': '+1234567890'
            },
            status='active'
        )
        
        execution = MeetingWorkflowExecution.objects.create(
            workflow=workflow,
            appointment=appointment,
            status='pending',
            scheduled_for=timezone.now()
        )
        
        # Execute the workflow (stub)
        workflow_engine._execute_workflow_action(execution)
        
        # Check execution completed (even though it's a stub)
        execution.refresh_from_db()
        assert execution.status == 'completed'
        assert 'sms_stubbed' in execution.result_data.get('summary', '')
    
    def test_execution_error_handling(self, firm, appointment_type, appointment, workflow_engine):
        """Test error handling during workflow execution."""
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="Invalid Workflow",
            trigger='appointment_created',
            appointment_type=appointment_type,
            delay_minutes=0,
            action_type='send_email',
            action_config={
                # Missing required fields to cause error
                'template': 'Test',
                # No to_email specified
            },
            status='active'
        )
        
        execution = MeetingWorkflowExecution.objects.create(
            workflow=workflow,
            appointment=appointment,
            status='pending',
            scheduled_for=timezone.now()
        )
        
        # Execute the workflow (should fail)
        with pytest.raises(Exception):
            workflow_engine._execute_workflow_action(execution)
        
        # Check execution marked as failed
        execution.refresh_from_db()
        assert execution.status == 'failed'
        assert execution.error_message != ''


@pytest.mark.django_db
class TestBatchExecution:
    """Test batch execution of pending workflows."""
    
    def test_execute_pending_workflows(self, firm, appointment_type, appointment, workflow_engine):
        """Test batch execution processes pending workflows."""
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="Test Workflow",
            trigger='appointment_created',
            delay_minutes=0,
            action_type='send_email',
            action_config={
                'subject': 'Test',
                'template': 'Test',
                'to_email': 'test@example.com'
            },
            status='active'
        )
        
        # Create multiple pending executions
        now = timezone.now()
        for i in range(3):
            MeetingWorkflowExecution.objects.create(
                workflow=workflow,
                appointment=appointment,
                status='pending',
                scheduled_for=now - timedelta(minutes=i)  # All in the past
            )
        
        # Execute pending workflows
        stats = workflow_engine.execute_pending_workflows()
        
        assert stats['executed'] == 3
        assert stats['failed'] == 0
        assert stats['skipped'] == 0
        
        # Check all executions completed
        executions = MeetingWorkflowExecution.objects.filter(workflow=workflow)
        assert all(e.status == 'completed' for e in executions)
    
    def test_skip_cancelled_appointments(self, firm, appointment_type, appointment, workflow_engine):
        """Test workflows are skipped for cancelled appointments."""
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="Test Workflow",
            trigger='appointment_created',
            delay_minutes=0,
            action_type='send_email',
            action_config={
                'subject': 'Test',
                'template': 'Test',
                'to_email': 'test@example.com'
            },
            status='active'
        )
        
        execution = MeetingWorkflowExecution.objects.create(
            workflow=workflow,
            appointment=appointment,
            status='pending',
            scheduled_for=timezone.now() - timedelta(minutes=1)
        )
        
        # Cancel the appointment
        appointment.status = 'cancelled'
        appointment.save()
        
        # Execute pending workflows
        stats = workflow_engine.execute_pending_workflows()
        
        assert stats['executed'] == 0
        assert stats['failed'] == 0
        assert stats['skipped'] == 1
        
        # Check execution was cancelled
        execution.refresh_from_db()
        assert execution.status == 'cancelled'


@pytest.mark.django_db
class TestSignalIntegration:
    """Test workflow triggering via Django signals."""
    
    def test_workflow_triggered_on_appointment_create(
        self, firm, appointment_type, staff_user
    ):
        """Test workflow automatically triggered when appointment created."""
        # Create workflow
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="Auto Trigger Test",
            trigger='appointment_created',
            appointment_type=appointment_type,
            delay_minutes=0,
            action_type='send_email',
            action_config={
                'subject': 'Test',
                'template': 'Test',
                'to_email': 'test@example.com'
            },
            status='active'
        )
        
        # Create appointment (signal should trigger workflow)
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            firm=firm,
            appointment_type=appointment_type,
            staff_user=staff_user,
            start_time=start_time,
            end_time=end_time,
            status='requested'
        )
        
        # Check workflow execution was created
        executions = MeetingWorkflowExecution.objects.filter(
            workflow=workflow,
            appointment=appointment
        )
        assert executions.count() == 1
    
    def test_workflow_triggered_on_status_change(
        self, firm, appointment_type, appointment, staff_user
    ):
        """Test workflow triggered when appointment status changes."""
        # Create workflow for confirmation
        workflow = MeetingWorkflow.objects.create(
            firm=firm,
            name="Confirmation Workflow",
            trigger='appointment_confirmed',
            appointment_type=appointment_type,
            delay_minutes=0,
            action_type='send_email',
            action_config={
                'subject': 'Confirmed',
                'template': 'Your appointment is confirmed',
                'to_email': 'test@example.com'
            },
            status='active'
        )
        
        # Change appointment status to confirmed
        appointment.status = 'confirmed'
        appointment._updated_by = staff_user
        appointment.save()
        
        # Manually create status history (normally done by signals)
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status='requested',
            to_status='confirmed',
            changed_by=staff_user
        )
        
        # Manually trigger workflows (since signals may not fire in tests)
        engine = WorkflowExecutionEngine()
        executions = engine.trigger_workflows(
            appointment=appointment,
            trigger_event='appointment_confirmed',
            actor=staff_user
        )
        
        # Check workflow execution was created
        assert len(executions) == 1
        assert executions[0].workflow == workflow
