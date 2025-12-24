"""
Tests for Assets module serializers.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from modules.assets.models import Asset, MaintenanceLog
from api.assets.serializers import AssetSerializer, MaintenanceLogSerializer


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(username='testuser', password='testpass123')


@pytest.fixture
def asset(db, user):
    """Create test asset."""
    return Asset.objects.create(
        asset_tag='ASSET-001',
        name='MacBook Pro',
        category='computer',
        status='active',
        assigned_to=user,
        purchase_price=Decimal('2500.00'),
        purchase_date=date.today() - timedelta(days=365),
        useful_life_years=3
    )


@pytest.mark.unit
@pytest.mark.django_db
class TestAssetSerializer:
    """Test AssetSerializer."""

    def test_valid_asset_data(self, user):
        """Test serializer accepts valid asset data."""
        data = {
            'asset_tag': 'LAPTOP-001',
            'name': 'Dell XPS 15',
            'category': 'computer',
            'status': 'active',
            'assigned_to': user.id,
            'purchase_price': '1800.00',
            'purchase_date': date.today().isoformat(),
            'useful_life_years': 3
        }
        serializer = AssetSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_asset_tag_uniqueness(self, asset):
        """Test asset tag must be unique."""
        data = {
            'asset_tag': asset.asset_tag,  # Duplicate
            'name': 'Another Asset',
            'category': 'computer',
            'status': 'active',
            'purchase_price': '1000.00',
            'purchase_date': date.today().isoformat()
        }
        serializer = AssetSerializer(data=data)
        assert not serializer.is_valid()

    def test_assigned_to_name_read_only(self, asset):
        """Test assigned_to_name is read-only field."""
        serializer = AssetSerializer(asset)
        assert 'assigned_to_name' in serializer.data
        assert serializer.data['assigned_to_name'] == asset.assigned_to.username

    def test_depreciation_fields(self, user):
        """Test asset includes depreciation fields."""
        data = {
            'asset_tag': 'ASSET-DEP',
            'name': 'Test Asset',
            'category': 'computer',
            'status': 'active',
            'purchase_price': '3000.00',
            'purchase_date': date.today().isoformat(),
            'useful_life_years': 5,
            'salvage_value': '500.00'
        }
        serializer = AssetSerializer(data=data)
        assert serializer.is_valid()
        asset = serializer.save()
        assert asset.salvage_value == Decimal('500.00')
        assert asset.useful_life_years == 5


@pytest.mark.unit
@pytest.mark.django_db
class TestMaintenanceLogSerializer:
    """Test MaintenanceLogSerializer."""

    def test_valid_maintenance_log_data(self, asset, user):
        """Test serializer accepts valid maintenance log data."""
        data = {
            'asset': asset.id,
            'maintenance_type': 'repair',
            'status': 'scheduled',
            'description': 'Replace keyboard',
            'scheduled_date': date.today().isoformat(),
            'performed_by': 'Tech Support',
            'cost': '150.00',
            'created_by': user.id
        }
        serializer = MaintenanceLogSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_maintenance_log_read_only_fields(self, asset, user):
        """Test maintenance log includes read-only asset info."""
        log = MaintenanceLog.objects.create(
            asset=asset,
            maintenance_type='preventive',
            status='completed',
            description='Regular maintenance',
            scheduled_date=date.today(),
            completed_date=date.today(),
            performed_by='IT Team',
            cost=Decimal('100.00'),
            created_by=user
        )
        serializer = MaintenanceLogSerializer(log)
        assert 'asset_tag' in serializer.data
        assert serializer.data['asset_tag'] == asset.asset_tag
        assert 'asset_name' in serializer.data
        assert serializer.data['asset_name'] == asset.name


@pytest.mark.integration
@pytest.mark.django_db
class TestAssetWorkflow:
    """Test asset management workflow."""

    def test_asset_lifecycle(self, user):
        """Test complete asset lifecycle from purchase to disposal."""
        # Create new asset
        asset = Asset.objects.create(
            asset_tag='LIFECYCLE-001',
            name='Test Equipment',
            category='computer',
            status='active',
            assigned_to=user,
            purchase_price=Decimal('2000.00'),
            purchase_date=date.today()
        )

        # Mark as in repair
        data = {'status': 'in_repair'}
        serializer = AssetSerializer(asset, data=data, partial=True)
        assert serializer.is_valid()
        asset = serializer.save()
        assert asset.status == 'in_repair'

        # Return to active
        data = {'status': 'active'}
        serializer = AssetSerializer(asset, data=data, partial=True)
        assert serializer.is_valid()
        asset = serializer.save()
        assert asset.status == 'active'

        # Retire asset
        data = {'status': 'retired', 'assigned_to': None}
        serializer = AssetSerializer(asset, data=data, partial=True)
        assert serializer.is_valid()
        asset = serializer.save()
        assert asset.status == 'retired'
        assert asset.assigned_to is None

    def test_maintenance_workflow(self, asset, user):
        """Test maintenance scheduling and completion workflow."""
        # Schedule maintenance
        log = MaintenanceLog.objects.create(
            asset=asset,
            maintenance_type='preventive',
            status='scheduled',
            description='Annual checkup',
            scheduled_date=date.today() + timedelta(days=7),
            performed_by='IT Team',
            cost=Decimal('200.00'),
            created_by=user
        )

        # Mark as in progress
        data = {'status': 'in_progress'}
        serializer = MaintenanceLogSerializer(log, data=data, partial=True)
        assert serializer.is_valid()
        log = serializer.save()
        assert log.status == 'in_progress'

        # Complete maintenance
        data = {
            'status': 'completed',
            'completed_date': date.today().isoformat()
        }
        serializer = MaintenanceLogSerializer(log, data=data, partial=True)
        assert serializer.is_valid()
        log = serializer.save()
        assert log.status == 'completed'
        assert log.completed_date == date.today()
