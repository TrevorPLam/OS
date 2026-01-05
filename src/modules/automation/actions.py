"""
Automation Action Executors (AUTO-3).

Implements executable actions within workflows:
- Send email
- Send SMS
- Create/update deals
- Update contact fields
- Add/remove tags and lists
- Create tasks
- Webhooks
- Wait conditions

Each action executor follows standard interface:
- execute(execution, node, config) -> result
"""

from datetime import timedelta
from typing import Any, Dict

from django.utils import timezone
from django.template import Context, Template

from modules.core.notifications import EmailNotification
from modules.crm.models import Deal, DealTask
from modules.marketing.models import EmailTemplate, Segment, SegmentMembership, Tag
from modules.projects.models import Task
from modules.sms.models import SMSMessage, SMSPhoneNumber
from modules.sms.twilio_service import TwilioService


class ActionExecutor:
    """Base class for action executors."""

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute action.

        Args:
            execution: WorkflowExecution instance
            node: WorkflowNode instance
            config: Node configuration

        Returns:
            Result dictionary with status and data
        """
        raise NotImplementedError("Subclasses must implement execute()")


class SendEmailAction(ActionExecutor):
    """
    Send email action (AUTO-3).

    Configuration:
    - template_id: Email template to use
    - from_email: Sender email (optional)
    - subject: Email subject (optional override)
    - body: Email body (optional override)
    - track_opens: Track email opens
    - track_clicks: Track link clicks
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Send email to contact."""
        contact = execution.contact

        # Get template or use inline content
        template_id = config.get("template_id")
        subject = config.get("subject", "")
        body = config.get("body", "")
        html_content = config.get("html_content")
        text_content = config.get("text_content")

        if template_id:
            template = EmailTemplate.objects.filter(firm=execution.firm, id=template_id).first()
            if not template:
                return {"status": "failed", "error": "Email template not found"}

            context = _build_merge_context(execution)
            subject = Template(template.subject_line).render(Context(context))
            html_content = Template(template.html_content).render(Context(context))
            text_content = template.plain_text_content or ""
            if text_content:
                text_content = Template(text_content).render(Context(context))
            template.mark_used()

        # Send email
        try:
            EmailNotification.send(
                to=contact.email,
                subject=subject,
                html_content=html_content or body,
                text_content=text_content,
            )

            result = {
                "status": "sent",
                "email": contact.email,
                "subject": subject,
                "sent_at": timezone.now().isoformat(),
            }

            return result
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }


class SendSMSAction(ActionExecutor):
    """
    Send SMS action (AUTO-3).

    Configuration:
    - message: SMS message text
    - from_number: Sender phone number (optional)
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS to contact."""
        contact = execution.contact
        message = config.get("message", "")
        from_number = config.get("from_number")
        media_urls = config.get("media_urls")

        if not message:
            return {"status": "failed", "error": "Missing SMS message"}

        to_number = contact.mobile_phone or contact.phone
        if not to_number:
            return {"status": "failed", "error": "Contact has no phone number"}

        phone_record = None
        if from_number:
            phone_record = SMSPhoneNumber.objects.filter(firm=execution.firm, phone_number=from_number).first()
        if not phone_record:
            phone_record = SMSPhoneNumber.objects.filter(firm=execution.firm, is_default=True).first()
        if not phone_record:
            return {"status": "failed", "error": "No SMS sender number configured"}

        sms_message = SMSMessage.objects.create(
            firm=execution.firm,
            from_number=phone_record,
            to_number=to_number,
            direction="outbound",
            message_body=message,
            status="queued",
            contact_id=contact.id,
        )

        service = TwilioService()
        result = service.send_sms(
            to_number=to_number,
            message=message,
            from_number=phone_record.phone_number,
            media_urls=media_urls,
        )

        if result.get("success"):
            sms_message.status = "sent"
            sms_message.provider_message_sid = result.get("message_sid", "")
            sms_message.provider_status = result.get("status", "")
            sms_message.price = result.get("price")
            sms_message.price_currency = result.get("price_currency") or sms_message.price_currency
            sms_message.sent_at = timezone.now()
            sms_message.error_code = ""
            sms_message.error_message = ""
        else:
            sms_message.status = "failed"
            sms_message.error_code = result.get("error_code", "")
            sms_message.error_message = result.get("error", "SMS send failed")
        sms_message.save(
            update_fields=[
                "status",
                "provider_message_sid",
                "provider_status",
                "price",
                "price_currency",
                "sent_at",
                "error_code",
                "error_message",
                "updated_at",
            ]
        )

        return {
            "status": "sent" if result.get("success") else "failed",
            "phone": to_number,
            "message": message,
            "provider_message_sid": sms_message.provider_message_sid,
            "sent_at": sms_message.sent_at.isoformat() if sms_message.sent_at else None,
            "error": sms_message.error_message,
        }


class CreateTaskAction(ActionExecutor):
    """
    Create task action (AUTO-3).

    Configuration:
    - title: Task title
    - description: Task description
    - due_date_offset_days: Days from now for due date
    - assigned_to_id: User ID to assign to
    - priority: Task priority
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create task for contact or deal."""
        firm = execution.firm
        contact = execution.contact

        # Get task details
        title = config.get("title", "")
        description = config.get("description", "")
        due_date_offset = config.get("due_date_offset_days", 7)
        assigned_to_id = config.get("assigned_to_id")

        # Calculate due date
        due_date = timezone.now() + timedelta(days=due_date_offset)

        # Find associated deal if exists
        deal = None
        deal_id = execution.context_data.get("deal_id")
        if deal_id:
            try:
                deal = Deal.objects.get(firm=firm, id=deal_id)
            except Deal.DoesNotExist:
                pass

        if deal:
            # Create deal task
            task = DealTask.objects.create(
                firm=firm,
                deal=deal,
                title=title,
                description=description,
                due_date=due_date.date(),
                assigned_to_id=assigned_to_id,
            )

            return {
                "status": "created",
                "task_id": task.id,
                "task_type": "deal_task",
            }
        project_id = config.get("project_id") or execution.context_data.get("project_id")
        if project_id:
            task = Task.objects.create(
                project_id=project_id,
                title=title or f"Follow up with {contact.full_name}",
                description=description,
                due_date=due_date.date(),
                assigned_to_id=assigned_to_id,
                priority=config.get("priority", "medium"),
            )
            return {
                "status": "created",
                "task_id": task.id,
                "task_type": "project_task",
            }

        return {
            "status": "failed",
            "error": "No deal or project context for task creation",
        }


class CreateDealAction(ActionExecutor):
    """
    Create deal action (AUTO-3).

    Configuration:
    - title: Deal title
    - pipeline_id: Pipeline ID
    - stage_id: Initial stage ID
    - value: Deal value
    - assigned_to_id: User ID to assign to
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create deal for contact."""
        firm = execution.firm
        contact = execution.contact

        # Get deal details
        title = config.get("title", f"Deal for {contact.full_name}")
        pipeline_id = config.get("pipeline_id")
        stage_id = config.get("stage_id")
        value = config.get("value", 0)
        assigned_to_id = config.get("assigned_to_id")

        try:
            deal = Deal.objects.create(
                firm=firm,
                contact=contact,
                title=title,
                pipeline_id=pipeline_id,
                stage_id=stage_id,
                value=value,
                assigned_to_id=assigned_to_id,
            )

            # Store deal ID in execution context
            execution.context_data["deal_id"] = deal.id
            execution.save()

            return {
                "status": "created",
                "deal_id": deal.id,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }


class UpdateDealAction(ActionExecutor):
    """
    Update deal action (AUTO-3).

    Configuration:
    - deal_id: Deal ID to update (or use from context)
    - stage_id: New stage ID
    - value: New value
    - status: New status
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing deal."""
        firm = execution.firm

        # Get deal ID from config or context
        deal_id = config.get("deal_id") or execution.context_data.get("deal_id")
        if not deal_id:
            return {
                "status": "failed",
                "error": "No deal_id provided",
            }

        try:
            deal = Deal.objects.get(firm=firm, id=deal_id)

            # Update fields
            if "stage_id" in config:
                deal.stage_id = config["stage_id"]
            if "value" in config:
                deal.value = config["value"]
            if "status" in config:
                deal.status = config["status"]

            deal.save()

            return {
                "status": "updated",
                "deal_id": deal.id,
            }
        except Deal.DoesNotExist:
            return {
                "status": "failed",
                "error": f"Deal {deal_id} not found",
            }


class UpdateContactAction(ActionExecutor):
    """
    Update contact field action (AUTO-3).

    Configuration:
    - field_updates: Dictionary of field name -> value
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update contact fields."""
        contact = execution.contact
        field_updates = config.get("field_updates", {})

        updated_fields = []
        for field_name, value in field_updates.items():
            if hasattr(contact, field_name):
                setattr(contact, field_name, value)
                updated_fields.append(field_name)

        if updated_fields:
            contact.save(update_fields=updated_fields)

        return {
            "status": "updated",
            "updated_fields": updated_fields,
        }


class AddTagAction(ActionExecutor):
    """
    Add tag action (AUTO-3).

    Configuration:
    - tag_id: Tag ID to add
    - tag_name: Tag name to add (creates if doesn't exist)
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add tag to contact."""
        firm = execution.firm
        contact = execution.contact

        tag_id = config.get("tag_id")
        tag_name = config.get("tag_name")

        try:
            if tag_id:
                tag = Tag.objects.get(firm=firm, id=tag_id)
            elif tag_name:
                tag, _ = Tag.objects.get_or_create(
                    firm=firm,
                    name=tag_name,
                    defaults={"tag_type": "contact"},
                )
            else:
                return {
                    "status": "failed",
                    "error": "No tag_id or tag_name provided",
                }

            # Add tag to contact
            contact.tags.add(tag)

            return {
                "status": "added",
                "tag_id": tag.id,
                "tag_name": tag.name,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }


class RemoveTagAction(ActionExecutor):
    """
    Remove tag action (AUTO-3).

    Configuration:
    - tag_id: Tag ID to remove
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Remove tag from contact."""
        firm = execution.firm
        contact = execution.contact
        tag_id = config.get("tag_id")

        try:
            tag = Tag.objects.get(firm=firm, id=tag_id)
            contact.tags.remove(tag)

            return {
                "status": "removed",
                "tag_id": tag.id,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }


class AddToListAction(ActionExecutor):
    """
    Add to list action (AUTO-3).

    Configuration:
    - list_id: List/segment ID to add to
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add contact to list/segment."""
        segment_id = config.get("list_id")
        if not segment_id:
            return {"status": "failed", "error": "Missing list_id"}

        segment = Segment.objects.filter(firm=execution.firm, id=segment_id).first()
        if not segment:
            return {"status": "failed", "error": "Segment not found"}

        membership, created = SegmentMembership.objects.get_or_create(
            segment=segment,
            entity_type="contact",
            entity_id=execution.contact.id,
            defaults={"added_by": getattr(execution, "created_by", None)},
        )

        return {
            "status": "added",
            "list_id": segment_id,
            "created": created,
        }


class RemoveFromListAction(ActionExecutor):
    """
    Remove from list action (AUTO-3).

    Configuration:
    - list_id: List/segment ID to remove from
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Remove contact from list/segment."""
        segment_id = config.get("list_id")
        if not segment_id:
            return {"status": "failed", "error": "Missing list_id"}

        membership = SegmentMembership.objects.filter(
            segment_id=segment_id,
            entity_type="contact",
            entity_id=execution.contact.id,
        ).first()
        if membership:
            membership.delete()
            return {"status": "removed", "list_id": segment_id}

        return {"status": "not_found", "list_id": segment_id}


class WebhookAction(ActionExecutor):
    """
    Send webhook action (AUTO-3).

    Configuration:
    - webhook_url: URL to send webhook to
    - method: HTTP method (GET, POST, PUT, DELETE)
    - headers: Custom headers
    - payload: Request payload
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook request."""
        import requests

        url = config.get("webhook_url")
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        payload = config.get("payload", {})

        # Add contact data to payload
        payload["contact"] = {
            "id": execution.contact.id,
            "email": execution.contact.email,
            "first_name": execution.contact.first_name,
            "last_name": execution.contact.last_name,
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                headers=headers,
                timeout=30,
            )

            return {
                "status": "sent",
                "status_code": response.status_code,
                "response": response.text[:1000],  # Limit response size
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }


class InternalNotificationAction(ActionExecutor):
    """
    Send internal notification action (AUTO-3).

    Configuration:
    - recipient_id: User ID to notify
    - message: Notification message
    """

    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Send internal notification to team member."""
        recipient_id = config.get("recipient_id")
        message = config.get("message", "")
        subject = config.get("subject", "Automation Notification")

        if not recipient_id:
            return {"status": "failed", "error": "Missing recipient_id"}

        from django.contrib.auth import get_user_model
        from modules.firm.models import FirmMembership

        User = get_user_model()
        recipient = User.objects.filter(id=recipient_id, is_active=True).first()
        if not recipient:
            return {"status": "failed", "error": "Recipient not found"}

        is_member = FirmMembership.objects.filter(
            firm=execution.firm,
            user=recipient,
            is_active=True,
        ).exists()
        if not is_member:
            return {"status": "failed", "error": "Recipient not in firm"}

        EmailNotification.send(
            to=recipient.email,
            subject=subject,
            text_content=message,
        )

        return {
            "status": "sent",
            "recipient_id": recipient_id,
        }


def _build_merge_context(execution) -> Dict[str, Any]:
    contact = execution.contact
    return {
        "contact": contact,
        "contact_first_name": getattr(contact, "first_name", ""),
        "contact_last_name": getattr(contact, "last_name", ""),
        "contact_full_name": getattr(contact, "full_name", ""),
        "contact_email": getattr(contact, "email", ""),
        "firm_name": execution.firm.name,
        "workflow_name": execution.workflow.name,
        "trigger_type": execution.trigger_type,
        "trigger_data": execution.trigger_data,
    }


# Action executor registry
ACTION_EXECUTORS = {
    "send_email": SendEmailAction,
    "send_sms": SendSMSAction,
    "create_task": CreateTaskAction,
    "create_deal": CreateDealAction,
    "update_deal": UpdateDealAction,
    "update_contact": UpdateContactAction,
    "add_tag": AddTagAction,
    "remove_tag": RemoveTagAction,
    "add_to_list": AddToListAction,
    "remove_from_list": RemoveFromListAction,
    "webhook": WebhookAction,
    "internal_notification": InternalNotificationAction,
}


def get_action_executor(action_type: str) -> ActionExecutor:
    """Get action executor for given action type."""
    executor_class = ACTION_EXECUTORS.get(action_type)
    if not executor_class:
        raise ValueError(f"Unknown action type: {action_type}")
    return executor_class
