"""Execute autopay for invoices that are scheduled for recurring billing."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from modules.finance.billing import process_recurring_invoices


class Command(BaseCommand):
    help = "Charge invoices that are due for autopay based on cadence and payment methods."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="List invoices that would be charged")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no charges will be attempted"))

        if dry_run:
            from modules.finance.models import Invoice

            queued = Invoice.objects.filter(
                autopay_opt_in=True,
                status__in=["sent", "partial", "overdue"],
            )
            for invoice in queued:
                if invoice.autopay_next_charge_at and invoice.autopay_next_charge_at > now:
                    continue
                self.stdout.write(
                    f"Invoice {invoice.invoice_number} for client {invoice.client_id} "
                    f"would be charged ${invoice.total_amount}"
                )
            return

        processed = process_recurring_invoices(reference_time=now)
        self.stdout.write(self.style.SUCCESS(f"Charged {len(processed)} invoices via autopay"))
