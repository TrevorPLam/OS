"""
Accounting Sync Service.

Handles bidirectional synchronization between UBOS and
accounting systems (QuickBooks Online, Xero).
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.utils import timezone
from django.db import transaction

from modules.finance.models import Invoice
from modules.clients.models import Client
from .models import (
    AccountingOAuthConnection,
    InvoiceSyncMapping,
    CustomerSyncMapping,
)
from .quickbooks_service import QuickBooksService
from .xero_service import XeroService

logger = logging.getLogger(__name__)


class AccountingSyncService:
    """
    Service for synchronizing data with accounting systems.

    Handles:
    - Invoice sync (push to accounting system)
    - Payment sync (pull from accounting system)
    - Customer/Contact sync (bidirectional)
    """

    def __init__(self, connection: AccountingOAuthConnection):
        """
        Initialize sync service for a specific connection.

        Args:
            connection: AccountingOAuthConnection instance
        """
        self.connection = connection
        self.firm = connection.firm

        # Initialize provider service
        if connection.provider == 'quickbooks':
            self.service = QuickBooksService()
        elif connection.provider == 'xero':
            self.service = XeroService()
        else:
            raise ValueError(f"Unsupported provider: {connection.provider}")

    def _ensure_fresh_token(self) -> bool:
        """
        Ensure connection has a fresh access token.

        Returns:
            True if token is fresh or refreshed successfully
        """
        if not self.connection.needs_refresh():
            return True

        # Refresh token
        result = self.service.refresh_token(self.connection.refresh_token)

        if result.get('success'):
            # Update connection with new tokens
            self.connection.access_token = result['access_token']
            if result.get('refresh_token'):
                self.connection.refresh_token = result['refresh_token']
            
            expires_in = result.get('expires_in', 3600)
            self.connection.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            self.connection.status = 'active'
            self.connection.save()
            return True
        else:
            # Token refresh failed
            self.connection.status = 'expired'
            self.connection.error_message = result.get('error', 'Token refresh failed')
            self.connection.save()
            logger.error(f"Token refresh failed for {self.connection}: {result.get('error')}")
            return False

    def sync_customer(self, client: Client) -> Dict:
        """
        Sync a customer/contact to accounting system.

        Args:
            client: Client instance to sync

        Returns:
            Dict with success status and details
        """
        if not self._ensure_fresh_token():
            return {'success': False, 'error': 'Token refresh failed'}

        try:
            # Check if mapping exists
            mapping = CustomerSyncMapping.objects.filter(
                connection=self.connection,
                client=client
            ).first()

            customer_data = self._build_customer_data(client)

            if mapping:
                # Update existing customer
                if self.connection.provider == 'quickbooks':
                    result = self.service.update_customer(
                        self.connection.access_token,
                        self.connection.provider_company_id,
                        mapping.external_id,
                        customer_data
                    )
                elif self.connection.provider == 'xero':
                    result = self.service.update_contact(
                        self.connection.access_token,
                        self.connection.provider_company_id,
                        mapping.external_id,
                        customer_data
                    )
            else:
                # Create new customer
                if self.connection.provider == 'quickbooks':
                    result = self.service.create_customer(
                        self.connection.access_token,
                        self.connection.provider_company_id,
                        customer_data
                    )
                elif self.connection.provider == 'xero':
                    result = self.service.create_contact(
                        self.connection.access_token,
                        self.connection.provider_company_id,
                        customer_data
                    )

            if result.get('success'):
                # Extract customer ID from response
                if self.connection.provider == 'quickbooks':
                    external_id = result['data']['Customer']['Id']
                    external_name = result['data']['Customer']['DisplayName']
                elif self.connection.provider == 'xero':
                    external_id = result['data']['Contacts'][0]['ContactID']
                    external_name = result['data']['Contacts'][0]['Name']

                # Create or update mapping
                if mapping:
                    mapping.external_id = external_id
                    mapping.external_name = external_name
                    mapping.sync_status = 'synced'
                    mapping.sync_error = ''
                    mapping.save()
                else:
                    mapping = CustomerSyncMapping.objects.create(
                        firm=self.firm,
                        connection=self.connection,
                        client=client,
                        external_id=external_id,
                        external_name=external_name,
                        sync_status='synced'
                    )

                self.connection.last_customer_sync_at = timezone.now()
                self.connection.save()

                return {'success': True, 'mapping': mapping}
            else:
                # Sync failed
                if mapping:
                    mapping.sync_status = 'error'
                    mapping.sync_error = result.get('error', 'Unknown error')
                    mapping.save()

                return {'success': False, 'error': result.get('error')}

        except Exception as e:
            logger.exception(f"Customer sync error for {client}: {e}")
            return {'success': False, 'error': str(e)}

    def sync_invoice(self, invoice: Invoice) -> Dict:
        """
        Sync an invoice to accounting system.

        Args:
            invoice: Invoice instance to sync

        Returns:
            Dict with success status and details

        Meta-commentary:
        - **Current Status:** Invoice sync is push-only and relies on last-write-wins when payment pulls update invoice status, with no field-level conflict resolution between local edits and provider-side changes.
        - **Follow-up (T-067):** Add bidirectional invoice merge with per-field precedence rules plus sync-level locking to avoid concurrent push/pull cycles trampling each other.
        - **Assumption:** InvoiceSyncMapping entries remain fresh; retrying a failed push reuses stale external IDs without verifying remote deletion, voiding, or renumbering.
        - **Limitation:** Token freshness and mapping writes are not wrapped in the same transaction, and there is no deduplication lock around the sync, so partial failures can leave invoices flagged as synced while a competing worker pushes divergent versions.
        """
        if not self._ensure_fresh_token():
            return {'success': False, 'error': 'Token refresh failed'}

        try:
            # Ensure customer is synced first
            customer_mapping = CustomerSyncMapping.objects.filter(
                connection=self.connection,
                client=invoice.client
            ).first()

            if not customer_mapping:
                # Sync customer first
                customer_result = self.sync_customer(invoice.client)
                if not customer_result.get('success'):
                    return {'success': False, 'error': 'Customer sync failed'}
                customer_mapping = customer_result['mapping']

            # Check if invoice mapping exists
            mapping = InvoiceSyncMapping.objects.filter(
                connection=self.connection,
                invoice=invoice
            ).first()

            invoice_data = self._build_invoice_data(invoice, customer_mapping.external_id)

            # Only create new invoices, don't update (accounting best practice)
            if not mapping:
                if self.connection.provider == 'quickbooks':
                    result = self.service.create_invoice(
                        self.connection.access_token,
                        self.connection.provider_company_id,
                        invoice_data
                    )
                elif self.connection.provider == 'xero':
                    result = self.service.create_invoice(
                        self.connection.access_token,
                        self.connection.provider_company_id,
                        invoice_data
                    )

                if result.get('success'):
                    # Extract invoice ID from response
                    if self.connection.provider == 'quickbooks':
                        external_id = result['data']['Invoice']['Id']
                        external_number = result['data']['Invoice'].get('DocNumber', '')
                    elif self.connection.provider == 'xero':
                        external_id = result['data']['Invoices'][0]['InvoiceID']
                        external_number = result['data']['Invoices'][0].get('InvoiceNumber', '')

                    # Create mapping
                    mapping = InvoiceSyncMapping.objects.create(
                        firm=self.firm,
                        connection=self.connection,
                        invoice=invoice,
                        external_id=external_id,
                        external_number=external_number,
                        sync_status='synced'
                    )

                    self.connection.last_invoice_sync_at = timezone.now()
                    self.connection.save()

                    return {'success': True, 'mapping': mapping}
                else:
                    return {'success': False, 'error': result.get('error')}
            else:
                # Already synced
                return {'success': True, 'mapping': mapping, 'already_synced': True}

        except Exception as e:
            logger.exception(f"Invoice sync error for {invoice}: {e}")
            return {'success': False, 'error': str(e)}

    def sync_payments(self, since_date: Optional[datetime] = None) -> Dict:
        """
        Pull payments from accounting system and update invoice status.

        Args:
            since_date: Optional date to filter payments

        Returns:
            Dict with success status and payment count
        """
        if not self._ensure_fresh_token():
            return {'success': False, 'error': 'Token refresh failed'}

        try:
            # Fetch payments from accounting system
            if self.connection.provider == 'quickbooks':
                result = self.service.query_payments(
                    self.connection.access_token,
                    self.connection.provider_company_id,
                    since_date
                )
            elif self.connection.provider == 'xero':
                result = self.service.get_payments(
                    self.connection.access_token,
                    self.connection.provider_company_id,
                    since_date
                )

            if result.get('success'):
                # Process payments
                payment_count = self._process_payments(result['data'])

                self.connection.last_payment_sync_at = timezone.now()
                self.connection.save()

                return {'success': True, 'payment_count': payment_count}
            else:
                return {'success': False, 'error': result.get('error')}

        except Exception as e:
            logger.exception(f"Payment sync error: {e}")
            return {'success': False, 'error': str(e)}

    def _build_customer_data(self, client: Client) -> Dict:
        """Build customer/contact data for accounting system."""
        if self.connection.provider == 'quickbooks':
            return {
                'DisplayName': client.name or client.email,
                'PrimaryEmailAddr': {'Address': client.email} if client.email else None,
                'PrimaryPhone': {'FreeFormNumber': getattr(client, 'phone', '')} if hasattr(client, 'phone') else None,
            }
        elif self.connection.provider == 'xero':
            return {
                'Name': client.name or client.email,
                'EmailAddress': client.email if client.email else '',
            }

    def _build_invoice_data(self, invoice: Invoice, customer_id: str) -> Dict:
        """Build invoice data for accounting system."""
        if self.connection.provider == 'quickbooks':
            line_items = [{
                'Amount': float(invoice.total_amount),
                'DetailType': 'SalesItemLineDetail',
                'SalesItemLineDetail': {
                    'Qty': 1,
                    'UnitPrice': float(invoice.total_amount),
                    'ItemRef': {'value': '1'},  # Services item (placeholder)
                },
                'Description': invoice.notes or 'Professional Services',
            }]

            return {
                'CustomerRef': {'value': customer_id},
                'Line': line_items,
                'DueDate': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else None,
            }
        elif self.connection.provider == 'xero':
            line_items = [{
                'Description': invoice.notes or 'Professional Services',
                'Quantity': 1,
                'UnitAmount': float(invoice.total_amount),
                'AccountCode': '200',  # Sales account (placeholder)
            }]

            return {
                'Type': 'ACCREC',  # Accounts Receivable
                'Contact': {'ContactID': customer_id},
                'LineItems': line_items,
                'Date': invoice.created_at.strftime('%Y-%m-%d'),
                'DueDate': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else None,
                'Status': 'AUTHORISED',
            }

    def _process_payments(self, payment_data: Dict) -> int:
        """Process payments from accounting system and update invoices."""
        payment_count = 0

        # Extract payments based on provider
        if self.connection.provider == 'quickbooks':
            payments = payment_data.get('QueryResponse', {}).get('Payment', [])
        elif self.connection.provider == 'xero':
            payments = payment_data.get('Payments', [])

        for payment in payments:
            try:
                # Extract payment details based on provider
                if self.connection.provider == 'quickbooks':
                    # QuickBooks payment processing
                    for line in payment.get('Line', []):
                        linked_txn = line.get('LinkedTxn', [])
                        for txn in linked_txn:
                            if txn.get('TxnType') == 'Invoice':
                                invoice_id = txn.get('TxnId')
                                self._update_invoice_payment_status(invoice_id)
                                payment_count += 1

                elif self.connection.provider == 'xero':
                    # Xero payment processing
                    invoice_ref = payment.get('Invoice', {}).get('InvoiceID')
                    if invoice_ref:
                        self._update_invoice_payment_status(invoice_ref)
                        payment_count += 1

            except Exception as e:
                logger.error(f"Error processing payment: {e}")
                continue

        return payment_count

    def _update_invoice_payment_status(self, external_invoice_id: str):
        """Update invoice payment status based on external payment."""
        try:
            mapping = InvoiceSyncMapping.objects.filter(
                connection=self.connection,
                external_id=external_invoice_id
            ).first()

            if mapping and mapping.invoice:
                # Update invoice status to paid if not already
                if mapping.invoice.status not in ['paid', 'partial']:
                    mapping.invoice.status = 'paid'
                    mapping.invoice.paid_date = timezone.now()
                    mapping.invoice.save()
                    logger.info(f"Updated invoice {mapping.invoice} to paid status")

        except Exception as e:
            logger.error(f"Error updating invoice payment status: {e}")
