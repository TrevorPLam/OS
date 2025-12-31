"""Execute autopay for invoices that are scheduled for recurring billing."""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from modules.finance.billing import process_recurring_invoices
from modules.firm.models import Firm


class Command(BaseCommand):
    help = "Charge invoices that are due for autopay based on cadence and payment methods."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="List invoices that would be charged")
        parser.add_argument(
            "--firm-id",
            type=int,
            help="Process invoices for a specific firm only (tenant isolation)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        firm_id = options.get("firm_id")
        now = timezone.now()

        # SECURITY: Resolve firm for tenant isolation (ASSESS-S6.2)
        firm = None
        if firm_id:
            try:
                firm = Firm.objects.get(id=firm_id, status__in=["active", "trial"])
                self.stdout.write(f"Processing invoices for firm: {firm.name} (ID: {firm.id})")
            except Firm.DoesNotExist as e:
                raise CommandError(f"Firm with ID {firm_id} not found or not active") from e

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no charges will be attempted"))

        if dry_run:
            from modules.finance.models import Invoice

            # SECURITY: Add firm filtering to dry-run mode (ASSESS-S6.2)
            queued = Invoice.objects.filter(
                autopay_opt_in=True,
                status__in=["sent", "partial", "overdue"],
            ).select_related("client", "firm")

            if firm:
                queued = queued.filter(firm=firm)

            count = 0
            for invoice in queued:
                if invoice.autopay_next_charge_at and invoice.autopay_next_charge_at > now:
                    continue
                self.stdout.write(
                    f"Invoice {invoice.invoice_number} for firm {invoice.firm.name} "
                    f"client {invoice.client_id} would be charged ${invoice.total_amount}"
                )
                count += 1

            self.stdout.write(self.style.SUCCESS(f"\nWould charge {count} invoices via autopay"))
            return

        # SECURITY: Pass firm parameter for tenant isolation (ASSESS-S6.2)
        processed = process_recurring_invoices(reference_time=now, firm=firm)
        self.stdout.write(self.style.SUCCESS(f"Charged {len(processed)} invoices via autopay"))
