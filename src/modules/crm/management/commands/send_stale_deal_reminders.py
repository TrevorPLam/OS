"""
Deal Rotting Alerts and Reminder System (DEAL-6).

Management command to send reminders for stale deals.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from modules.crm.models import Deal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send reminders for stale deals (DEAL-6)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually sending emails',
        )
        parser.add_argument(
            '--firm-id',
            type=int,
            help='Only process deals for specific firm',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        firm_id = options.get('firm_id')
        
        # Find all stale active deals
        queryset = Deal.objects.filter(
            is_active=True,
            is_stale=True
        ).select_related('owner', 'firm', 'stage', 'pipeline')
        
        if firm_id:
            queryset = queryset.filter(firm_id=firm_id)
        
        if not queryset.exists():
            self.stdout.write(self.style.SUCCESS('No stale deals found'))
            return
        
        self.stdout.write(f'Found {queryset.count()} stale deals')
        
        reminders_sent = 0
        for deal in queryset:
            if self.send_stale_deal_reminder(deal, dry_run):
                reminders_sent += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully sent {reminders_sent} reminder{"s" if reminders_sent != 1 else ""}'
            )
        )

    def send_stale_deal_reminder(self, deal, dry_run=False):
        """Send reminder email for a stale deal."""
        if not deal.owner or not deal.owner.email:
            logger.warning(f'Deal {deal.id} has no owner or owner email')
            return False
        
        # Calculate how long deal has been stale
        if not deal.last_activity_date:
            days_stale_str = 'an unknown number of'
            days_stale_display = 'unknown'
        else:
            days_stale = (timezone.now().date() - deal.last_activity_date).days
            days_stale_str = str(days_stale)
            days_stale_display = deal.last_activity_date.strftime('%Y-%m-%d')
        
        subject = f'⚠️ Stale Deal Alert: {deal.name}'
        
        # Get frontend URL from settings, with fallback
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        
        message = f"""
Hello {deal.owner.first_name or deal.owner.email},

This is a reminder that the following deal has had no activity for {days_stale_str} days:

Deal: {deal.name}
Pipeline: {deal.pipeline.name}
Stage: {deal.stage.name}
Value: ${deal.value}
Expected Close: {deal.expected_close_date}
Last Activity: {days_stale_display}

Please review this deal and take appropriate action:
- Update the deal with recent activity
- Move to a different stage
- Mark as won or lost if applicable

You can view this deal at: {frontend_url}/crm/deals

Best regards,
{deal.firm.name} CRM System
        """
        
        if dry_run:
            self.stdout.write(f'[DRY RUN] Would send email to {deal.owner.email} for deal {deal.id}')
            return True
        
        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[deal.owner.email],
                fail_silently=False,
            )
            logger.info(f'Sent stale deal reminder for deal {deal.id} to {deal.owner.email}')
            return True
        except Exception as e:
            logger.error(f'Failed to send reminder for deal {deal.id}: {e}')
            self.stdout.write(self.style.ERROR(f'Failed to send reminder for deal {deal.id}: {e}'))
            return False
