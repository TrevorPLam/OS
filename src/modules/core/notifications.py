"""
Notification Service for ConsultantPro.

Provides utilities for sending notifications via:
- Email (Django's email backend)
- Slack (future)
- SMS (future)

Email templates are rendered using Django's template system.
"""

import logging
from dataclasses import dataclass
from email.utils import formataddr
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from modules.core.telemetry import log_event, log_metric, track_duration
from modules.integrations.models import SlackIntegration
from modules.integrations.services import SlackService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailComplianceDetails:
    """Compliance details for email footer and headers."""

    sender_name: str | None = None
    sender_email: str | None = None
    reply_to: list[str] | None = None
    physical_address: str | None = None
    unsubscribe_url: str | None = None
    company_name: str | None = None
    compliance_reason: str | None = None


def _format_from_email(from_email: str, from_name: str | None) -> str:
    if from_name:
        return formataddr((from_name, from_email))
    return from_email


def _build_compliance_footer(compliance: EmailComplianceDetails) -> tuple[str, str]:
    footer_lines = []
    company_name = compliance.company_name or "ConsultantPro"

    if compliance.compliance_reason:
        footer_lines.append(compliance.compliance_reason)

    if compliance.physical_address:
        footer_lines.append(f"Mailing address: {compliance.physical_address}")

    if compliance.unsubscribe_url:
        footer_lines.append(f"Unsubscribe: {compliance.unsubscribe_url}")

    footer_lines.append(f"Sent by {company_name}.")

    text_footer = "\n".join(footer_lines)
    html_footer = (
        "<hr>"
        "<p style=\"color: #666; font-size: 12px; line-height: 1.5;\">"
        + "<br>".join(footer_lines)
        + "</p>"
    )

    return html_footer, text_footer


def _apply_compliance_footer(
    html_content: str | None,
    text_content: str | None,
    compliance: EmailComplianceDetails,
) -> tuple[str | None, str | None]:
    html_footer, text_footer = _build_compliance_footer(compliance)

    if html_content:
        html_content = f"{html_content}\n{html_footer}"

    if text_content:
        text_content = f"{text_content}\n\n{text_footer}"
    elif html_content:
        text_content = f"{strip_tags(html_content)}\n\n{text_footer}"

    return html_content, text_content


class EmailNotification:
    """
    Email notification service using Django's email backend.

    Usage:
        EmailNotification.send(
            to=['user@example.com'],
            subject='Proposal Accepted',
            template='emails/proposal_accepted.html',
            context={'proposal': proposal_instance}
        )
    """

    @staticmethod
    def send(
        to: list[str] | str,
        subject: str,
        template: str | None = None,
        context: dict[str, Any] | None = None,
        html_content: str | None = None,
        text_content: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: list[str] | None = None,
        compliance: EmailComplianceDetails | None = None,
    ) -> bool:
        """
        Send email notification.

        Args:
            to: List of recipient email addresses or single email string
            subject: Email subject line
            template: Path to HTML template (e.g., 'emails/proposal_accepted.html')
            context: Template context variables
            html_content: Direct HTML content (if not using template)
            text_content: Plain text content (auto-generated from HTML if not provided)
            from_email: Sender email (defaults to settings.DEFAULT_FROM_EMAIL)
            from_name: Sender name to include in the From header
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-To addresses
            compliance: Optional compliance footer and sender identification details

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            with track_duration("notification_email_send", channel="email"):
                # Use default from_email if not provided
                if not from_email:
                    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@consultantpro.com")

                if compliance and compliance.sender_email:
                    from_email = compliance.sender_email
                if compliance and compliance.sender_name:
                    from_name = compliance.sender_name

                # Render HTML content from template if provided
                if template and context is not None:
                    html_content = render_to_string(template, context)

                # Generate plain text version if not provided
                if html_content and not text_content:
                    text_content = strip_tags(html_content)

                if compliance:
                    html_content, text_content = _apply_compliance_footer(
                        html_content,
                        text_content,
                        compliance,
                    )

                resolved_reply_to = reply_to
                if compliance and compliance.reply_to:
                    resolved_reply_to = compliance.reply_to

                formatted_from_email = _format_from_email(from_email, from_name)

                # Create email message
                if html_content:
                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=text_content or "",
                        from_email=formatted_from_email,
                        to=to if isinstance(to, list) else [to],
                        cc=cc,
                        bcc=bcc,
                        reply_to=resolved_reply_to,
                    )
                    email.attach_alternative(html_content, "text/html")
                else:
                    # Plain text only
                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=text_content or "",
                        from_email=formatted_from_email,
                        to=to if isinstance(to, list) else [to],
                        cc=cc,
                        bcc=bcc,
                        reply_to=resolved_reply_to,
                    )

                # Send email
                email.send(fail_silently=False)

            log_metric(
                "notification_email_sent",
                channel="email",
                count=len(to if isinstance(to, list) else [to]),
                status="success",
            )
            logger.info("Email sent successfully")
            return True

        except Exception as e:
            log_event(
                "notification_email_failed",
                channel="email",
                error_class=e.__class__.__name__,
                error_message=str(e),
            )
            logger.error(f"Failed to send email to {to}: {e.__class__.__name__}: {e}")
            return False

    @staticmethod
    def send_proposal_accepted(proposal: Any) -> bool:
        """
        Send notification when a proposal is accepted.

        Args:
            proposal: Proposal model instance

        Returns:
            True if email sent successfully, False otherwise
        """

        # Determine recipient email
        recipient_email = None
        if hasattr(proposal, "created_by") and proposal.created_by:
            recipient_email = proposal.created_by.email

        if not recipient_email:
            logger.warning(f"No recipient email for proposal {getattr(proposal, 'proposal_number', 'unknown')}")
            log_event("notification_missing_recipient", channel="email", context="proposal_accepted")
            return False

        # Prepare email context
        context = {
            "proposal": proposal,
            "proposal_number": proposal.proposal_number,
            "proposal_title": proposal.title,
            "estimated_value": proposal.estimated_value,
            "currency": proposal.currency,
            "client_name": (
                getattr(proposal.client, "company_name", "N/A")
                if hasattr(proposal, "client") and proposal.client
                else (
                    getattr(proposal.prospect, "company_name", "N/A")
                    if hasattr(proposal, "prospect") and proposal.prospect
                    else "N/A"
                )
            ),
        }

        # Send email
        return EmailNotification.send(
            to=[recipient_email],
            subject=f"🎉 Proposal {proposal.proposal_number} Accepted!",
            html_content=f"""
                <h2>Congratulations! Your proposal has been accepted.</h2>
                <p><strong>Proposal:</strong> {context['proposal_number']} - {context['proposal_title']}</p>
                <p><strong>Client:</strong> {context['client_name']}</p>
                <p><strong>Value:</strong> {context['currency']} {context['estimated_value']}</p>
                <p>The client conversion process has been initiated automatically.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated notification from ConsultantPro CRM.
                </p>
            """,
        )

    @staticmethod
    def send_proposal_sent(proposal: Any) -> bool:
        """
        Send notification when a proposal is sent to client.

        Args:
            proposal: Proposal model instance

        Returns:
            True if email sent successfully, False otherwise
        """
        recipient_email = None
        if hasattr(proposal, "created_by") and proposal.created_by:
            recipient_email = proposal.created_by.email

        if not recipient_email:
            logger.warning(f"No recipient email for proposal {getattr(proposal, 'proposal_number', 'unknown')}")
            log_event("notification_missing_recipient", channel="email", context="proposal_sent")
            return False

        context = {
            "proposal_number": proposal.proposal_number,
            "proposal_title": proposal.title,
            "client_name": (
                getattr(proposal.client, "company_name", "N/A")
                if hasattr(proposal, "client") and proposal.client
                else (
                    getattr(proposal.prospect, "company_name", "N/A")
                    if hasattr(proposal, "prospect") and proposal.prospect
                    else "N/A"
                )
            ),
            "valid_until": proposal.valid_until,
        }

        return EmailNotification.send(
            to=[recipient_email],
            subject=f"Proposal {proposal.proposal_number} Sent",
            html_content=f"""
                <h2>Proposal Sent Successfully</h2>
                <p><strong>Proposal:</strong> {context['proposal_number']} - {context['proposal_title']}</p>
                <p><strong>Client:</strong> {context['client_name']}</p>
                <p><strong>Valid Until:</strong> {context['valid_until']}</p>
                <p>The proposal has been sent to the client for review.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated notification from ConsultantPro CRM.
                </p>
            """,
        )

    @staticmethod
    def send_contract_activated(contract: Any) -> bool:
        """
        Send notification when a contract is activated.

        Args:
            contract: Contract model instance

        Returns:
            True if email sent successfully, False otherwise
        """
        # Send to project managers and account manager
        recipients = []

        # Add client's account manager if available
        if hasattr(contract, "client") and contract.client:
            if hasattr(contract.client, "account_manager") and contract.client.account_manager:
                recipients.append(contract.client.account_manager.email)

        if not recipients:
            logger.warning(f"No recipients for contract {getattr(contract, 'contract_number', 'unknown')}")
            log_event("notification_missing_recipient", channel="email", context="contract_activated")
            return False

        context = {
            "contract_number": contract.contract_number,
            "contract_title": contract.title,
            "client_name": (
                getattr(contract.client, "company_name", "N/A")
                if hasattr(contract, "client") and contract.client
                else "N/A"
            ),
            "contract_value": contract.contract_value,
            "currency": contract.currency,
            "start_date": contract.start_date,
            "end_date": contract.end_date,
        }

        return EmailNotification.send(
            to=recipients,
            subject=f"📋 Contract {contract.contract_number} Activated",
            html_content=f"""
                <h2>Contract Activated</h2>
                <p><strong>Contract:</strong> {context['contract_number']} - {context['contract_title']}</p>
                <p><strong>Client:</strong> {context['client_name']}</p>
                <p><strong>Value:</strong> {context['currency']} {context['contract_value']}</p>
                <p><strong>Duration:</strong> {context['start_date']} to {context['end_date']}</p>
                <p>Please proceed with project setup and resource allocation.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated notification from ConsultantPro CRM.
                </p>
            """,
        )

    @staticmethod
    def send_task_assignment(task: Any) -> bool:
        """
        Send notification when a task is assigned.

        Args:
            task: Task model instance

        Returns:
            True if email sent successfully, False otherwise
        """
        if not task.assigned_to or not task.assigned_to.email:
            logger.warning(f"Task '{getattr(task, 'title', 'unknown')}' has no assigned user with email")
            log_event("notification_missing_recipient", channel="email", context="task_assignment")
            return False

        context = {
            "task_title": task.title,
            "task_description": task.description or "No description provided",
            "project_name": task.project.name if hasattr(task, "project") and task.project else "N/A",
            "due_date": task.due_date if hasattr(task, "due_date") else "Not set",
            "priority": task.priority if hasattr(task, "priority") else "normal",
            "assigned_to_name": task.assigned_to.get_full_name() or task.assigned_to.username,
        }

        return EmailNotification.send(
            to=[task.assigned_to.email],
            subject=f"📋 New Task Assigned: {task.title}",
            html_content=f"""
                <h2>New Task Assigned</h2>
                <p>Hello {context['assigned_to_name']},</p>
                <p>You have been assigned a new task:</p>
                <p><strong>Task:</strong> {context['task_title']}</p>
                <p><strong>Project:</strong> {context['project_name']}</p>
                <p><strong>Priority:</strong> {context['priority'].upper()}</p>
                <p><strong>Due Date:</strong> {context['due_date']}</p>
                <p><strong>Description:</strong></p>
                <p>{context['task_description']}</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated notification from ConsultantPro Project Management.
                </p>
            """,
        )

    @staticmethod
    def send_project_completed(project: Any) -> bool:
        """
        Send notification when a project is completed.

        Args:
            project: Project model instance

        Returns:
            True if email sent successfully, False otherwise
        """
        # Send to project manager, client account manager, and project team
        recipients = []

        if hasattr(project, "project_manager") and project.project_manager:
            recipients.append(project.project_manager.email)

        if hasattr(project, "client") and project.client:
            if hasattr(project.client, "account_manager") and project.client.account_manager:
                recipients.append(project.client.account_manager.email)

        if not recipients:
            logger.warning(f"No recipients for project '{getattr(project, 'name', 'unknown')}'")
            log_event("notification_missing_recipient", channel="email", context="project_completed")
            return False

        # Remove duplicates
        recipients = list(set(recipients))

        context = {
            "project_name": project.name,
            "project_code": project.project_code if hasattr(project, "project_code") else "N/A",
            "client_name": (
                getattr(project.client, "company_name", "N/A")
                if hasattr(project, "client") and project.client
                else "N/A"
            ),
            "start_date": project.start_date if hasattr(project, "start_date") else "N/A",
            "completion_date": (
                project.actual_completion_date
                if hasattr(project, "actual_completion_date") and project.actual_completion_date
                else project.end_date
                if hasattr(project, "end_date")
                else "N/A"
            ),
        }

        return EmailNotification.send(
            to=recipients,
            subject=f"🎊 Project Completed: {project.name}",
            html_content=f"""
                <h2>Project Completed Successfully</h2>
                <p><strong>Project:</strong> {context['project_code']} - {context['project_name']}</p>
                <p><strong>Client:</strong> {context['client_name']}</p>
                <p><strong>Duration:</strong> {context['start_date']} to {context['completion_date']}</p>
                <p>The project has been marked as completed. Please proceed with:</p>
                <ul>
                    <li>Final billing and invoicing</li>
                    <li>Project closure report</li>
                    <li>Client satisfaction survey</li>
                    <li>Team debriefing</li>
                </ul>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated notification from ConsultantPro Project Management.
                </p>
            """,
        )


class SlackNotification:
    """
    Slack notification service (placeholder for future implementation).

    Requires:
    - Slack API token in settings
    - Slack webhook URL or Bot token
    """

    @staticmethod
    def send(
        channel: str,
        message: str,
        attachments: list[dict[str, Any]] | None = None,
        firm=None,
    ) -> bool:
        """
        Send Slack notification using configured integration.

        Args:
            _channel: Slack channel name or ID
            _message: Message text
            _attachments: Slack attachments
            firm: Optional firm context to resolve tenant-specific installation
        """
        integration = None
        if firm:
            integration = SlackIntegration.objects.filter(firm=firm, status="active").first()

        if not integration:
            logger.info("Slack notification attempted without active integration")
            log_event("notification_slack_attempted", channel="slack", context="missing_integration")
            return False

        service = SlackService(integration)
        ok = service.send_message(text=_message, channel=_channel, attachments=_attachments or [])
        log_event("notification_slack_sent" if ok else "notification_slack_failed", channel="slack")
        return ok


class SMSNotification:
    """
    SMS notification service (placeholder for future implementation).

    Requires:
    - Twilio or similar SMS service integration
    """

    @staticmethod
    def send(to: str, message: str) -> bool:
        """
        Send SMS notification (placeholder).

        Args:
            to (str): Phone number
            message (str): SMS message text
        """
        logger.info("SMS notification dispatch attempted")
        log_event("notification_sms_attempted", channel="sms")
        # DEFERRED: SMS service integration - See TODO_ANALYSIS.md #11
        # Requires: Twilio or similar SMS service credentials
        return False
