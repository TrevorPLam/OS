"""
Stripe Reconciliation Service (ASSESS-G18.5).

Implements daily reconciliation to cross-check Invoice status vs Stripe API.
Flags mismatches for manual review.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

import stripe
from django.utils import timezone
from django.db.models import Q

from modules.finance.models import Invoice
from modules.finance.services import StripeService
from modules.firm.audit import AuditEvent
from modules.firm.models import Firm

logger = logging.getLogger(__name__)


class StripeReconciliationService:
    """
    Service for reconciling Invoice records with Stripe API.

    ASSESS-G18.5: Daily cron to cross-check Invoice status vs Stripe API; flag mismatches.
    """

    def __init__(self, firm: Firm = None):
        """
        Initialize reconciliation service.

        Args:
            firm: Optional firm to reconcile (if None, reconciles all firms)
        """
        self.firm = firm
        self.stripe_service = StripeService()
        self.mismatches = []

    def reconcile_all_firms(self) -> Dict[str, Any]:
        """
        Reconcile invoices for all active firms.

        Returns:
            Dict with reconciliation summary
        """
        firms = Firm.objects.filter(status__in=["active", "trial"])
        if self.firm:
            firms = firms.filter(id=self.firm.id)

        total_invoices = 0
        total_mismatches = 0
        firm_results = []

        for firm in firms:
            result = self.reconcile_firm(firm)
            total_invoices += result["total_invoices"]
            total_mismatches += result["mismatches_count"]
            firm_results.append(result)

        return {
            "reconciliation_date": timezone.now().isoformat(),
            "firms_processed": len(firm_results),
            "total_invoices": total_invoices,
            "total_mismatches": total_mismatches,
            "firm_results": firm_results,
        }

    def reconcile_firm(self, firm: Firm) -> Dict[str, Any]:
        """
        Reconcile invoices for a specific firm.

        Args:
            firm: Firm to reconcile

        Returns:
            Dict with reconciliation results
        """
        logger.info(f"Starting Stripe reconciliation for firm {firm.id} ({firm.name})")

        # Get invoices with Stripe IDs
        invoices = Invoice.objects.filter(
            firm=firm,
        ).exclude(
            Q(stripe_invoice_id="") | Q(stripe_invoice_id__isnull=True)
        ).exclude(
            Q(stripe_payment_intent_id="") | Q(stripe_payment_intent_id__isnull=True)
        )

        mismatches = []
        reconciled = 0
        errors = []

        for invoice in invoices:
            try:
                mismatch = self._reconcile_invoice(invoice)
                if mismatch:
                    mismatches.append(mismatch)
                else:
                    reconciled += 1
            except Exception as e:
                logger.error(f"Error reconciling invoice {invoice.id}: {str(e)}")
                errors.append({
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "error": str(e),
                })

        # Create audit event for reconciliation run
        AuditEvent.objects.create(
            firm=firm,
            category=AuditEvent.CATEGORY_SYSTEM,
            action="stripe_reconciliation_run",
            severity=AuditEvent.SEVERITY_INFO,
            resource_type="Invoice",
            metadata={
                "total_invoices": invoices.count(),
                "reconciled": reconciled,
                "mismatches": len(mismatches),
                "errors": len(errors),
            },
        )

        return {
            "firm_id": firm.id,
            "firm_name": firm.name,
            "total_invoices": invoices.count(),
            "reconciled": reconciled,
            "mismatches_count": len(mismatches),
            "mismatches": mismatches,
            "errors": errors,
        }

    def _reconcile_invoice(self, invoice: Invoice) -> Dict[str, Any] | None:
        """
        Reconcile a single invoice with Stripe.

        Args:
            invoice: Invoice to reconcile

        Returns:
            Mismatch dict if found, None otherwise
        """
        import stripe

        # Try to fetch from Stripe using invoice ID first, then payment intent
        stripe_invoice = None
        stripe_payment_intent = None

        if invoice.stripe_invoice_id:
            try:
                stripe_invoice = stripe.Invoice.retrieve(invoice.stripe_invoice_id)
            except stripe.error.InvalidRequestError:
                # Invoice might not exist in Stripe
                pass

        if invoice.stripe_payment_intent_id:
            try:
                stripe_payment_intent = stripe.PaymentIntent.retrieve(invoice.stripe_payment_intent_id)
            except stripe.error.InvalidRequestError:
                # Payment intent might not exist
                pass

        # Determine expected status from Stripe
        expected_status = self._map_stripe_status_to_invoice_status(
            stripe_invoice, stripe_payment_intent
        )

        # Check for mismatches
        mismatches = []

        if expected_status and invoice.status != expected_status:
            mismatches.append({
                "field": "status",
                "local_value": invoice.status,
                "stripe_value": expected_status,
            })

        # Check amount mismatch
        if stripe_invoice:
            stripe_amount = Decimal(stripe_invoice.amount_due) / 100  # Convert cents to dollars
            if abs(float(invoice.total_amount) - float(stripe_amount)) > 0.01:
                mismatches.append({
                    "field": "total_amount",
                    "local_value": str(invoice.total_amount),
                    "stripe_value": str(stripe_amount),
                })

        # Check paid date
        if stripe_payment_intent and stripe_payment_intent.status == "succeeded":
            stripe_paid_at = datetime.fromtimestamp(stripe_payment_intent.created)
            if invoice.paid_date:
                local_paid_date = datetime.combine(invoice.paid_date, datetime.min.time())
                if abs((stripe_paid_at - local_paid_date).total_seconds()) > 86400:  # More than 1 day difference
                    mismatches.append({
                        "field": "paid_date",
                        "local_value": invoice.paid_date.isoformat(),
                        "stripe_value": stripe_paid_at.date().isoformat(),
                    })

        if mismatches:
            # Create audit event for mismatch
            AuditEvent.objects.create(
                firm=invoice.firm,
                category=AuditEvent.CATEGORY_SYSTEM,
                action="stripe_reconciliation_mismatch",
                severity=AuditEvent.SEVERITY_WARNING,
                resource_type="Invoice",
                resource_id=str(invoice.id),
                metadata={
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "mismatches": mismatches,
                    "stripe_invoice_id": invoice.stripe_invoice_id,
                    "stripe_payment_intent_id": invoice.stripe_payment_intent_id,
                },
            )

            return {
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "mismatches": mismatches,
            }

        return None

    def _map_stripe_status_to_invoice_status(
        self, stripe_invoice, stripe_payment_intent
    ) -> str | None:
        """
        Map Stripe status to Invoice status.

        Args:
            stripe_invoice: Stripe Invoice object or None
            stripe_payment_intent: Stripe PaymentIntent object or None

        Returns:
            Expected Invoice status or None
        """
        from decimal import Decimal

        # Priority: PaymentIntent status (more recent)
        if stripe_payment_intent:
            status = stripe_payment_intent.status
            if status == "succeeded":
                return "paid"
            elif status == "requires_payment_method":
                return "sent"
            elif status == "canceled":
                return "cancelled"
            elif status in ["requires_action", "requires_confirmation"]:
                return "sent"

        # Fallback: Invoice status
        if stripe_invoice:
            status = stripe_invoice.status
            if status == "paid":
                return "paid"
            elif status == "open":
                return "sent"
            elif status == "draft":
                return "draft"
            elif status == "void":
                return "cancelled"
            elif status == "uncollectible":
                return "failed"

        return None
