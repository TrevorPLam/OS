"""
Square Service for Payment Processing (PAY-2).

Provides utilities for creating payments, managing terminals, and processing transactions.
Alternative to Stripe for firms that prefer Square (especially for in-person payments).
"""

from decimal import Decimal
from typing import Any
from uuid import uuid4

from django.conf import settings


class SquareService:
    """
    Service for interacting with Square API.

    Provides methods for payment processing, customer management, and terminal operations.
    """

    def __init__(self):
        """Initialize Square client with API credentials."""
        from square.client import Client as SquareClient

        self.client = SquareClient(
            access_token=settings.SQUARE_ACCESS_TOKEN,
            environment=settings.SQUARE_ENVIRONMENT,  # 'sandbox' or 'production'
        )

    def create_customer(
        self, email: str, given_name: str, family_name: str = "", company_name: str = "", metadata: dict | None = None
    ) -> dict:
        """
        Create a Square customer.

        Args:
            email: Customer email
            given_name: Customer first name
            family_name: Customer last name
            company_name: Company name
            metadata: Additional reference data

        Returns:
            dict: Created customer object with customer_id

        Raises:
            Exception: If customer creation fails
        """
        try:
            body = {
                "idempotency_key": str(uuid4()),
                "given_name": given_name,
                "email_address": email,
            }

            if family_name:
                body["family_name"] = family_name

            if company_name:
                body["company_name"] = company_name

            if metadata:
                body["reference_id"] = str(metadata.get("client_id", ""))
                body["note"] = str(metadata.get("note", ""))

            result = self.client.customers.create_customer(body=body)

            if result.is_success():
                return result.body["customer"]
            elif result.is_error():
                errors = result.errors
                raise Exception(f"Failed to create Square customer: {errors}")

        except Exception as e:
            raise Exception(f"Square customer creation error: {str(e)}") from e

    def create_payment(
        self,
        amount: Decimal,
        currency: str = "USD",
        customer_id: str | None = None,
        source_id: str | None = None,
        metadata: dict | None = None,
        idempotency_key: str | None = None,
        autocomplete: bool = True,
    ) -> dict:
        """
        Create a Square payment.

        Args:
            amount: Payment amount in dollars
            currency: Currency code (default: 'USD')
            customer_id: Optional Square customer ID
            source_id: Payment source ID (card nonce or saved card ID)
            metadata: Additional metadata (e.g., {'invoice_id': 123})
            idempotency_key: Idempotency key to prevent duplicate charges
            autocomplete: Auto-complete payment (default: True)

        Returns:
            dict: Created payment object

        Raises:
            Exception: If payment creation fails
        """
        try:
            # Convert amount to cents (Square uses smallest currency unit)
            amount_cents = int(amount * 100)

            body = {
                "idempotency_key": idempotency_key or str(uuid4()),
                "amount_money": {"amount": amount_cents, "currency": currency},
                "autocomplete": autocomplete,
            }

            if source_id:
                body["source_id"] = source_id

            if customer_id:
                body["customer_id"] = customer_id

            if metadata:
                # Square doesn't have metadata, use note and reference_id
                body["note"] = f"Invoice: {metadata.get('invoice_number', '')}"
                body["reference_id"] = str(metadata.get("invoice_id", ""))

            result = self.client.payments.create_payment(body=body)

            if result.is_success():
                return result.body["payment"]
            elif result.is_error():
                errors = result.errors
                raise Exception(f"Failed to create Square payment: {errors}")

        except Exception as e:
            raise Exception(f"Square payment creation error: {str(e)}") from e

    def create_payment_link(
        self,
        amount: Decimal,
        description: str,
        currency: str = "USD",
        metadata: dict | None = None,
        redirect_url: str | None = None,
    ) -> dict:
        """
        Create a Square payment link for online checkout.

        Args:
            amount: Payment amount in dollars
            description: Payment description
            currency: Currency code (default: 'USD')
            metadata: Additional metadata
            redirect_url: URL to redirect after payment

        Returns:
            dict: Payment link object with url

        Raises:
            Exception: If payment link creation fails
        """
        try:
            amount_cents = int(amount * 100)

            body = {
                "idempotency_key": str(uuid4()),
                "quick_pay": {
                    "name": description,
                    "price_money": {"amount": amount_cents, "currency": currency},
                    "location_id": settings.SQUARE_LOCATION_ID,
                },
            }

            if redirect_url:
                body["checkout_options"] = {"redirect_url": redirect_url}

            if metadata:
                # Add invoice reference
                body["quick_pay"]["name"] = f"{description} - Invoice: {metadata.get('invoice_number', '')}"

            result = self.client.checkout.create_payment_link(body=body)

            if result.is_success():
                return result.body["payment_link"]
            elif result.is_error():
                errors = result.errors
                raise Exception(f"Failed to create Square payment link: {errors}")

        except Exception as e:
            raise Exception(f"Square payment link creation error: {str(e)}") from e

    def retrieve_payment(self, payment_id: str) -> dict:
        """
        Retrieve a Square payment.

        Args:
            payment_id: Square payment ID

        Returns:
            dict: Payment object

        Raises:
            Exception: If retrieval fails
        """
        try:
            result = self.client.payments.get_payment(payment_id=payment_id)

            if result.is_success():
                return result.body["payment"]
            elif result.is_error():
                errors = result.errors
                raise Exception(f"Failed to retrieve Square payment: {errors}")

        except Exception as e:
            raise Exception(f"Square payment retrieval error: {str(e)}") from e

    def refund_payment(self, payment_id: str, amount: Decimal | None = None, reason: str = "") -> dict:
        """
        Refund a Square payment.

        Args:
            payment_id: Square payment ID to refund
            amount: Refund amount in dollars (None = full refund)
            reason: Reason for refund

        Returns:
            dict: Refund object

        Raises:
            Exception: If refund fails
        """
        try:
            body = {
                "idempotency_key": str(uuid4()),
                "payment_id": payment_id,
            }

            if amount is not None:
                amount_cents = int(amount * 100)
                body["amount_money"] = {"amount": amount_cents, "currency": "USD"}

            if reason:
                body["reason"] = reason

            result = self.client.refunds.refund_payment(body=body)

            if result.is_success():
                return result.body["refund"]
            elif result.is_error():
                errors = result.errors
                raise Exception(f"Failed to refund Square payment: {errors}")

        except Exception as e:
            raise Exception(f"Square refund error: {str(e)}") from e

    def list_customer_cards(self, customer_id: str) -> list[dict]:
        """
        List saved payment methods for a customer.

        Args:
            customer_id: Square customer ID

        Returns:
            list: List of card objects

        Raises:
            Exception: If listing fails
        """
        try:
            result = self.client.cards.list_cards(customer_id=customer_id)

            if result.is_success():
                return result.body.get("cards", [])
            elif result.is_error():
                errors = result.errors
                raise Exception(f"Failed to list Square cards: {errors}")

        except Exception as e:
            raise Exception(f"Square card listing error: {str(e)}") from e

    def create_invoice(
        self,
        customer_id: str,
        line_items: list[dict],
        invoice_number: str,
        due_date: str = None,
        metadata: dict | None = None,
    ) -> dict:
        """
        Create a Square invoice.

        Args:
            customer_id: Square customer ID
            line_items: List of line items [{"name": "Service", "quantity": "1", "amount": "1000"}]
            invoice_number: Invoice number
            due_date: Due date (ISO format)
            metadata: Additional metadata

        Returns:
            dict: Created invoice object

        Raises:
            Exception: If invoice creation fails
        """
        try:
            # Format line items for Square
            square_line_items = []
            for item in line_items:
                square_line_items.append(
                    {
                        "name": item.get("name", "Service"),
                        "quantity": str(item.get("quantity", 1)),
                        "base_price_money": {
                            "amount": int(Decimal(str(item.get("amount", 0))) * 100),
                            "currency": "USD",
                        },
                    }
                )

            body = {
                "invoice": {
                    "location_id": settings.SQUARE_LOCATION_ID,
                    "order_id": metadata.get("order_id") if metadata else None,
                    "primary_recipient": {"customer_id": customer_id},
                    "payment_requests": [
                        {
                            "request_type": "BALANCE",
                            "due_date": due_date,
                        }
                    ],
                    "invoice_number": invoice_number,
                }
            }

            result = self.client.invoices.create_invoice(body=body)

            if result.is_success():
                return result.body["invoice"]
            elif result.is_error():
                errors = result.errors
                raise Exception(f"Failed to create Square invoice: {errors}")

        except Exception as e:
            raise Exception(f"Square invoice creation error: {str(e)}") from e

    def publish_invoice(self, invoice_id: str, version: int) -> dict:
        """
        Publish (send) a Square invoice.

        Args:
            invoice_id: Square invoice ID
            version: Invoice version for optimistic concurrency

        Returns:
            dict: Published invoice object

        Raises:
            Exception: If publishing fails
        """
        try:
            body = {"version": version, "idempotency_key": str(uuid4())}

            result = self.client.invoices.publish_invoice(invoice_id=invoice_id, body=body)

            if result.is_success():
                return result.body["invoice"]
            elif result.is_error():
                errors = result.errors
                raise Exception(f"Failed to publish Square invoice: {errors}")

        except Exception as e:
            raise Exception(f"Square invoice publishing error: {str(e)}") from e
