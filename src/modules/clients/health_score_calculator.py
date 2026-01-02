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

from modules.clients.models import Client
from modules.clients.health_score import ClientHealthScore, ClientHealthScoreConfig, ClientHealthScoreAlert


class HealthScoreCalculator:
    """Calculator for client health scores."""
    
    def __init__(self, client: Client, config: Optional[ClientHealthScoreConfig] = None):
        """
        Initialize calculator for a client.
        
        Args:
            client: Client to calculate score for
            config: Optional custom config (defaults to firm's active config)
        """
        self.client = client
        self.firm = client.firm
        
        # Get or create config
        if config is None:
            config, _ = ClientHealthScoreConfig.objects.get_or_create(
                firm=self.firm,
                is_active=True,
                defaults={
                    "engagement_weight": 25,
                    "payment_weight": 30,
                    "communication_weight": 20,
                    "project_delivery_weight": 25,
                    "alert_threshold": 20,
                    "at_risk_threshold": 50,
                    "lookback_days": 90,
                }
            )
        self.config = config
        
        # Calculate lookback date
        self.lookback_date = timezone.now() - timedelta(days=self.config.lookback_days)
    
    def calculate(self) -> ClientHealthScore:
        """
        Calculate health score for the client.
        
        Returns:
            ClientHealthScore instance with calculated scores
        """
        # Calculate individual factor scores
        engagement_score = self._calculate_engagement_score()
        payment_score = self._calculate_payment_score()
        communication_score = self._calculate_communication_score()
        project_delivery_score = self._calculate_project_delivery_score()
        
        # Calculate weighted overall score
        overall_score = int(
            (engagement_score * self.config.engagement_weight / 100) +
            (payment_score * self.config.payment_weight / 100) +
            (communication_score * self.config.communication_weight / 100) +
            (project_delivery_score * self.config.project_delivery_weight / 100)
        )
        
        # Get previous score for comparison
        previous_health_score = ClientHealthScore.objects.filter(
            client=self.client
        ).order_by("-calculated_at").first()
        
        previous_score = previous_health_score.score if previous_health_score else None
        score_change = overall_score - previous_score if previous_score is not None else 0
        
        # Determine if at risk
        is_at_risk = overall_score < self.config.at_risk_threshold
        
        # Determine if alert should be triggered
        triggered_alert = False
        if previous_score is not None and score_change < 0:
            triggered_alert = abs(score_change) >= self.config.alert_threshold
        
        # Build calculation metadata
        metadata = {
            "engagement": self._get_engagement_metadata(),
            "payment": self._get_payment_metadata(),
            "communication": self._get_communication_metadata(),
            "project_delivery": self._get_project_delivery_metadata(),
            "config": {
                "engagement_weight": self.config.engagement_weight,
                "payment_weight": self.config.payment_weight,
                "communication_weight": self.config.communication_weight,
                "project_delivery_weight": self.config.project_delivery_weight,
                "lookback_days": self.config.lookback_days,
            },
            "calculation_date": timezone.now().isoformat(),
        }
        
        # Create health score record
        health_score = ClientHealthScore.objects.create(
            firm=self.firm,
            client=self.client,
            score=overall_score,
            engagement_score=engagement_score,
            payment_score=payment_score,
            communication_score=communication_score,
            project_delivery_score=project_delivery_score,
            calculation_metadata=metadata,
            previous_score=previous_score,
            score_change=score_change,
            is_at_risk=is_at_risk,
            triggered_alert=triggered_alert,
        )
        
        # Create alert if triggered
        if triggered_alert:
            ClientHealthScoreAlert.objects.create(
                firm=self.firm,
                client=self.client,
                health_score=health_score,
                status="pending",
                score_drop=abs(score_change),
                previous_score=previous_score,
                current_score=overall_score,
            )
        
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
        elif (timezone.now().date() - self.client.created_at.date()).days < self.config.lookback_days:
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
        
        # Paid on time (+0 points, already at 100)
        paid_invoices = invoices.filter(status="paid").count()
        on_time_ratio = paid_invoices / total_invoices if total_invoices > 0 else 0
        
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
        from modules.communications.models import Conversation, Message
        
        score = 50  # Start at neutral
        
        # Find conversations related to this client
        # Look for conversations linked to client or their projects
        from modules.projects.models import Project
        
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
        
        # Active projects (0 points, neutral)
        active_projects = projects.filter(status="active").count()
        
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
    
    def _get_engagement_metadata(self) -> Dict[str, Any]:
        """Get detailed engagement metrics."""
        from modules.projects.models import Project
        from modules.finance.models import Invoice
        
        return {
            "active_projects_count": self.client.active_projects_count,
            "recent_projects_count": Project.objects.filter(
                client=self.client,
                created_at__gte=self.lookback_date
            ).count(),
            "recent_invoices_count": Invoice.objects.filter(
                client=self.client,
                created_at__gte=self.lookback_date
            ).count(),
            "client_status": self.client.status,
            "client_age_days": (timezone.now().date() - self.client.created_at.date()).days,
        }
    
    def _get_payment_metadata(self) -> Dict[str, Any]:
        """Get detailed payment metrics."""
        from modules.finance.models import Invoice
        
        invoices = Invoice.objects.filter(
            client=self.client,
            created_at__gte=self.lookback_date
        )
        
        return {
            "total_invoices": invoices.count(),
            "paid_invoices": invoices.filter(status="paid").count(),
            "overdue_invoices": invoices.filter(status="overdue").count(),
            "failed_invoices": invoices.filter(status="failed").count(),
            "disputed_invoices": invoices.filter(status="disputed").count(),
            "partial_invoices": invoices.filter(status="partial").count(),
            "total_amount_due": float(invoices.aggregate(
                total=Sum("total_amount")
            )["total"] or Decimal("0.00")),
        }
    
    def _get_communication_metadata(self) -> Dict[str, Any]:
        """Get detailed communication metrics."""
        from modules.communications.models import Conversation
        from modules.projects.models import Project
        
        client_projects = Project.objects.filter(client=self.client).values_list("id", flat=True)
        
        conversations = Conversation.objects.filter(
            firm=self.firm,
            last_message_at__gte=self.lookback_date
        ).filter(
            Q(primary_object_type="Client", primary_object_id=self.client.id) |
            Q(primary_object_type="Project", primary_object_id__in=client_projects)
        )
        
        return {
            "conversation_count": conversations.count(),
            "total_messages": conversations.aggregate(total=Sum("message_count"))["total"] or 0,
        }
    
    def _get_project_delivery_metadata(self) -> Dict[str, Any]:
        """Get detailed project delivery metrics."""
        from modules.projects.models import Project
        
        projects = Project.objects.filter(
            client=self.client,
            created_at__gte=self.lookback_date
        )
        
        return {
            "total_projects": projects.count(),
            "completed_projects": projects.filter(status="completed").count(),
            "active_projects": projects.filter(status="active").count(),
            "on_hold_projects": projects.filter(status="on_hold").count(),
            "cancelled_projects": projects.filter(status="cancelled").count(),
        }


def calculate_all_client_health_scores(firm_id: int) -> int:
    """
    Calculate health scores for all active clients in a firm.
    
    Args:
        firm_id: ID of the firm
        
    Returns:
        Number of clients processed
    """
    clients = Client.objects.filter(
        firm_id=firm_id,
        status="active"
    )
    
    count = 0
    for client in clients:
        calculator = HealthScoreCalculator(client)
        calculator.calculate()
        count += 1
    
    return count
