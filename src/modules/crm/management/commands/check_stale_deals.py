"""
Management command to check for stale deals and create alerts (DEAL-6).

This command should be run periodically (e.g., via cron) to:
1. Identify stale deals that have had no activity for extended periods
2. Create alerts for deal owners and stakeholders
3. Send notifications to relevant users

Example usage:
    python manage.py check_stale_deals
    python manage.py check_stale_deals --send-notifications
    python manage.py check_stale_deals --firm-id 123
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from modules.crm.models import Deal, DealAlert
from modules.firm.models import Firm


class Command(BaseCommand):
    help = "Check for stale deals and create alerts (DEAL-6)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--firm-id',
            type=int,
            help='Process only deals for a specific firm',
        )
        parser.add_argument(
            '--send-notifications',
            action='store_true',
            help='Send notifications for created alerts',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='Override stale days threshold (default: use deal setting)',
        )

    def handle(self, *args, **options):
        firm_id = options.get('firm_id')
        send_notifications = options.get('send_notifications', False)
        days_override = options.get('days')
        
        # Get firms to process
        if firm_id:
            firms = Firm.objects.filter(id=firm_id)
            if not firms.exists():
                self.stdout.write(self.style.ERROR(f'Firm with id {firm_id} not found'))
                return
        else:
            firms = Firm.objects.filter(is_active=True)
        
        total_alerts_created = 0
        total_deals_checked = 0
        
        for firm in firms:
            self.stdout.write(f'\nProcessing firm: {firm.name}')
            
            # Get active deals for this firm
            deals = Deal.objects.filter(
                firm=firm,
                is_active=True,
                is_won=False,
                is_lost=False
            )
            
            alerts_created = 0
            
            for deal in deals:
                total_deals_checked += 1
                
                # Determine stale threshold
                threshold = days_override if days_override else (deal.stale_days_threshold or 30)
                
                # Check if deal is stale
                if deal.last_activity_date:
                    days_since_activity = (timezone.now().date() - deal.last_activity_date).days
                    
                    if days_since_activity >= threshold:
                        # Mark deal as stale if not already
                        if not deal.is_stale:
                            deal.is_stale = True
                            deal.save(update_fields=['is_stale', 'updated_at'])
                            self.stdout.write(f'  Marked deal as stale: {deal.name} ({days_since_activity} days)')
                        
                        # Check if an unacknowledged stale alert already exists
                        existing_alert = DealAlert.objects.filter(
                            deal=deal,
                            alert_type='stale',
                            is_acknowledged=False,
                            is_dismissed=False
                        ).first()
                        
                        if not existing_alert:
                            # Create alert
                            alert = DealAlert.objects.create(
                                deal=deal,
                                alert_type='stale',
                                priority='high' if days_since_activity >= threshold * 2 else 'medium',
                                title=f'Stale Deal: {deal.name}',
                                message=f'Deal "{deal.name}" has had no activity for {days_since_activity} days. '
                                       f'Current stage: {deal.stage.name}. Value: ${deal.value}.',
                            )
                            
                            # Add recipients (owner and secondary owners)
                            recipients = []
                            if deal.owner:
                                recipients.append(deal.owner)
                            recipients.extend(deal.secondary_owners.all())
                            
                            alert.recipients.set(recipients)
                            alerts_created += 1
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  Created alert for stale deal: {deal.name} ({days_since_activity} days)'
                                )
                            )
                            
                            # Send notification if requested
                            if send_notifications:
                                alert.send_notification()
                                self.stdout.write(f'    Sent notification to {len(recipients)} recipient(s)')
                
                # Check for approaching close dates
                if deal.expected_close_date:
                    days_until_close = (deal.expected_close_date - timezone.now().date()).days
                    
                    # Alert if close date is within 7 days
                    if 0 <= days_until_close <= 7:
                        existing_alert = DealAlert.objects.filter(
                            deal=deal,
                            alert_type='close_date',
                            is_acknowledged=False,
                            is_dismissed=False,
                            created_at__gte=timezone.now() - timedelta(days=7)
                        ).first()
                        
                        if not existing_alert:
                            alert = DealAlert.objects.create(
                                deal=deal,
                                alert_type='close_date',
                                priority='high' if days_until_close <= 3 else 'medium',
                                title=f'Close Date Approaching: {deal.name}',
                                message=f'Deal "{deal.name}" is expected to close in {days_until_close} day(s). '
                                       f'Current stage: {deal.stage.name}. Value: ${deal.value}.',
                            )
                            
                            recipients = []
                            if deal.owner:
                                recipients.append(deal.owner)
                            recipients.extend(deal.secondary_owners.all())
                            
                            alert.recipients.set(recipients)
                            alerts_created += 1
                            
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  Created alert for approaching close date: {deal.name} ({days_until_close} days)'
                                )
                            )
                            
                            if send_notifications:
                                alert.send_notification()
            
            total_alerts_created += alerts_created
            self.stdout.write(f'  Created {alerts_created} alert(s) for firm {firm.name}')
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary:'
                f'\n  Firms processed: {firms.count()}'
                f'\n  Deals checked: {total_deals_checked}'
                f'\n  Alerts created: {total_alerts_created}'
            )
        )
