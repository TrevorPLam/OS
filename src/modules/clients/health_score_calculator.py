"""
Client Health Score Calculator

Business logic for calculating client health scores based on multiple factors:
- Engagement: Activity levels, portal usage, responsiveness
- Payments: Invoice payment patterns, overdue amounts
- Communication: Message frequency, response times
- Project Delivery: On-time completion, client satisfaction
"""

from datetime import timedelta
from decimal import Decimal
from typing import Dict, Any, Optional

from django.db.models import Avg, Count, Sum, Q, F
from django.utils import timezone

from modules.clients.models import Client, ClientHealthScore


class HealthScoreCalculator:
    """Calculator for client health scores."""
    
    def __init__(self, client: Client, lookback_days: int = 90):
        """
        Initialize calculator for a client.
        
        Args:
            client: Client to calculate score for
            lookback_days: Days to look back for historical data
        """
        self.client = client
        self.firm = client.firm
        self.lookback_days = lookback_days
        
        # Calculate lookback date
        self.lookback_date = timezone.now() - timedelta(days=self.lookback_days)
    
    def calculate(self) -> ClientHealthScore:
        """
        Calculate health score for the client.
        
        Returns:
            ClientHealthScore instance with calculated scores
        """
        # Get or create health score record for this client
        health_score, created = ClientHealthScore.objects.get_or_create(
            client=self.client,
            defaults={
                "score": 75,
                "engagement_score": 75,
                "payment_score": 75,
                "communication_score": 75,
                "delivery_score": 75,
            }
        )
        
        # Save previous score for trend calculation
        if not created:
            health_score.previous_score = health_score.score
        
        # Calculate individual factor scores
        engagement_score = self._calculate_engagement_score()
        payment_score = self._calculate_payment_score()
        communication_score = self._calculate_communication_score()
        project_delivery_score = self._calculate_project_delivery_score()
        
        # Update factor scores
        health_score.engagement_score = engagement_score
        health_score.payment_score = payment_score
        health_score.communication_score = communication_score
        health_score.delivery_score = project_delivery_score
        
        # Update metrics
        health_score.days_since_last_activity = self._calculate_days_since_last_activity()
        health_score.overdue_invoice_count = self._calculate_overdue_invoice_count()
        health_score.overdue_invoice_amount = self._calculate_overdue_invoice_amount()
        health_score.avg_payment_delay_days = self._calculate_avg_payment_delay()
        health_score.email_response_rate = self._calculate_email_response_rate()
        health_score.project_completion_rate = self._calculate_project_completion_rate()
        
        # Calculate weighted overall score
        health_score.score = health_score.calculate_score()
        
        # Update trend
        health_score.update_trend()
        
        # Check at-risk status
        health_score.check_at_risk()
        
        # Save to history
        health_score.save_to_history()
        
        # Save the updated health score
        health_score.save()
        
        return health_score
    
    def _calculate_engagement_score(self) -> int:
        """
        Calculate engagement score (0-100).
        
        Factors:
        - Active projects count
        - Recent portal logins
        - Document access frequency
        - Time since last activity
        """
        score = 0
        
        # Active projects (0-40 points)
        active_projects = self.client.active_projects_count
        if active_projects > 0:
            score += min(40, active_projects * 10)
        
        # Recent activity (0-30 points)
        # Check for projects, invoices, or communications in lookback period
        from modules.projects.models import Project
        from modules.finance.models import Invoice
        
        recent_projects = Project.objects.filter(
            client=self.client,
            created_at__gte=self.lookback_date
        ).count()
        
        recent_invoices = Invoice.objects.filter(
            client=self.client,
            created_at__gte=self.lookback_date
        ).count()
        
        if recent_projects > 0 or recent_invoices > 0:
            score += 30
        elif (timezone.now().date() - self.client.created_at.date()).days < self.lookback_days:
            # New client, give benefit of the doubt
            score += 20
        
        # Client status (0-30 points)
        if self.client.status == "active":
            score += 30
        elif self.client.status == "inactive":
            score += 10
        
        return min(100, score)
    
    def _calculate_payment_score(self) -> int:
        """
        Calculate payment score (0-100).
        
        Factors:
        - Payment history (on-time vs late)
        - Overdue invoices
        - Average payment delay
        - Outstanding balance
        """
        from modules.finance.models import Invoice
        
        score = 100  # Start at perfect score, deduct for issues
        
        # Get all invoices in lookback period
        invoices = Invoice.objects.filter(
            client=self.client,
            created_at__gte=self.lookback_date
        )
        
        total_invoices = invoices.count()
        
        if total_invoices == 0:
            # No recent invoices - neutral score
            return 70
        
        # Overdue invoices (-30 points max)
        overdue_invoices = invoices.filter(status="overdue").count()
        if overdue_invoices > 0:
            overdue_ratio = overdue_invoices / total_invoices
            score -= int(30 * overdue_ratio)
        
        # Failed payments (-20 points max)
        failed_invoices = invoices.filter(status="failed").count()
        if failed_invoices > 0:
            failed_ratio = failed_invoices / total_invoices
            score -= int(20 * failed_ratio)
        
        # Disputed invoices (-15 points max)
        disputed_invoices = invoices.filter(status="disputed").count()
        if disputed_invoices > 0:
            disputed_ratio = disputed_invoices / total_invoices
            score -= int(15 * disputed_ratio)
        
        # Partial payments (-10 points max)
        partial_invoices = invoices.filter(status="partial").count()
        if partial_invoices > 0:
            partial_ratio = partial_invoices / total_invoices
            score -= int(10 * partial_ratio)
        
        return max(0, min(100, score))
    
    def _calculate_communication_score(self) -> int:
        """
        Calculate communication score (0-100).
        
        Factors:
        - Message frequency
        - Response rate
        - Recent communication activity
        """
        from modules.communications.models import Conversation
        from modules.projects.models import Project
        
        score = 50  # Start at neutral
        
        # Find conversations related to this client
        client_projects = Project.objects.filter(client=self.client).values_list("id", flat=True)
        
        conversations = Conversation.objects.filter(
            firm=self.firm,
            last_message_at__gte=self.lookback_date
        ).filter(
            Q(primary_object_type="Client", primary_object_id=self.client.id) |
            Q(primary_object_type="Project", primary_object_id__in=client_projects)
        )
        
        conversation_count = conversations.count()
        
        if conversation_count == 0:
            # No recent communication - slightly negative
            return 40
        
        # Active communication (+30 points)
        if conversation_count > 0:
            score += min(30, conversation_count * 5)
        
        # Message frequency (+20 points max)
        total_messages = conversations.aggregate(total=Sum("message_count"))["total"] or 0
        if total_messages > 0:
            score += min(20, total_messages // 5)
        
        return min(100, score)
    
    def _calculate_project_delivery_score(self) -> int:
        """
        Calculate project delivery score (0-100).
        
        Factors:
        - On-time project completion
        - Project status distribution
        - Overdue tasks
        """
        from modules.projects.models import Project
        
        score = 70  # Start at good baseline
        
        # Get all projects in lookback period
        projects = Project.objects.filter(
            client=self.client,
            created_at__gte=self.lookback_date
        )
        
        total_projects = projects.count()
        
        if total_projects == 0:
            # No recent projects - neutral score
            return 60
        
        # Completed projects (+20 points max)
        completed_projects = projects.filter(status="completed").count()
        if completed_projects > 0:
            completion_ratio = completed_projects / total_projects
            score += int(20 * completion_ratio)
        
        # On hold projects (-10 points max)
        on_hold_projects = projects.filter(status="on_hold").count()
        if on_hold_projects > 0:
            on_hold_ratio = on_hold_projects / total_projects
            score -= int(10 * on_hold_ratio)
        
        # Cancelled projects (-15 points max)
        cancelled_projects = projects.filter(status="cancelled").count()
        if cancelled_projects > 0:
            cancelled_ratio = cancelled_projects / total_projects
            score -= int(15 * cancelled_ratio)
        
        return max(0, min(100, score))
    
    def _calculate_days_since_last_activity(self) -> int:
        """Calculate days since last client activity."""
        from modules.projects.models import Project
        from modules.finance.models import Invoice
        from modules.communications.models import Conversation
        
        # Check various activity sources
        last_project = Project.objects.filter(client=self.client).order_by("-created_at").first()
        last_invoice = Invoice.objects.filter(client=self.client).order_by("-created_at").first()
        
        latest_date = None
        
        if last_project and last_project.created_at:
            latest_date = last_project.created_at
        
        if last_invoice and last_invoice.created_at:
            if latest_date is None or last_invoice.created_at > latest_date:
                latest_date = last_invoice.created_at
        
        if latest_date:
            return (timezone.now() - latest_date).days
        
        return (timezone.now().date() - self.client.created_at.date()).days
    
    def _calculate_overdue_invoice_count(self) -> int:
        """Calculate number of overdue invoices."""
        from modules.finance.models import Invoice
        
        return Invoice.objects.filter(
            client=self.client,
            status="overdue"
        ).count()
    
    def _calculate_overdue_invoice_amount(self) -> Decimal:
        """Calculate total overdue invoice amount."""
        from modules.finance.models import Invoice
        
        result = Invoice.objects.filter(
            client=self.client,
            status="overdue"
        ).aggregate(total=Sum("total_amount"))
        
        return result["total"] or Decimal("0.00")
    
    def _calculate_avg_payment_delay(self) -> int:
        """Calculate average payment delay in days."""
        from modules.finance.models import Invoice
        
        paid_invoices = Invoice.objects.filter(
            client=self.client,
            status="paid",
            paid_date__isnull=False,
            due_date__isnull=False
        )
        
        if not paid_invoices.exists():
            return 0
        
        total_delay = 0
        count = 0
        
        for invoice in paid_invoices:
            if invoice.paid_date and invoice.due_date:
                delay = (invoice.paid_date - invoice.due_date).days
                if delay > 0:  # Only count late payments
                    total_delay += delay
                    count += 1
        
        return total_delay // count if count > 0 else 0
    
    def _calculate_email_response_rate(self) -> Decimal:
        """Calculate email response rate percentage."""
        # Placeholder - would need email tracking to calculate
        return Decimal("80.00")
    
    def _calculate_project_completion_rate(self) -> Decimal:
        """Calculate project completion rate percentage."""
        from modules.projects.models import Project
        
        projects = Project.objects.filter(client=self.client)
        total_projects = projects.count()
        
        if total_projects == 0:
            return Decimal("100.00")
        
        completed_projects = projects.filter(status="completed").count()
        
        return Decimal(str(round((completed_projects / total_projects) * 100, 2)))


def calculate_all_client_health_scores(firm_id: int, lookback_days: int = 90) -> int:
    """
    Calculate health scores for all active clients in a firm.
    
    Args:
        firm_id: ID of the firm
        lookback_days: Days to look back for historical data
        
    Returns:
        Number of clients processed
    """
    clients = Client.objects.filter(
        firm_id=firm_id,
        status="active"
    )
    
    count = 0
    for client in clients:
        calculator = HealthScoreCalculator(client, lookback_days)
        calculator.calculate()
        count += 1
    
    return count
