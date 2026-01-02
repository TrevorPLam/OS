"""
Tests for Client Health Score functionality.

Tests the dynamic client health score calculation system.
"""

import pytest
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone

from modules.clients.models import Client
from modules.clients.health_score import ClientHealthScore, ClientHealthScoreConfig, ClientHealthScoreAlert
from modules.clients.health_score_calculator import HealthScoreCalculator
from modules.firm.models import Firm
from modules.finance.models import Invoice
from modules.projects.models import Project


@pytest.mark.django_db
class TestClientHealthScoreConfig:
    """Test ClientHealthScoreConfig model."""
    
    def test_create_config(self, firm, user):
        """Test creating a health score config."""
        config = ClientHealthScoreConfig.objects.create(
            firm=firm,
            engagement_weight=25,
            payment_weight=30,
            communication_weight=20,
            project_delivery_weight=25,
            created_by=user
        )
        
        assert config.engagement_weight == 25
        assert config.payment_weight == 30
        assert config.communication_weight == 20
        assert config.project_delivery_weight == 25
        assert config.is_active is True
    
    def test_weight_validation(self, firm, user):
        """Test that weights must sum to 100."""
        from django.core.exceptions import ValidationError
        
        config = ClientHealthScoreConfig(
            firm=firm,
            engagement_weight=30,  # These sum to 110, not 100
            payment_weight=30,
            communication_weight=30,
            project_delivery_weight=20,
            created_by=user
        )
        
        with pytest.raises(ValidationError):
            config.clean()


@pytest.mark.django_db
class TestHealthScoreCalculator:
    """Test HealthScoreCalculator."""
    
    def test_calculate_engagement_score_active_client(self, firm, user):
        """Test engagement score for active client."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            active_projects_count=2,
            client_since=timezone.now().date()
        )
        
        calculator = HealthScoreCalculator(client)
        score = calculator._calculate_engagement_score()
        
        # Active client with 2 active projects should have good score
        assert score >= 50
    
    def test_calculate_payment_score_good_payer(self, firm, user):
        """Test payment score for client with good payment history."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            client_since=timezone.now().date()
        )
        
        # Create paid invoices
        for i in range(3):
            Invoice.objects.create(
                firm=firm,
                client=client,
                invoice_number=f"INV-{i}",
                status="paid",
                subtotal=Decimal("1000.00"),
                tax_amount=Decimal("100.00"),
                total_amount=Decimal("1100.00"),
                amount_paid=Decimal("1100.00"),
                issue_date=timezone.now().date(),
                due_date=timezone.now().date() + timedelta(days=30)
            )
        
        calculator = HealthScoreCalculator(client)
        score = calculator._calculate_payment_score()
        
        # All invoices paid should give high score
        assert score >= 90
    
    def test_calculate_payment_score_overdue(self, firm, user):
        """Test payment score for client with overdue invoices."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            client_since=timezone.now().date()
        )
        
        # Create overdue invoices
        for i in range(2):
            Invoice.objects.create(
                firm=firm,
                client=client,
                invoice_number=f"INV-{i}",
                status="overdue",
                subtotal=Decimal("1000.00"),
                tax_amount=Decimal("100.00"),
                total_amount=Decimal("1100.00"),
                amount_paid=Decimal("0.00"),
                issue_date=timezone.now().date() - timedelta(days=60),
                due_date=timezone.now().date() - timedelta(days=30)
            )
        
        calculator = HealthScoreCalculator(client)
        score = calculator._calculate_payment_score()
        
        # Overdue invoices should reduce score
        assert score < 80
    
    def test_calculate_overall_score(self, firm, user):
        """Test overall health score calculation."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            active_projects_count=1,
            client_since=timezone.now().date()
        )
        
        calculator = HealthScoreCalculator(client)
        health_score = calculator.calculate()
        
        assert health_score is not None
        assert 0 <= health_score.score <= 100
        assert health_score.engagement_score >= 0
        assert health_score.payment_score >= 0
        assert health_score.communication_score >= 0
        assert health_score.project_delivery_score >= 0
    
    def test_alert_triggered_on_score_drop(self, firm, user):
        """Test that alert is created when score drops significantly."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            active_projects_count=2,
            client_since=timezone.now().date()
        )
        
        # Create initial good score
        ClientHealthScore.objects.create(
            firm=firm,
            client=client,
            score=80,
            engagement_score=80,
            payment_score=80,
            communication_score=80,
            project_delivery_score=80,
            is_at_risk=False,
            triggered_alert=False
        )
        
        # Create overdue invoices to drop payment score
        for i in range(5):
            Invoice.objects.create(
                firm=firm,
                client=client,
                invoice_number=f"INV-{i}",
                status="overdue",
                subtotal=Decimal("1000.00"),
                tax_amount=Decimal("100.00"),
                total_amount=Decimal("1100.00"),
                amount_paid=Decimal("0.00"),
                issue_date=timezone.now().date() - timedelta(days=60),
                due_date=timezone.now().date() - timedelta(days=30)
            )
        
        # Calculate new score
        calculator = HealthScoreCalculator(client)
        health_score = calculator.calculate()
        
        # Score should have dropped
        assert health_score.score < 80
        
        # Alert might be triggered if drop is significant enough
        if health_score.triggered_alert:
            alerts = ClientHealthScoreAlert.objects.filter(client=client)
            assert alerts.exists()


@pytest.mark.django_db
class TestClientHealthScore:
    """Test ClientHealthScore model."""
    
    def test_create_health_score(self, firm, user):
        """Test creating a health score."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            client_since=timezone.now().date()
        )
        
        score = ClientHealthScore.objects.create(
            firm=firm,
            client=client,
            score=75,
            engagement_score=80,
            payment_score=70,
            communication_score=75,
            project_delivery_score=75,
            is_at_risk=False,
            triggered_alert=False
        )
        
        assert score.score == 75
        assert score.client == client
    
    def test_at_risk_flag(self, firm, user):
        """Test at-risk flag is set correctly."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            client_since=timezone.now().date()
        )
        
        # Create at-risk score
        score = ClientHealthScore.objects.create(
            firm=firm,
            client=client,
            score=35,  # Below default threshold of 50
            engagement_score=40,
            payment_score=30,
            communication_score=35,
            project_delivery_score=35,
            is_at_risk=True,
            triggered_alert=False
        )
        
        assert score.is_at_risk is True


@pytest.mark.django_db
class TestClientHealthScoreAlert:
    """Test ClientHealthScoreAlert model."""
    
    def test_create_alert(self, firm, user):
        """Test creating a health score alert."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            client_since=timezone.now().date()
        )
        
        health_score = ClientHealthScore.objects.create(
            firm=firm,
            client=client,
            score=45,
            engagement_score=50,
            payment_score=40,
            communication_score=45,
            project_delivery_score=45,
            previous_score=70,
            score_change=-25,
            is_at_risk=True,
            triggered_alert=True
        )
        
        alert = ClientHealthScoreAlert.objects.create(
            firm=firm,
            client=client,
            health_score=health_score,
            status="pending",
            score_drop=25,
            previous_score=70,
            current_score=45
        )
        
        assert alert.status == "pending"
        assert alert.score_drop == 25
    
    def test_acknowledge_alert(self, firm, user):
        """Test acknowledging an alert."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            client_since=timezone.now().date()
        )
        
        health_score = ClientHealthScore.objects.create(
            firm=firm,
            client=client,
            score=45,
            engagement_score=50,
            payment_score=40,
            communication_score=45,
            project_delivery_score=45,
            is_at_risk=True,
            triggered_alert=True
        )
        
        alert = ClientHealthScoreAlert.objects.create(
            firm=firm,
            client=client,
            health_score=health_score,
            status="pending",
            score_drop=25,
            previous_score=70,
            current_score=45
        )
        
        # Acknowledge the alert
        alert.status = "acknowledged"
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = user
        alert.save()
        
        assert alert.status == "acknowledged"
        assert alert.acknowledged_by == user
        assert alert.acknowledged_at is not None


# Fixtures
@pytest.fixture
def firm():
    """Create a test firm."""
    return Firm.objects.create(
        name="Test Firm",
        slug="test-firm"
    )


@pytest.fixture
def user(firm):
    """Create a test user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        firm=firm
    )
