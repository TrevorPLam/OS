"""
Management command to send file request reminders (FILE-2).

This command processes scheduled file request reminders and sends emails
to recipients. It should be run periodically via cron.

Usage:
    python manage.py send_file_request_reminders [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from modules.core.notifications import EmailNotification
from modules.documents.models import FileRequest, FileRequestReminder


class Command(BaseCommand):
    help = "Send scheduled file request reminders"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without actually sending emails",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        now = timezone.now()

        # Get reminders that are scheduled to be sent
        reminders = FileRequestReminder.objects.filter(
            status="scheduled",
            scheduled_for__lte=now,
        ).select_related(
            "file_request",
            "file_request__external_share",
            "file_request__created_by"
        )

        if not reminders.exists():
            self.stdout.write(self.style.SUCCESS("No reminders to send."))
            return

        self.stdout.write(f"Found {reminders.count()} reminder(s) to send...")

        sent_count = 0
        skipped_count = 0
        failed_count = 0

        for reminder in reminders:
            file_request = reminder.file_request

            # Skip if file request is already completed or cancelled
            if file_request.status in ["completed", "cancelled"]:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping reminder {reminder.id}: Request {file_request.id} is {file_request.status}"
                    )
                )
                reminder.mark_as_skipped()
                skipped_count += 1
                continue

            # Skip if file request has expired
            if file_request.is_expired:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping reminder {reminder.id}: Request {file_request.id} has expired"
                    )
                )
                reminder.mark_as_skipped()
                skipped_count += 1
                continue

            # Skip if file request is already fulfilled
            if file_request.status == "uploaded" and not reminder.escalate_to_team:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping reminder {reminder.id}: Request {file_request.id} already uploaded"
                    )
                )
                reminder.mark_as_skipped()
                skipped_count += 1
                continue

            # Send reminder
            try:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[DRY RUN] Would send reminder {reminder.id} to {file_request.recipient_email}"
                        )
                    )
                    self.stdout.write(f"  Subject: {reminder.subject}")
                    self.stdout.write(f"  Type: {reminder.reminder_type}")
                    if reminder.escalate_to_team:
                        self.stdout.write(f"  Escalation to: {', '.join(reminder.escalation_emails)}")
                else:
                    self._send_reminder(reminder, file_request)
                    reminder.mark_as_sent()

                    # Update file request reminder count
                    file_request.reminder_sent_count += 1
                    file_request.last_reminder_sent_at = now
                    file_request.save(update_fields=["reminder_sent_count", "last_reminder_sent_at", "updated_at"])

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Sent reminder {reminder.id} to {file_request.recipient_email}"
                        )
                    )

                sent_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to send reminder {reminder.id}: {str(e)}"
                    )
                )
                reminder.mark_as_failed(str(e))
                failed_count += 1

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No emails were actually sent."))
        self.stdout.write(self.style.SUCCESS(f"Reminders sent: {sent_count}"))
        self.stdout.write(self.style.WARNING(f"Reminders skipped: {skipped_count}"))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f"Reminders failed: {failed_count}"))
        self.stdout.write(self.style.SUCCESS("=" * 50))

    def _send_reminder(self, reminder, file_request):
        """Send reminder email to recipient and optionally escalate to team."""
        email_service = EmailNotification()

        # Generate upload URL
        upload_url = f"/api/public/file-requests/{file_request.external_share.share_token}/"

        # Customize message with upload URL
        message = f"""{reminder.message}

Upload Link: {upload_url}

This link will expire on {file_request.expires_at.strftime('%B %d, %Y at %I:%M %p') if file_request.expires_at else 'never'}.
"""

        # Send to recipient
        email_service.send(
            to_email=file_request.recipient_email,
            subject=reminder.subject,
            body=message.strip(),
        )

        # Send escalation email to team if needed
        if reminder.escalate_to_team and reminder.escalation_emails:
            escalation_subject = f"[ESCALATION] {reminder.subject}"
            escalation_message = f"""
This is an escalation notice for a pending file request.

Request: {file_request.title}
Recipient: {file_request.recipient_name or file_request.recipient_email}
Status: {file_request.status}
Created: {file_request.created_at.strftime('%B %d, %Y')}
Expires: {file_request.expires_at.strftime('%B %d, %Y') if file_request.expires_at else 'Never'}

Files Uploaded: {file_request.uploaded_file_count}
{f'Max Files: {file_request.max_files}' if file_request.max_files else ''}

Reminders Sent: {file_request.reminder_sent_count}

Please follow up with the recipient to ensure the documents are uploaded.

Internal Link: /api/v1/documents/file-requests/{file_request.id}/
"""

            for escalation_email in reminder.escalation_emails:
                email_service.send(
                    to_email=escalation_email,
                    subject=escalation_subject,
                    body=escalation_message.strip(),
                )
