"""
Management command for Stripe reconciliation (ASSESS-G18.5).

Daily cron to cross-check Invoice status vs Stripe API; flag mismatches.
"""

from django.core.management.base import BaseCommand
from modules.finance.reconciliation import StripeReconciliationService
from modules.firm.models import Firm


class Command(BaseCommand):
    help = "Reconcile Invoice records with Stripe API (ASSESS-G18.5)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--firm-id",
            type=int,
            help="Reconcile invoices for a specific firm (if not provided, reconciles all firms)",
        )

    def handle(self, *args, **options):
        firm_id = options.get("firm_id")
        firm = None

        if firm_id:
            try:
                firm = Firm.objects.get(id=firm_id)
            except Firm.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Firm with ID {firm_id} not found"))
                return

        service = StripeReconciliationService(firm=firm)
        result = service.reconcile_all_firms()

        self.stdout.write(self.style.SUCCESS(f"Stripe Reconciliation Complete"))
        self.stdout.write(f"Firms processed: {result['firms_processed']}")
        self.stdout.write(f"Total invoices: {result['total_invoices']}")
        self.stdout.write(f"Total mismatches: {result['total_mismatches']}")

        if result["total_mismatches"] > 0:
            self.stdout.write(self.style.WARNING(f"\nMismatches found:"))
            for firm_result in result["firm_results"]:
                if firm_result["mismatches_count"] > 0:
                    self.stdout.write(
                        f"  Firm {firm_result['firm_name']}: {firm_result['mismatches_count']} mismatches"
                    )
                    for mismatch in firm_result["mismatches"]:
                        self.stdout.write(
                            f"    - Invoice {mismatch['invoice_number']}: {mismatch['mismatches']}"
                        )

        if result.get("errors"):
            self.stdout.write(self.style.ERROR(f"\nErrors encountered:"))
            for firm_result in result["firm_results"]:
                if firm_result.get("errors"):
                    for error in firm_result["errors"]:
                        self.stdout.write(f"    - {error}")
