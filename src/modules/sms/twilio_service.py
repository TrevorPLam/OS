"""
Twilio SMS Integration Service.

Provides SMS sending, webhook handling, and phone number validation
using the Twilio API.
"""

import logging
import os
import time
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class TwilioService:
    """
    Service for Twilio SMS integration.

    Handles SMS sending, bulk messaging, webhook processing, and phone validation.
    Uses environment variables for Twilio credentials:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN
    """

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2

    def __init__(self):
        """Initialize Twilio service with credentials from environment."""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self._client = None

        if not self.account_sid or not self.auth_token:
            logger.warning(
                "Twilio credentials not found in environment. "
                "Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to enable SMS."
            )

    @property
    def client(self):
        """Lazy-load Twilio client."""
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                logger.error(
                    "Twilio library not installed. Install with: pip install twilio"
                )
                raise ImportError(
                    "Twilio library required. Install with: pip install twilio"
                )
        return self._client

    def send_sms(
        self,
        to_number: str,
        message: str,
        from_number: str,
        media_urls: Optional[List[str]] = None
    ) -> Dict:
        """
        Send a single SMS message.

        Args:
            to_number: Recipient phone number (E.164 format)
            message: Message text
            from_number: Sender phone number (Twilio number)
            media_urls: Optional list of media URLs for MMS

        Returns:
            Dict containing:
                - success (bool): Whether send was successful
                - message_sid (str): Twilio message SID (if successful)
                - status (str): Message status
                - error (str): Error message (if failed)
                - error_code (str): Twilio error code (if failed)

        Raises:
            ValueError: If phone numbers are invalid
        """
        if not self.account_sid or not self.auth_token:
            return {
                'success': False,
                'error': 'Twilio credentials not configured',
                'error_code': 'CREDENTIALS_MISSING'
            }

        # Validate phone numbers
        if not to_number.startswith('+'):
            raise ValueError(f"to_number must be in E.164 format: {to_number}")
        if not from_number.startswith('+'):
            raise ValueError(f"from_number must be in E.164 format: {from_number}")

        # Build message parameters
        message_params = {
            'to': to_number,
            'from_': from_number,
            'body': message,
        }

        if media_urls:
            message_params['media_url'] = media_urls

        # Send with retry logic
        for attempt in range(self.MAX_RETRIES):
            try:
                twilio_message = self.client.messages.create(**message_params)

                logger.info(
                    f"SMS sent successfully: SID={twilio_message.sid}, "
                    f"to={to_number}, status={twilio_message.status}"
                )

                return {
                    'success': True,
                    'message_sid': twilio_message.sid,
                    'status': twilio_message.status,
                    'price': twilio_message.price,
                    'price_currency': twilio_message.price_unit,
                    'error_code': twilio_message.error_code or '',
                    'error_message': twilio_message.error_message or '',
                }

            except Exception as e:
                error_msg = str(e)
                error_code = getattr(e, 'code', 'UNKNOWN_ERROR')

                logger.warning(
                    f"SMS send attempt {attempt + 1}/{self.MAX_RETRIES} failed: "
                    f"{error_msg} (code: {error_code})"
                )

                # Check if error is retryable
                if self._is_retryable_error(e):
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAY_SECONDS * (attempt + 1))
                        continue

                # Final failure
                logger.error(
                    f"SMS send failed after {attempt + 1} attempts: "
                    f"{error_msg} (to={to_number})"
                )

                return {
                    'success': False,
                    'error': error_msg,
                    'error_code': error_code,
                }

        # Should not reach here
        return {
            'success': False,
            'error': 'Maximum retries exceeded',
            'error_code': 'MAX_RETRIES_EXCEEDED'
        }

    def send_bulk_sms(
        self,
        recipients: List[str],
        message: str,
        from_number: str
    ) -> Dict:
        """
        Send SMS to multiple recipients.

        Args:
            recipients: List of recipient phone numbers (E.164 format)
            message: Message text
            from_number: Sender phone number (Twilio number)

        Returns:
            Dict containing:
                - total (int): Total recipients
                - sent (int): Successfully sent
                - failed (int): Failed sends
                - results (List[Dict]): Individual results for each recipient
        """
        results = []
        sent_count = 0
        failed_count = 0

        for to_number in recipients:
            result = self.send_sms(to_number, message, from_number)

            if result['success']:
                sent_count += 1
            else:
                failed_count += 1

            results.append({
                'to_number': to_number,
                **result
            })

        logger.info(
            f"Bulk SMS completed: {sent_count} sent, {failed_count} failed "
            f"out of {len(recipients)} recipients"
        )

        return {
            'total': len(recipients),
            'sent': sent_count,
            'failed': failed_count,
            'results': results
        }

    def handle_webhook(self, request_data: Dict) -> Dict:
        """
        Process Twilio webhook for delivery status or inbound SMS.

        Args:
            request_data: Webhook POST data from Twilio

        Returns:
            Dict containing:
                - webhook_type (str): 'status' or 'inbound'
                - message_sid (str): Twilio message SID
                - status (str): Message status (for status webhooks)
                - from_number (str): Sender number (for inbound)
                - to_number (str): Recipient number (for inbound)
                - body (str): Message body (for inbound)
                - media_urls (List[str]): Media URLs (for inbound MMS)
        """
        message_sid = request_data.get('MessageSid', '')
        message_status = request_data.get('MessageStatus')

        # Determine webhook type
        if message_status:
            # Status callback webhook
            return {
                'webhook_type': 'status',
                'message_sid': message_sid,
                'status': message_status,
                'error_code': request_data.get('ErrorCode', ''),
                'error_message': request_data.get('ErrorMessage', ''),
            }
        else:
            # Inbound SMS webhook
            num_media = int(request_data.get('NumMedia', 0))
            media_urls = []

            for i in range(num_media):
                media_url = request_data.get(f'MediaUrl{i}')
                if media_url:
                    media_urls.append(media_url)

            return {
                'webhook_type': 'inbound',
                'message_sid': message_sid,
                'from_number': request_data.get('From', ''),
                'to_number': request_data.get('To', ''),
                'body': request_data.get('Body', ''),
                'media_urls': media_urls,
            }

    def verify_phone_number(self, phone_number: str) -> Tuple[bool, str]:
        """
        Validate phone number format.

        Args:
            phone_number: Phone number to validate

        Returns:
            Tuple of (is_valid, formatted_number)
        """
        import re

        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone_number)

        # Check E.164 format: +[country code][number]
        # Length should be 7-15 digits after the +
        if not cleaned.startswith('+'):
            # Try adding + if starts with digit
            if cleaned and cleaned[0].isdigit():
                cleaned = '+' + cleaned
            else:
                return False, ''

        # Validate length (E.164: min 7, max 15 digits after +)
        digits_only = cleaned[1:]  # Remove +
        if not digits_only.isdigit():
            return False, ''

        if len(digits_only) < 7 or len(digits_only) > 15:
            return False, ''

        return True, cleaned

    def get_message_status(self, message_sid: str) -> Dict:
        """
        Get current delivery status of a message.

        Args:
            message_sid: Twilio message SID

        Returns:
            Dict containing:
                - success (bool): Whether query was successful
                - status (str): Current message status
                - error_code (str): Error code if failed
                - error_message (str): Error message if failed
                - date_sent (str): ISO timestamp when sent
                - price (str): Message cost
        """
        if not self.account_sid or not self.auth_token:
            return {
                'success': False,
                'error': 'Twilio credentials not configured'
            }

        try:
            message = self.client.messages(message_sid).fetch()

            return {
                'success': True,
                'status': message.status,
                'error_code': message.error_code or '',
                'error_message': message.error_message or '',
                'date_sent': message.date_sent.isoformat() if message.date_sent else '',
                'price': message.price,
                'price_currency': message.price_unit,
            }

        except Exception as e:
            logger.error(f"Failed to fetch message status for {message_sid}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': getattr(e, 'code', 'FETCH_ERROR')
            }

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Check if an error is retryable.

        Retryable errors include:
        - Network errors
        - Rate limiting (429)
        - Temporary Twilio service errors (500, 503)

        Args:
            error: Exception from Twilio

        Returns:
            True if error should be retried
        """
        # Check for Twilio error codes
        error_code = getattr(error, 'code', None)

        # Retryable Twilio error codes
        retryable_codes = [
            20429,  # Too Many Requests (rate limit)
            20500,  # Internal Server Error
            20503,  # Service Unavailable
        ]

        if error_code in retryable_codes:
            return True

        # Check for network-level errors
        error_msg = str(error).lower()
        network_errors = [
            'timeout',
            'connection',
            'network',
            'dns',
        ]

        return any(keyword in error_msg for keyword in network_errors)
