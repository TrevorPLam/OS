"""
Deal Rotting Alert Utilities (DEAL-6).

Helper functions for detecting and reporting on stale deals.
"""

from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def _get_user_display_name(user_data):
    """
    Get display name for a user from query data.
    
    Args:
        user_data: Dictionary with user fields (owner__first_name, owner__last_name, owner__email)
        
    Returns:
        String display name
    """
    first = user_data.get('owner__first_name', '').strip()
    last = user_data.get('owner__last_name', '').strip()
    email = user_data.get('owner__email', 'Unknown')
    
    if first and last:
        return f"{first} {last}"
    elif first:
        return first
    elif last:
        return last
    else:
        return email


def check_and_mark_stale_deals():
    """
    Check all active deals and mark them as stale if needed (DEAL-6).
    
    This function should be called periodically (e.g., daily cron job).
    
    Returns:
        Number of deals marked as stale
    """
    # Import here to avoid circular imports
    from django.apps import apps
    Deal = apps.get_model('crm', 'Deal')
    
    now = timezone.now().date()
    
    # Get all active deals with last_activity_date
    active_deals = Deal.objects.filter(
        is_active=True,
        last_activity_date__isnull=False
    )
    
    marked_stale = 0
    unmarked_stale = 0
    
    for deal in active_deals:
        days_since_activity = (now - deal.last_activity_date).days
        
        # Check if deal should be marked as stale
        if days_since_activity >= deal.stale_days_threshold and not deal.is_stale:
            deal.is_stale = True
            deal.save(update_fields=['is_stale', 'updated_at'])
            marked_stale += 1
            logger.info(f'Marked deal {deal.id} as stale ({days_since_activity} days inactive)')
        
        # Unmark stale if activity was recorded
        elif days_since_activity < deal.stale_days_threshold and deal.is_stale:
            deal.is_stale = False
            deal.save(update_fields=['is_stale', 'updated_at'])
            unmarked_stale += 1
            logger.info(f'Unmarked deal {deal.id} as stale')
    
    logger.info(f'Marked {marked_stale} deals as stale, unmarked {unmarked_stale}')
    return marked_stale


def get_stale_deal_report(firm_id=None):
    """
    Generate a report of stale deals (DEAL-6).
    
    Args:
        firm_id: Optional firm ID to filter by
        
    Returns:
        Dictionary with stale deal statistics
    """
    # Import here to avoid circular imports
    from django.apps import apps
    Deal = apps.get_model('crm', 'Deal')
    
    queryset = Deal.objects.filter(is_active=True, is_stale=True)
    if firm_id:
        queryset = queryset.filter(firm_id=firm_id)
    
    # Calculate statistics
    total_stale = queryset.count()
    total_value = queryset.aggregate(Sum('value'))['value__sum'] or 0
    weighted_value = queryset.aggregate(Sum('weighted_value'))['weighted_value__sum'] or 0
    
    # Group by owner
    by_owner = queryset.values(
        'owner__email', 'owner__first_name', 'owner__last_name', 'owner_id'
    ).annotate(
        deal_count=Count('id'),
        total_value=Sum('value'),
        weighted_value=Sum('weighted_value')
    ).order_by('-deal_count')
    
    # Add display names
    by_owner_list = []
    for owner in by_owner:
        owner['display_name'] = _get_user_display_name(owner)
        by_owner_list.append(owner)
    
    # Group by pipeline
    by_pipeline = queryset.values(
        'pipeline__name', 'pipeline_id'
    ).annotate(
        deal_count=Count('id'),
        total_value=Sum('value'),
        weighted_value=Sum('weighted_value')
    ).order_by('-deal_count')
    
    # Group by stage
    by_stage = queryset.values(
        'stage__name', 'stage_id', 'pipeline__name'
    ).annotate(
        deal_count=Count('id'),
        total_value=Sum('value')
    ).order_by('-deal_count')
    
    # Group by age (days stale)
    now = timezone.now().date()
    age_ranges = {
        '30-60 days': queryset.filter(
            last_activity_date__gte=now - timedelta(days=60),
            last_activity_date__lt=now - timedelta(days=30)
        ).count(),
        '60-90 days': queryset.filter(
            last_activity_date__gte=now - timedelta(days=90),
            last_activity_date__lt=now - timedelta(days=60)
        ).count(),
        '90+ days': queryset.filter(
            last_activity_date__lt=now - timedelta(days=90)
        ).count(),
    }
    
    # Get most at-risk deals (high value + very stale)
    at_risk_deals = queryset.filter(
        last_activity_date__lt=now - timedelta(days=60)
    ).order_by('-value')[:10].values(
        'id', 'name', 'value', 'weighted_value', 'last_activity_date',
        'expected_close_date', 'owner__email', 'stage__name', 'pipeline__name'
    )
    
    return {
        'total_stale_deals': total_stale,
        'total_value_at_risk': float(total_value),
        'total_weighted_value_at_risk': float(weighted_value),
        'by_owner': by_owner_list,
        'by_pipeline': list(by_pipeline),
        'by_stage': list(by_stage),
        'age_distribution': age_ranges,
        'at_risk_deals': list(at_risk_deals),
    }


def get_deal_splitting_report(firm_id=None):
    """
    Generate a report of deals with split ownership (DEAL-6).
    
    Args:
        firm_id: Optional firm ID to filter by
        
    Returns:
        Dictionary with split deal statistics
    """
    # Import here to avoid circular imports
    from django.apps import apps
    from django.db.models import Q
    Deal = apps.get_model('crm', 'Deal')
    
    # Find deals with split_percentage data
    queryset = Deal.objects.filter(is_active=True).exclude(
        Q(split_percentage__isnull=True) | Q(split_percentage={})
    )
    
    if firm_id:
        queryset = queryset.filter(firm_id=firm_id)
    
    total_split_deals = queryset.count()
    total_value = queryset.aggregate(Sum('value'))['value__sum'] or 0
    
    # Get details of split deals
    split_deals = queryset.values(
        'id', 'name', 'value', 'split_percentage', 'owner__email',
        'pipeline__name', 'stage__name'
    ).order_by('-value')
    
    return {
        'total_split_deals': total_split_deals,
        'total_value': float(total_value),
        'deals': list(split_deals),
    }


def send_stale_deal_digest(firm_id, recipient_email):
    """
    Send a digest email with stale deal report (DEAL-6).
    
    Args:
        firm_id: Firm ID
        recipient_email: Email address to send digest to
        
    Returns:
        Boolean indicating success
    """
    from django.core.mail import send_mail
    from django.conf import settings
    
    report = get_stale_deal_report(firm_id)
    
    if report['total_stale_deals'] == 0:
        logger.info(f'No stale deals for firm {firm_id}, skipping digest')
        return False
    
    subject = f"📊 Stale Deals Digest - {report['total_stale_deals']} Deals Need Attention"
    
    # Build message
    message = f"""
Stale Deals Digest

Summary:
- Total Stale Deals: {report['total_stale_deals']}
- Total Value at Risk: ${report['total_value_at_risk']:,.2f}
- Weighted Value: ${report['total_weighted_value_at_risk']:,.2f}

Age Distribution:
- 30-60 days: {report['age_distribution']['30-60 days']} deals
- 60-90 days: {report['age_distribution']['60-90 days']} deals
- 90+ days: {report['age_distribution']['90+ days']} deals

By Owner:
"""
    
    for owner in report['by_owner'][:5]:
        name = owner.get('display_name', 'Unknown')
        message += f"- {name}: {owner['deal_count']} deals (${owner['total_value']:,.2f})\n"
    
    message += "\nBy Pipeline:\n"
    for pipeline in report['by_pipeline'][:5]:
        message += f"- {pipeline['pipeline__name']}: {pipeline['deal_count']} deals (${pipeline['total_value']:,.2f})\n"
    
    message += "\nTop At-Risk Deals:\n"
    for deal in report['at_risk_deals'][:5]:
        message += f"- {deal['name']}: ${deal['value']:,.2f} - Last activity: {deal['last_activity_date']}\n"
    
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    message += f"\nView all stale deals: {frontend_url}/crm/deals?stale=true\n"
    
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f'Sent stale deal digest to {recipient_email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send digest to {recipient_email}: {e}')
        return False
