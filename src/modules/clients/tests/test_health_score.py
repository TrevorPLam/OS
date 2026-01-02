"""
Tests for Client Health Score functionality.

Tests the dynamic client health score calculation system.
"""

import pytest
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone

from modules.clients.models import Client, ClientHealthScore
from modules.clients.health_score_calculator import HealthScoreCalculator
from modules.firm.models import Firm
from modules.finance.models import Invoice
from modules.projects.models import Project


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
            client=client,
            score=75,
            engagement_score=80,
            payment_score=70,
            communication_score=75,
            delivery_score=75,
        )
        
        assert score.score == 75
        assert score.client == client
    
    def test_calculate_score_method(self, firm, user):
        """Test calculate_score method."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            client_since=timezone.now().date()
        )
        
        health_score = ClientHealthScore.objects.create(
            client=client,
            engagement_score=80,
            payment_score=90,
            communication_score=70,
            delivery_score=85,
        )
        
        calculated_score = health_score.calculate_score()
        assert 0 <= calculated_score <= 100
    
    def test_update_trend_method(self, firm, user):
        """Test update_trend method."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            client_since=timezone.now().date()
        )
        
        health_score = ClientHealthScore.objects.create(
            client=client,
            score=85,
            previous_score=70,
            engagement_score=85,
            payment_score=85,
            communication_score=85,
            delivery_score=85,
        )
        
        health_score.update_trend()
        assert health_score.score_trend in ["improving", "stable", "declining"]
    
    def test_check_at_risk_method(self, firm, user):
        """Test check_at_risk method."""
        client = Client.objects.create(
            firm=firm,
            company_name="Test Company",
            primary_contact_name="John Doe",
            primary_contact_email="john@test.com",
            status="active",
            client_since=timezone.now().date()
        )
        
        health_score = ClientHealthScore.objects.create(
            client=client,
            score=45,
            alert_threshold=60,
            engagement_score=45,
            payment_score=45,
            communication_score=45,
            delivery_score=45,
        )
        
        is_at_risk = health_score.check_at_risk()
        assert is_at_risk is True
        assert health_score.is_at_risk is True


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
        assert health_score.delivery_score >= 0


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
    from django.contrib.auth import get_user_model()
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        firm=firm
    )
