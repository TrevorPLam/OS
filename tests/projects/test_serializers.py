"""
Tests for Projects module serializers with comprehensive validation coverage.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from modules.crm.models import Client, Contract
from modules.projects.models import Project, Task, TimeEntry
from api.projects.serializers import ProjectSerializer, TaskSerializer, TimeEntrySerializer


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(username='testuser', password='testpass123')


@pytest.fixture
def client_obj(db, user):
    """Create test client."""
    return Client.objects.create(
        company_name='Test Company',
        primary_contact_name='John Doe',
        primary_contact_email='john@test.com',
        owner=user,
        status='active'
    )


@pytest.fixture
def contract(db, client_obj):
    """Create test contract."""
    return Contract.objects.create(
        client=client_obj,
        contract_number='CTR-001',
        title='Test Contract',
        contract_value=Decimal('50000.00'),
        status='active',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365)
    )


@pytest.fixture
def project(db, client_obj, contract, user):
    """Create test project."""
    return Project.objects.create(
        client=client_obj,
        contract=contract,
        project_manager=user,
        project_code='PRJ-001',
        name='Test Project',
        status='in_progress',
        billing_type='hourly',
        hourly_rate=Decimal('150.00'),
        start_date=date.today(),
        end_date=date.today() + timedelta(days=90)
    )


@pytest.mark.unit
@pytest.mark.django_db
class TestProjectSerializer:
    """Test ProjectSerializer validation logic."""

    def test_valid_project_data(self, client_obj, user):
        """Test serializer accepts valid project data."""
        data = {
            'client': client_obj.id,
            'project_manager': user.id,
            'project_code': 'PRJ-TEST',
            'name': 'Test Project',
            'status': 'in_progress',
            'billing_type': 'hourly',
            'hourly_rate': '150.00',
            'start_date': date.today().isoformat(),
            'end_date': (date.today() + timedelta(days=90)).isoformat()
        }
        serializer = ProjectSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_budget_validation_positive(self):
        """Test budget must be positive."""
        serializer = ProjectSerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_budget(Decimal('-100.00'))
        assert 'greater than 0' in str(exc_info.value)

    def test_hourly_rate_validation_positive(self):
        """Test hourly rate must be positive."""
        serializer = ProjectSerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_hourly_rate(Decimal('0.00'))
        assert 'greater than 0' in str(exc_info.value)

    def test_end_date_after_start_date(self, client_obj, user):
        """Test end date must be after start date."""
        data = {
            'client': client_obj.id,
            'project_manager': user.id,
            'project_code': 'PRJ-TEST',
            'name': 'Test Project',
            'start_date': date.today().isoformat(),
            'end_date': (date.today() - timedelta(days=1)).isoformat()
        }
        serializer = ProjectSerializer(data=data)
        assert not serializer.is_valid()
        assert 'end_date' in serializer.errors

    def test_contract_client_mismatch(self, client_obj, contract, user):
        """Test contract must belong to same client."""
        other_client = Client.objects.create(
            company_name='Other Company',
            primary_contact_email='other@test.com',
            owner=user,
            status='active'
        )
        data = {
            'client': other_client.id,
            'contract': contract.id,
            'project_manager': user.id,
            'project_code': 'PRJ-TEST',
            'name': 'Test Project',
        }
        serializer = ProjectSerializer(data=data)
        assert not serializer.is_valid()
        assert 'contract' in serializer.errors

    def test_actual_completion_date_validation(self, client_obj, user):
        """Test actual completion date cannot be before start date."""
        data = {
            'client': client_obj.id,
            'project_manager': user.id,
            'project_code': 'PRJ-TEST',
            'name': 'Test Project',
            'start_date': date.today().isoformat(),
            'actual_completion_date': (date.today() - timedelta(days=10)).isoformat()
        }
        serializer = ProjectSerializer(data=data)
        assert not serializer.is_valid()
        assert 'actual_completion_date' in serializer.errors


@pytest.mark.unit
@pytest.mark.django_db
class TestTaskSerializer:
    """Test TaskSerializer validation logic."""

    def test_valid_task_data(self, project, user):
        """Test serializer accepts valid task data."""
        data = {
            'project': project.id,
            'assigned_to': user.id,
            'title': 'Test Task',
            'description': 'Task description',
            'status': 'todo',
            'priority': 'medium',
            'estimated_hours': '8.0'
        }
        serializer = TaskSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_estimated_hours_positive(self):
        """Test estimated hours must be positive."""
        serializer = TaskSerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_estimated_hours(Decimal('-5.0'))
        assert 'greater than 0' in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.django_db
class TestTimeEntrySerializer:
    """Test TimeEntrySerializer validation logic."""

    def test_hours_validation_positive(self):
        """Test hours must be positive."""
        serializer = TimeEntrySerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_hours(Decimal('0.0'))
        assert 'greater than 0' in str(exc_info.value)

    def test_hours_validation_reasonable_max(self):
        """Test hours cannot exceed 24 in a day."""
        serializer = TimeEntrySerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_hours(Decimal('25.0'))
        assert '24 hours' in str(exc_info.value)

    def test_date_not_in_future(self, project, user):
        """Test time entry date cannot be in the future."""
        data = {
            'project': project.id,
            'user': user.id,
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'hours': '8.0',
            'description': 'Test entry'
        }
        serializer = TimeEntrySerializer(data=data)
        assert not serializer.is_valid()
        assert 'date' in serializer.errors


@pytest.mark.integration
@pytest.mark.django_db
class TestProjectWorkflow:
    """Test complete project workflow integration."""

    def test_project_completion_workflow(self, project):
        """Test marking project as completed sets actual_completion_date."""
        data = {
            'status': 'completed',
            'actual_completion_date': date.today().isoformat()
        }
        serializer = ProjectSerializer(project, data=data, partial=True)
        assert serializer.is_valid()
        updated_project = serializer.save()
        assert updated_project.status == 'completed'
        assert updated_project.actual_completion_date == date.today()
