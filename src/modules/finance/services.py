"""
Stripe Service for Payment Processing.

Provides utilities for creating invoices, processing payments, and managing subscriptions.
"""
import stripe
from django.conf import settings
from typing import Optional, Dict, Any
from decimal import Decimal

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """
    Service for interacting with Stripe API.

    Provides methods for payment processing, invoicing, and customer management.
    """

    @staticmethod
    def create_customer(email: str, name: str, metadata: Optional[Dict] = None) -> stripe.Customer:
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
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return customer
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create Stripe customer: {str(e)}")

    @staticmethod
    def create_invoice(
        customer_id: str,
        amount: Decimal,
        description: str,
        metadata: Optional[Dict] = None
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
                customer=customer_id,
                amount=amount_cents,
                currency='usd',
                description=description
            )

            # Create invoice
            invoice = stripe.Invoice.create(
                customer=customer_id,
                auto_advance=True,  # Auto-finalize the invoice
                metadata=metadata or {}
            )

            # Send the invoice
            invoice.send_invoice()

            return invoice
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create Stripe invoice: {str(e)}")

    @staticmethod
    def create_payment_intent(
        amount: Decimal,
        currency: str = 'usd',
        customer_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        payment_method: Optional[str] = None,
    ) -> stripe.PaymentIntent:
        """
        Create a payment intent for one-time payments.

        Args:
            amount: Payment amount in dollars
            currency: Currency code (default: 'usd')
            customer_id: Optional Stripe customer ID
            metadata: Additional metadata

        Returns:
            stripe.PaymentIntent: Created payment intent
        """
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)

            kwargs: Dict[str, Any] = {
                'amount': amount_cents,
                'currency': currency,
                'customer': customer_id,
                'metadata': metadata or {},
                'automatic_payment_methods': {'enabled': True},
            }

            if payment_method:
                kwargs['payment_method'] = payment_method
                kwargs['confirm'] = True
                kwargs['off_session'] = True

            payment_intent = stripe.PaymentIntent.create(**kwargs)

            return payment_intent
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create payment intent: {str(e)}")

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
            raise Exception(f"Failed to retrieve invoice: {str(e)}")

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
            raise Exception(f"Failed to retrieve payment intent: {str(e)}")

    @staticmethod
    def refund_payment(payment_intent_id: str, amount: Optional[Decimal] = None) -> stripe.Refund:
        """
        Refund a payment.

        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Refund amount in dollars (None = full refund)

        Returns:
            stripe.Refund: Refund object
        """
        try:
            refund_params = {'payment_intent': payment_intent_id}

            if amount is not None:
                refund_params['amount'] = int(amount * 100)

            return stripe.Refund.create(**refund_params)
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to refund payment: {str(e)}")
