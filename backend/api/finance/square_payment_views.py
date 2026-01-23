"""
Square Payment Processing Views (PAY-2).

TIER 2.5: Payments can be accessed by both firm users and portal users.
Portal users can only pay invoices for their own client.
"""

from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from modules.clients.models import ClientPortalUser
from modules.clients.permissions import IsPortalUserOrFirmUser
from modules.firm.utils import FirmScopingError, get_request_firm
from modules.finance.models import Invoice
from modules.finance.square_service import SquareService

from .serializers import InvoiceSerializer


class SquarePaymentViewSet(viewsets.ViewSet):
    """
    ViewSet for payment processing with Square.

    TIER 2.5: Both firm users and portal users can access payments.
    Portal users are scoped to their own client's invoices only.
    """

    permission_classes = [IsAuthenticated, IsPortalUserOrFirmUser]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.square_service = SquareService()

    def _get_portal_client(self, request):
        portal_user = (
            ClientPortalUser.objects.select_related("client")
            .filter(user=request.user)
            .first()
        )
        if not portal_user:
            return None, None

        if not portal_user.can_view_billing:
            return None, Response(
                {"error": "Billing access is disabled for this portal user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return portal_user.client, None

    def _resolve_invoice(self, request):
        try:
            firm = get_request_firm(request)
        except FirmScopingError as exc:
            return None, Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        invoice_id = request.data.get("invoice_id")
        if not invoice_id:
            return None, Response({"error": "invoice_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            invoice = Invoice.firm_scoped.for_firm(firm).select_related("client").get(id=invoice_id)
        except Invoice.DoesNotExist:
            return None, Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        portal_client, portal_error = self._get_portal_client(request)
        if portal_error:
            return None, portal_error

        if portal_client and portal_client.id != invoice.client_id:
            return None, Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        return invoice, None

    @action(detail=False, methods=["post"], url_path="create-payment")
    def create_payment(self, request):
        """
        Create a Square payment for an invoice.

        POST /api/finance/square-payment/create-payment/
        {
            "invoice_id": 123,
            "source_id": "cnon:xxx",  // Card nonce from Square.js
            "customer_email": "client@example.com"
        }
        """
        try:
            source_id = request.data.get("source_id")
            customer_email = request.data.get("customer_email")

            if not source_id:
                return Response({"error": "source_id (card nonce) is required"}, status=status.HTTP_400_BAD_REQUEST)

            invoice, error_response = self._resolve_invoice(request)
            if error_response:
                return error_response

            # Create or get Square customer
            customer_name = invoice.client.company_name if hasattr(invoice, "client") else "Customer"
            square_customer = self.square_service.create_customer(
                email=customer_email or invoice.client.primary_contact_email,
                given_name=customer_name,
                metadata={"client_id": invoice.client.id, "invoice_id": invoice.id},
            )

            # Create payment
            payment = self.square_service.create_payment(
                amount=invoice.total_amount - invoice.amount_paid,
                currency=invoice.currency,
                customer_id=square_customer["id"],
                source_id=source_id,
                metadata={"invoice_id": invoice.id, "invoice_number": invoice.invoice_number},
                idempotency_key=f"invoice-{invoice.id}-{source_id[:8]}",
            )

            # Update invoice with Square payment ID
            if not invoice.stripe_payment_intent_id:  # Using same field for Square
                invoice.stripe_payment_intent_id = payment["id"]
                invoice.save()

            # Check payment status
            if payment["status"] == "COMPLETED":
                # Update invoice immediately
                amount_paid = Decimal(payment["amount_money"]["amount"]) / 100
                invoice.amount_paid += amount_paid

                if invoice.amount_paid >= invoice.total_amount:
                    invoice.status = "paid"
                    from django.utils import timezone

                    invoice.paid_date = timezone.now().date()
                else:
                    invoice.status = "partial"

                invoice.save()

            return Response(
                {
                    "payment_id": payment["id"],
                    "status": payment["status"],
                    "amount": float(invoice.total_amount - invoice.amount_paid),
                    "currency": invoice.currency,
                    "receipt_url": payment.get("receipt_url", ""),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="create-payment-link")
    def create_payment_link(self, request):
        """
        Create a Square payment link for an invoice.

        POST /api/finance/square-payment/create-payment-link/
        {
            "invoice_id": 123,
            "redirect_url": "https://example.com/success"
        }
        """
        try:
            redirect_url = request.data.get("redirect_url")

            invoice, error_response = self._resolve_invoice(request)
            if error_response:
                return error_response

            # Create payment link
            payment_link = self.square_service.create_payment_link(
                amount=invoice.total_amount - invoice.amount_paid,
                description=f"Invoice {invoice.invoice_number}",
                currency=invoice.currency,
                metadata={"invoice_id": invoice.id, "invoice_number": invoice.invoice_number},
                redirect_url=redirect_url,
            )

            return Response(
                {
                    "payment_link_url": payment_link["url"],
                    "payment_link_id": payment_link["id"],
                    "amount": float(invoice.total_amount - invoice.amount_paid),
                    "currency": invoice.currency,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="refund-payment")
    def refund_payment(self, request):
        """
        Refund a Square payment.

        POST /api/finance/square-payment/refund-payment/
        {
            "invoice_id": 123,
            "payment_id": "xxx",
            "amount": 100.00,  // Optional, omit for full refund
            "reason": "Customer request"
        }
        """
        try:
            payment_id = request.data.get("payment_id")
            amount = request.data.get("amount")
            reason = request.data.get("reason", "Refund requested")

            if not payment_id:
                return Response(
                    {"error": "invoice_id and payment_id are required"}, status=status.HTTP_400_BAD_REQUEST
                )

            invoice, error_response = self._resolve_invoice(request)
            if error_response:
                return error_response

            # Process refund
            refund_amount = Decimal(amount) if amount else None
            refund = self.square_service.refund_payment(payment_id=payment_id, amount=refund_amount, reason=reason)

            # Update invoice
            refund_amount_dollars = Decimal(refund["amount_money"]["amount"]) / 100
            invoice.amount_paid -= refund_amount_dollars

            if invoice.amount_paid <= 0:
                invoice.status = "refunded"
                invoice.amount_paid = Decimal("0.00")
            elif invoice.amount_paid < invoice.total_amount:
                invoice.status = "partial"

            invoice.save()

            return Response(
                {
                    "message": "Refund processed successfully",
                    "refund_id": refund["id"],
                    "refund_amount": float(refund_amount_dollars),
                    "invoice": InvoiceSerializer(invoice).data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="create-invoice")
    def create_invoice(self, request):
        """
        Create and send a Square invoice.

        POST /api/finance/square-payment/create-invoice/
        {
            "invoice_id": 123
        }
        """
        try:
            invoice, error_response = self._resolve_invoice(request)
            if error_response:
                return error_response

            # Create or get Square customer
            customer_name = invoice.client.company_name
            customer_email = invoice.client.primary_contact_email

            square_customer = self.square_service.create_customer(
                email=customer_email, given_name=customer_name, metadata={"client_id": invoice.client.id}
            )

            # Create Square invoice
            square_invoice = self.square_service.create_invoice(
                customer_id=square_customer["id"],
                line_items=invoice.line_items,
                invoice_number=invoice.invoice_number,
                due_date=invoice.due_date.isoformat() if invoice.due_date else None,
                metadata={"invoice_id": invoice.id},
            )

            # Publish the invoice
            published_invoice = self.square_service.publish_invoice(
                invoice_id=square_invoice["id"], version=square_invoice["version"]
            )

            # Update our invoice
            invoice.stripe_invoice_id = square_invoice["id"]  # Using same field
            invoice.status = "sent"
            from django.utils import timezone

            invoice.sent_at = timezone.now()
            invoice.save()

            return Response(
                {
                    "message": "Invoice sent successfully",
                    "square_invoice_id": square_invoice["id"],
                    "invoice_url": published_invoice.get("public_url", ""),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="payment-status")
    def payment_status(self, request):
        """
        Check Square payment status.

        GET /api/finance/square-payment/payment-status/?payment_id=xxx
        """
        try:
            payment_id = request.query_params.get("payment_id")

            if not payment_id:
                return Response({"error": "payment_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve payment
            payment = self.square_service.retrieve_payment(payment_id)

            return Response(
                {
                    "payment_id": payment["id"],
                    "status": payment["status"],
                    "amount": float(Decimal(payment["amount_money"]["amount"]) / 100),
                    "currency": payment["amount_money"]["currency"],
                    "created_at": payment.get("created_at", ""),
                    "receipt_url": payment.get("receipt_url", ""),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
