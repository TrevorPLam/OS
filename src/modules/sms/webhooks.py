"""
SMS Webhook Handlers.

Processes Twilio webhooks for delivery status updates and inbound SMS messages.
"""

import logging
import os
import re
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import (
    SMSMessage,
    SMSConversation,
    SMSOptOut,
    SMSPhoneNumber,
    SMSCampaign,
)
from .twilio_service import TwilioService

logger = logging.getLogger(__name__)

# Opt-out keywords (case-insensitive)
OPT_OUT_KEYWORDS = [
    'stop',
    'stopall',
    'unsubscribe',
    'cancel',
    'end',
    'quit',
]


def _verify_twilio_signature(request):
    """
    Verify Twilio webhook signature (CONST-3 compliance).
    
    Validates that the request is genuinely from Twilio by checking
    the X-Twilio-Signature header against the expected signature.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    if not auth_token:
        logger.warning("TWILIO_AUTH_TOKEN not configured, skipping signature verification")
        return True  # Allow in development mode
    
    try:
        from twilio.request_validator import RequestValidator
        
        validator = RequestValidator(auth_token)
        
        # Get the signature from headers
        signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')
        
        # Construct the full URL
        url = request.build_absolute_uri()
        
        # Get POST parameters as dict
        params = request.POST.dict()
        
        # Validate the signature
        is_valid = validator.validate(url, params, signature)
        
        if not is_valid:
            logger.warning(f"Invalid Twilio signature for URL: {url}")
        
        return is_valid
        
    except ImportError:
        logger.error("Twilio library not installed, cannot verify signature")
        return False
    except Exception as e:
        logger.error(f"Error verifying Twilio signature: {e}", exc_info=True)
        return False


@csrf_exempt
@require_POST
def twilio_status_webhook(request):
    """
    Handle Twilio delivery status webhook (SEC-1: Idempotency tracking).

    Updates message status when delivery status changes.

    Expected parameters from Twilio:
    - MessageSid: Twilio message ID
    - MessageStatus: New status (delivered, failed, undelivered, etc.)
    - ErrorCode: Error code if failed (optional)
    - ErrorMessage: Error description if failed (optional)
    
    SEC-1: Implements idempotency by checking SMSWebhookEvent before processing.
    """
    from django.db import IntegrityError
    from modules.sms.models import SMSWebhookEvent
    
    # CONST-3: Verify Twilio webhook signature
    if not _verify_twilio_signature(request):
        logger.error("Invalid Twilio signature for status webhook")
        return HttpResponse("Forbidden - Invalid signature", status=403)
    
    try:
        # Parse webhook data
        twilio_service = TwilioService()
        webhook_data = twilio_service.handle_webhook(request.POST.dict())

        if webhook_data['webhook_type'] != 'status':
            logger.warning("Status webhook received non-status data")
            return HttpResponse(status=400)

        message_sid = webhook_data['message_sid']
        new_status = webhook_data['status']

        logger.info(f"Status webhook: {message_sid} -> {new_status}")

        # Find message by provider SID
        message = None
        firm = None
        try:
            message = SMSMessage.objects.select_related('firm').get(provider_message_sid=message_sid)
            firm = message.firm
        except SMSMessage.DoesNotExist:
            logger.warning(f"Message not found for SID: {message_sid}")
            return HttpResponse(status=404)

        # SEC-1: Check for duplicate webhook event
        # Try to create webhook event record atomically
        try:
            with transaction.atomic():
                # Try to create webhook event log
                webhook_event = SMSWebhookEvent.objects.create(
                    firm=firm,
                    twilio_message_sid=message_sid,
                    event_type='status_callback',
                    webhook_type='status',
                    message_status=new_status,
                    sms_message=message,
                    event_data=webhook_data,
                )
                
        except IntegrityError:
            # Duplicate webhook delivery - event already processed
            logger.info(f"Duplicate Twilio status webhook received: {message_sid} (status)")
            # Return 200 OK without reprocessing (SEC-1 acceptance criteria)
            return HttpResponse(status=200)

        # Update message status
        with transaction.atomic():
            # Map Twilio status to our status
            status_mapping = {
                'queued': 'queued',
                'sending': 'sending',
                'sent': 'sent',
                'delivered': 'delivered',
                'failed': 'failed',
                'undelivered': 'undelivered',
            }

            message.status = status_mapping.get(new_status, new_status)
            message.provider_status = new_status

            if new_status == 'delivered':
                message.delivered_at = timezone.now()

            if webhook_data.get('error_code'):
                message.error_code = webhook_data['error_code']
                message.error_message = webhook_data.get('error_message', '')

            message.save(update_fields=[
                'status',
                'provider_status',
                'delivered_at',
                'error_code',
                'error_message',
            ])

            # Update campaign stats if part of campaign
            if message.campaign:
                _update_campaign_stats(message.campaign)
            
            # Mark webhook event as successfully processed
            webhook_event.processed_successfully = True
            webhook_event.save(update_fields=['processed_successfully'])

        logger.info(f"Updated message {message.id} status to {message.status}")

        return HttpResponse(status=200)

    except Exception as e:
        logger.error(f"Error processing status webhook: {e}", exc_info=True)
        return HttpResponse(status=500)


@csrf_exempt
@require_POST
def twilio_inbound_webhook(request):
    """
    Handle Twilio inbound SMS webhook.

    Processes incoming SMS messages, creates conversation threads,
    and checks for opt-out keywords.

    Expected parameters from Twilio:
    - MessageSid: Twilio message ID
    - From: Sender phone number
    - To: Recipient phone number (our number)
    - Body: Message text
    - NumMedia: Number of media attachments
    - MediaUrl0, MediaUrl1, ...: Media URLs (if MMS)
    """
    # CONST-3: Verify Twilio webhook signature
    if not _verify_twilio_signature(request):
        logger.error("Invalid Twilio signature for inbound webhook")
        return HttpResponse("Forbidden - Invalid signature", status=403)
    
    from django.db import IntegrityError
    from modules.sms.models import SMSWebhookEvent
    
    try:
        # Parse webhook data
        twilio_service = TwilioService()
        webhook_data = twilio_service.handle_webhook(request.POST.dict())

        if webhook_data['webhook_type'] != 'inbound':
            logger.warning("Inbound webhook received non-inbound data")
            return HttpResponse(status=400)

        from_number = webhook_data['from_number']
        to_number = webhook_data['to_number']
        message_body = webhook_data['body']
        message_sid = webhook_data['message_sid']
        media_urls = webhook_data.get('media_urls', [])

        logger.info(f"Inbound SMS: {from_number} -> {to_number}: {message_body[:50]}")

        # Find our phone number
        try:
            our_phone = SMSPhoneNumber.objects.get(phone_number=to_number)
        except SMSPhoneNumber.DoesNotExist:
            logger.warning(f"Phone number not found: {to_number}")
            return HttpResponse(status=404)

        firm = our_phone.firm

        # SEC-1: Check for duplicate webhook event
        # Try to create webhook event record atomically
        try:
            with transaction.atomic():
                # Try to create webhook event log
                webhook_event = SMSWebhookEvent.objects.create(
                    firm=firm,
                    twilio_message_sid=message_sid,
                    event_type='inbound_message',
                    webhook_type='inbound',
                    message_status='received',
                    event_data=webhook_data,
                )
                
        except IntegrityError:
            # Duplicate webhook delivery - event already processed
            logger.info(f"Duplicate Twilio inbound webhook received: {message_sid} (inbound)")
            # Return 200 OK without reprocessing (SEC-1 acceptance criteria)
            return HttpResponse(
                '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
                content_type='text/xml',
                status=200
            )

        # Check for opt-out keywords
        is_opt_out = _check_opt_out_keywords(message_body)

        with transaction.atomic():
            # Get or create conversation
            conversation, created = SMSConversation.objects.get_or_create(
                firm=firm,
                our_number=our_phone,
                their_number=from_number,
                defaults={
                    'status': 'active',
                }
            )

            if created:
                logger.info(f"Created new conversation: {conversation.id}")

            # Create message record
            sms_message = SMSMessage.objects.create(
                firm=firm,
                from_number=None,  # Inbound, so from_number is their number
                to_number=from_number,  # Store in to_number for consistency
                direction='inbound',
                message_body=message_body,
                media_urls=media_urls,
                status='received',
                provider_message_sid=message_sid,
                conversation=conversation,
                contact=conversation.contact,
                lead=conversation.lead,
            )

            # Link webhook event to message and conversation (SEC-1)
            webhook_event.sms_message = sms_message
            webhook_event.conversation = conversation
            webhook_event.processed_successfully = True
            webhook_event.save(update_fields=['sms_message', 'conversation', 'processed_successfully'])

            # Update conversation
            conversation.message_count += 1
            conversation.last_message_at = timezone.now()
            conversation.last_message_from_us = False
            conversation.save(update_fields=[
                'message_count',
                'last_message_at',
                'last_message_from_us',
            ])

            # Update phone number stats
            our_phone.messages_received += 1
            our_phone.last_used_at = timezone.now()
            our_phone.save(update_fields=['messages_received', 'last_used_at'])

            # Handle opt-out
            if is_opt_out:
                _process_opt_out(
                    firm=firm,
                    phone_number=from_number,
                    message_body=message_body,
                    conversation=conversation,
                )

                # Send auto-response
                response_message = (
                    "You have been unsubscribed from SMS messages. "
                    "Reply START to resubscribe."
                )

                _send_auto_response(
                    to_number=from_number,
                    message=response_message,
                    from_number=to_number,
                    firm=firm,
                    conversation=conversation,
                )

        logger.info(f"Processed inbound SMS: message {sms_message.id}")

        # Return TwiML response (empty is fine)
        return HttpResponse(
            '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            content_type='text/xml',
            status=200
        )

    except Exception as e:
        logger.error(f"Error processing inbound webhook: {e}", exc_info=True)
        return HttpResponse(status=500)


def _check_opt_out_keywords(message_body: str) -> bool:
    """
    Check if message contains opt-out keywords.

    Args:
        message_body: Message text

    Returns:
        True if message contains opt-out keywords
    """
    # Normalize message (lowercase, strip whitespace)
    normalized = message_body.strip().lower()

    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)

    # Check if any keyword matches
    return normalized in OPT_OUT_KEYWORDS


def _process_opt_out(
    firm,
    phone_number: str,
    message_body: str,
    conversation,
):
    """
    Process opt-out request.

    Creates opt-out record and marks conversation as opted out.

    Args:
        firm: Firm instance
        phone_number: Phone number opting out
        message_body: Opt-out message text
        conversation: Conversation instance
    """
    # Create or update opt-out record
    opt_out, created = SMSOptOut.objects.get_or_create(
        firm=firm,
        phone_number=phone_number,
        defaults={
            'opt_out_message': message_body,
            'conversation': conversation,
            'contact': conversation.contact if conversation else None,
        }
    )

    if not created:
        # Update existing opt-out
        opt_out.opt_out_message = message_body
        opt_out.conversation = conversation
        opt_out.save(update_fields=['opt_out_message', 'conversation'])

    # Mark conversation as opted out
    if conversation:
        conversation.is_opt_out = True
        conversation.status = 'closed'
        conversation.save(update_fields=['is_opt_out', 'status'])

    logger.info(f"Processed opt-out for {phone_number}")


def _send_auto_response(
    to_number: str,
    message: str,
    from_number: str,
    firm,
    conversation,
):
    """
    Send automatic response message.

    Args:
        to_number: Recipient phone number
        message: Message text
        from_number: Sender phone number (our number)
        firm: Firm instance
        conversation: Conversation instance
    """
    try:
        # Send via Twilio
        twilio_service = TwilioService()
        result = twilio_service.send_sms(
            to_number=to_number,
            message=message,
            from_number=from_number,
        )

        # Create message record
        sms_message = SMSMessage.objects.create(
            firm=firm,
            from_number=conversation.our_number if conversation else None,
            to_number=to_number,
            direction='outbound',
            message_body=message,
            status='sent' if result['success'] else 'failed',
            provider_message_sid=result.get('message_sid', ''),
            conversation=conversation,
        )

        logger.info(f"Sent auto-response: {sms_message.id}")

    except Exception as e:
        logger.error(f"Error sending auto-response: {e}", exc_info=True)


def _update_campaign_stats(campaign: SMSCampaign):
    """
    Update campaign statistics based on messages.

    Args:
        campaign: SMSCampaign instance
    """
    messages = campaign.messages.all()

    campaign.messages_sent = messages.filter(
        status__in=['sent', 'delivered']
    ).count()

    campaign.messages_delivered = messages.filter(
        status='delivered'
    ).count()

    campaign.messages_failed = messages.filter(
        status__in=['failed', 'undelivered']
    ).count()

    campaign.save(update_fields=[
        'messages_sent',
        'messages_delivered',
        'messages_failed',
    ])

    logger.debug(f"Updated campaign {campaign.id} stats")
