"""
Payment Processing Views using Stripe.

TIER 2.5: Payments can be accessed by both firm users and portal users.
Portal users can only pay invoices for their own client.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from modules.clients.models import ClientPortalUser
from modules.clients.permissions import IsPortalUserOrFirmUser
from modules.firm.utils import FirmScopingError, get_request_firm
from modules.finance.models import Invoice
from modules.finance.services import StripeService

from .serializers import InvoiceSerializer


class PaymentViewSet(viewsets.ViewSet):
    """
    ViewSet for payment processing with Stripe.

    TIER 2.5: Both firm users and portal users can access payments.
    Portal users are scoped to their own client's invoices only.
    """

    permission_classes = [IsAuthenticated, IsPortalUserOrFirmUser]

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
        """Return a firm-scoped invoice or an error response."""
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

    @action(detail=False, methods=["post"])
    def create_payment_intent(self, request):
        """
        Create a Stripe payment intent for an invoice.

        POST /api/finance/payment/create_payment_intent/
        {
            "invoice_id": 123,
            "customer_email": "client@example.com"
        }
        """
        try:
            customer_email = request.data.get("customer_email")

            invoice, error_response = self._resolve_invoice(request)
            if error_response:
                return error_response

            # Create or get Stripe customer
            customer_name = invoice.client.company_name if hasattr(invoice, "client") else "Customer"
            stripe_customer = StripeService.create_customer(
                email=customer_email or invoice.client.primary_contact_email,
                name=customer_name,
                metadata={"invoice_id": invoice.id, "client_id": invoice.client.id},
            )

            # Create payment intent
            payment_intent = StripeService.create_payment_intent(
                amount=invoice.total_amount - invoice.amount_paid,
                currency=invoice.currency.lower(),
                customer_id=stripe_customer.id,
                metadata={"invoice_id": invoice.id, "invoice_number": invoice.invoice_number},
            )

            # Update invoice with Stripe invoice ID
            if not invoice.stripe_invoice_id:
                invoice.stripe_invoice_id = payment_intent.id
                invoice.save()

            return Response(
                {
                    "client_secret": payment_intent.client_secret,
                    "payment_intent_id": payment_intent.id,
                    "amount": float(invoice.total_amount - invoice.amount_paid),
                    "currency": invoice.currency,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def confirm_payment(self, request):
        """
        Confirm a payment and update invoice status.

        POST /api/finance/payment/confirm_payment/
        {
            "invoice_id": 123,
            "payment_intent_id": "pi_xxx",
            "amount_paid": 1000.00
        }
        """
        try:
            payment_intent_id = request.data.get("payment_intent_id")
            amount_paid = request.data.get("amount_paid")

            invoice, error_response = self._resolve_invoice(request)
            if error_response:
                return error_response

            # Verify payment with Stripe
            payment_intent = StripeService.retrieve_payment_intent(payment_intent_id)

            if payment_intent.status == "succeeded":
                # Update invoice
                invoice.amount_paid += float(amount_paid)

                if invoice.amount_paid >= invoice.total_amount:
                    invoice.status = "paid"
                    from django.utils import timezone

                    invoice.paid_date = timezone.now().date()
                else:
                    invoice.status = "partial"

                invoice.save()

                return Response(
                    {"message": "Payment confirmed successfully", "invoice": InvoiceSerializer(invoice).data},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": f"Payment status is {payment_intent.status}"}, status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def send_invoice(self, request):
        """
        Create and send a Stripe invoice.

        POST /api/finance/payment/send_invoice/
        {
            "invoice_id": 123
        }
        """
        try:
            invoice, error_response = self._resolve_invoice(request)
            if error_response:
                return error_response

            # Create or get Stripe customer
            customer_name = invoice.client.company_name
            customer_email = invoice.client.primary_contact_email

            stripe_customer = StripeService.create_customer(
                email=customer_email, name=customer_name, metadata={"client_id": invoice.client.id}
            )

            # Create Stripe invoice
            stripe_invoice = StripeService.create_invoice(
                customer_id=stripe_customer.id,
                amount=invoice.total_amount,
                description=f"Invoice {invoice.invoice_number}",
                metadata={"invoice_id": invoice.id, "invoice_number": invoice.invoice_number},
            )

            # Update our invoice
            invoice.stripe_invoice_id = stripe_invoice.id
            invoice.status = "sent"
            from django.utils import timezone

            invoice.sent_at = timezone.now()
            invoice.save()

            return Response(
                {
                    "message": "Invoice sent successfully",
                    "stripe_invoice_id": stripe_invoice.id,
                    "invoice_url": stripe_invoice.hosted_invoice_url,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
