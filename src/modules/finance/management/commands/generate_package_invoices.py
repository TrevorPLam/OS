"""
TIER 4.2: Package Invoice Generation Management Command

Automatically generates package fee invoices based on engagement schedules.

This command:
1. Finds all active engagements with package billing
2. Determines which invoices are due based on schedule
3. Generates invoices for the current billing period
4. Prevents duplicate invoice generation

Usage:
    python manage.py generate_package_invoices [--dry-run] [--firm-id ID]

Options:
    --dry-run: Show what would be generated without creating invoices
    --firm-id: Generate invoices for a specific firm only
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
import logging

from modules.clients.models import ClientEngagement
from modules.finance.billing import (
    create_package_invoice,
    get_package_billing_period,
    should_generate_package_invoice,
)
from modules.firm.models import Firm

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate package fee invoices for active engagements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without creating invoices',
        )
        parser.add_argument(
            '--firm-id',
            type=int,
            help='Generate invoices for a specific firm only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        firm_id = options.get('firm_id')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No invoices will be created'))

        # Get firms to process
        if firm_id:
            try:
                firms = [Firm.objects.get(id=firm_id, status__in=['active', 'trial'])]
            except Firm.DoesNotExist:
                raise CommandError(f'Firm with ID {firm_id} not found or not active')
        else:
            firms = Firm.objects.filter(status__in=['active', 'trial'])

        total_generated = 0
        total_skipped = 0
        total_errors = 0

        for firm in firms:
            self.stdout.write(f'\nProcessing firm: {firm.name} (ID: {firm.id})')

            try:
                generated, skipped = self.process_firm(firm, dry_run)
                total_generated += generated
                total_skipped += skipped
            except Exception as e:
                total_errors += 1
                self.stdout.write(
                    self.style.ERROR(f'Error processing firm {firm.name}: {e}')
                )
                logger.exception(f'Error processing firm {firm.id}')

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n{"=" * 60}'))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS(f'{"=" * 60}'))
        self.stdout.write(f'Firms processed: {len(firms)}')
        self.stdout.write(f'Invoices generated: {total_generated}')
        self.stdout.write(f'Engagements skipped: {total_skipped}')
        if total_errors:
            self.stdout.write(self.style.ERROR(f'Errors: {total_errors}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes made'))

    def process_firm(self, firm, dry_run=False):
        """Process all package billing engagements for a firm."""
        generated_count = 0
        skipped_count = 0

        # Find active engagements with package billing
        engagements = ClientEngagement.objects.filter(
            firm=firm,
            status='current',
            pricing_mode__in=['package', 'mixed'],
            package_fee__isnull=False
        ).select_related('client', 'contract')

        if not engagements.exists():
            self.stdout.write(f'  No package billing engagements found')
            return 0, 0

        reference_date = timezone.now().date()

        for engagement in engagements:
            try:
                period_start, period_end = get_package_billing_period(
                    engagement, reference_date=reference_date
                )

                if self.should_generate_invoice(engagement, reference_date=reference_date):
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [DRY RUN] Would generate invoice for: '
                                f'{engagement.client.name} - ${engagement.package_fee} '
                                f'({period_start} to {period_end})'
                            )
                        )
                        generated_count += 1
                    else:
                        invoice = self.generate_invoice(
                            engagement, issue_date=reference_date, reference_date=reference_date
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Generated invoice {invoice.invoice_number} for '
                                f'{engagement.client.name} - ${invoice.total_amount}'
                            )
                        )
                        generated_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error for engagement {engagement.id}: {e}'
                    )
                )
                logger.exception(f'Error generating invoice for engagement {engagement.id}')

        return generated_count, skipped_count

    def should_generate_invoice(self, engagement, reference_date=None):
        """
        Determine if an invoice should be generated for this engagement.

        Logic:
        - Check if there's already an invoice for the current billing period
        - Check based on package_fee_schedule (Monthly, Quarterly, etc.)
        - Ensure we don't generate duplicates
        """
        return should_generate_package_invoice(engagement, reference_date=reference_date)

    @transaction.atomic
    def generate_invoice(self, engagement, issue_date=None, reference_date=None):
        """
        Generate a package fee invoice for the engagement.

        Returns:
            Invoice: The created invoice
        """
        invoice = create_package_invoice(
            engagement, issue_date=issue_date, reference_date=reference_date
        )

        # Log generation
        logger.info(
            f'Generated package invoice {invoice.invoice_number} for '
            f'engagement {engagement.id}, amount ${invoice.total_amount}'
        )

        return invoice
