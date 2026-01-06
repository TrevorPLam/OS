"""
Stripe Service for Payment Processing.

Provides utilities for creating invoices, processing payments, and managing subscriptions.
"""

from decimal import Decimal
from typing import Any

import stripe
from django.conf import settings

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """
    Service for interacting with Stripe API.

    Provides methods for payment processing, invoicing, and customer management.
    """

    @staticmethod
    def create_customer(email: str, name: str, metadata: dict | None = None) -> stripe.Customer:
        """
        Create a Stripe customer.

        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata (e.g., {'client_id': 123})

        Returns:
            stripe.Customer: Created customer object
        """
        try:
            customer = stripe.Customer.create(email=email, name=name, metadata=metadata or {})
            return customer
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create Stripe customer: {str(e)}") from e

    @staticmethod
    def create_invoice(
        customer_id: str, amount: Decimal, description: str, metadata: dict | None = None
    ) -> stripe.Invoice:
        """
        Create and send a Stripe invoice.

        Args:
            customer_id: Stripe customer ID
            amount: Invoice amount in dollars
            description: Invoice description
            metadata: Additional metadata (e.g., {'invoice_id': 123})

        Returns:
            stripe.Invoice: Created invoice object
        """
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)

            # Create invoice item
            stripe.InvoiceItem.create(
                customer=customer_id, amount=amount_cents, currency="usd", description=description
            )

            # Create invoice
            invoice = stripe.Invoice.create(
                customer=customer_id, auto_advance=True, metadata=metadata or {}  # Auto-finalize the invoice
            )

            # Send the invoice
            invoice.send_invoice()

            return invoice
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create Stripe invoice: {str(e)}") from e

    @staticmethod
    def create_payment_intent(
        amount: Decimal,
        currency: str = "usd",
        customer_id: str | None = None,
        metadata: dict | None = None,
        payment_method: str | None = None,
        idempotency_key: str | None = None,
    ) -> stripe.PaymentIntent:
        """
        Create a payment intent for one-time payments.

        Args:
            amount: Payment amount in dollars
            currency: Currency code (default: 'usd')
            customer_id: Optional Stripe customer ID
            metadata: Additional metadata
            payment_method: Optional payment method ID for off-session payments
            idempotency_key: Optional idempotency key to prevent duplicate charges (ASSESS-D4.4)

        Returns:
            stripe.PaymentIntent: Created payment intent

        Meta-commentary:
        - **Current Status:** Idempotency is caller-provided and optional, so retries without a key can double-charge; anti-duplicate guards rely entirely on upstream usage.
        - **Follow-up (T-067):** Attach ledger-aware metadata (invoice IDs, tenant) and persist the returned PaymentIntent ID to enforce reconciliation and dispute tracing.
        - **Assumption:** Automatic payment methods are enabled, but SCA/3DS outcomes are not inspected here; downstream invoice state updates assume webhook success elsewhere.
        - **Limitation:** No concurrency guard exists when multiple workers create intents for the same invoice, and there is no timeout/backoff policy on Stripe API errors.
        """
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)

            kwargs: dict[str, Any] = {
                "amount": amount_cents,
                "currency": currency,
                "customer": customer_id,
                "metadata": metadata or {},
                "automatic_payment_methods": {"enabled": True},
            }

            if payment_method:
                kwargs["payment_method"] = payment_method
                kwargs["confirm"] = True
                kwargs["off_session"] = True

            # SECURITY: Add idempotency key to prevent duplicate charges (ASSESS-D4.4)
            if idempotency_key:
                kwargs["idempotency_key"] = idempotency_key

            payment_intent = stripe.PaymentIntent.create(**kwargs)

            return payment_intent
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create payment intent: {str(e)}") from e

    @staticmethod
    def retrieve_invoice(invoice_id: str) -> stripe.Invoice:
        """
        Retrieve a Stripe invoice.

        Args:
            invoice_id: Stripe invoice ID

        Returns:
            stripe.Invoice: Invoice object
        """
        try:
            return stripe.Invoice.retrieve(invoice_id)
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to retrieve invoice: {str(e)}") from e

    @staticmethod
    def retrieve_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
        """
        Retrieve a payment intent.

        Args:
            payment_intent_id: Stripe payment intent ID

        Returns:
            stripe.PaymentIntent: Payment intent object
        """
        try:
            return stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to retrieve payment intent: {str(e)}") from e

    @staticmethod
    def refund_payment(payment_intent_id: str, amount: Decimal | None = None) -> stripe.Refund:
        """
        Refund a payment.

        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Refund amount in dollars (None = full refund)

        Returns:
            stripe.Refund: Refund object
        """
        try:
            refund_params = {"payment_intent": payment_intent_id}

            if amount is not None:
                refund_params["amount"] = int(amount * 100)

            return stripe.Refund.create(**refund_params)
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to refund payment: {str(e)}") from e

    @staticmethod
    def create_checkout_session(
        amount: Decimal,
        currency: str = "usd",
        success_url: str = None,
        cancel_url: str = None,
        metadata: dict | None = None,
        customer_email: str | None = None,
        invoice_number: str | None = None,
    ) -> stripe.checkout.Session:
        """
        Create a Stripe Checkout session for invoice payment.

        This creates a hosted payment page that clients can use to pay invoices.
        The session URL should be returned to the client for redirect.

        Args:
            amount: Payment amount in dollars
            currency: Currency code (default: 'usd')
            success_url: URL to redirect to after successful payment
            cancel_url: URL to redirect to if payment is cancelled
            metadata: Additional metadata (should include invoice_id)
            customer_email: Pre-fill customer email
            invoice_number: Invoice number for display

        Returns:
            stripe.checkout.Session: Created checkout session

        Raises:
            Exception: If checkout session creation fails
        """
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)

            # Build session parameters
            session_params = {
                "payment_method_types": ["card"],
                "line_items": [
                    {
                        "price_data": {
                            "currency": currency,
                            "unit_amount": amount_cents,
                            "product_data": {
                                "name": f"Invoice {invoice_number}" if invoice_number else "Invoice Payment",
                                "description": f"Payment for invoice {invoice_number}" if invoice_number else "Invoice payment",
                            },
                        },
                        "quantity": 1,
                    }
                ],
                "mode": "payment",
                "success_url": success_url or settings.STRIPE_CHECKOUT_SUCCESS_URL,
                "cancel_url": cancel_url or settings.STRIPE_CHECKOUT_CANCEL_URL,
                "metadata": metadata or {},
            }

            # Optionally pre-fill customer email
            if customer_email:
                session_params["customer_email"] = customer_email

            # Create the checkout session
            session = stripe.checkout.Session.create(**session_params)

            return session

        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create checkout session: {str(e)}") from e
