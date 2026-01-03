"""
Management command to clean up old webhook events (SEC-3).

Removes webhook events older than the configured retention period.
Default: 180 days for webhook events.

Usage:
    python manage.py cleanup_webhook_events
    python manage.py cleanup_webhook_events --dry-run
    python manage.py cleanup_webhook_events --retention-days 90
    python manage.py cleanup_webhook_events --provider stripe
"""

import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clean up old webhook events per data retention policy (SEC-3)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--retention-days",
            type=int,
            default=getattr(settings, "WEBHOOK_RETENTION_DAYS", 180),
            help="Number of days to retain webhook events (default: 180)",
        )
        parser.add_argument(
            "--provider",
            type=str,
            choices=["stripe", "square", "docusign", "sms"],
            help="Clean up events for specific provider only",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without making changes",
        )

    def handle(self, *args, **options):
        retention_days = options["retention_days"]
        provider = options.get("provider")
        dry_run = options["dry_run"]

        cutoff_date = timezone.now() - timedelta(days=retention_days)

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting webhook event cleanup (retention: {retention_days} days)"
            )
        )
        self.stdout.write(f"Cutoff date: {cutoff_date.date()}")
        self.stdout.write(f"Dry run: {dry_run}")
        if provider:
            self.stdout.write(f"Provider filter: {provider}")

        stats = {
            "stripe": 0,
            "square": 0,
            "docusign": 0,
            "sms": 0,
            "total": 0,
        }

        try:
            # Clean up Stripe webhook events
            if not provider or provider == "stripe":
                stats["stripe"] = self._cleanup_stripe_webhooks(
                    cutoff_date, dry_run
                )

            # Clean up Square webhook events
            if not provider or provider == "square":
                stats["square"] = self._cleanup_square_webhooks(
                    cutoff_date, dry_run
                )

            # Clean up DocuSign webhook events
            if not provider or provider == "docusign":
                stats["docusign"] = self._cleanup_docusign_webhooks(
                    cutoff_date, dry_run
                )

            # Clean up SMS webhook events
            if not provider or provider == "sms":
                stats["sms"] = self._cleanup_sms_webhooks(cutoff_date, dry_run)

            stats["total"] = sum(
                stats[k] for k in ["stripe", "square", "docusign", "sms"]
            )

            # Display results
            self.stdout.write("\n" + self.style.SUCCESS("Cleanup Summary:"))
            self.stdout.write(f"  Stripe webhooks: {stats['stripe']}")
            self.stdout.write(f"  Square webhooks: {stats['square']}")
            self.stdout.write(f"  DocuSign webhooks: {stats['docusign']}")
            self.stdout.write(f"  SMS webhooks: {stats['sms']}")
            self.stdout.write(
                self.style.SUCCESS(f"  Total: {stats['total']} webhook events")
            )

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        "\n** DRY RUN ** No changes were made. Run without --dry-run to delete."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "\n✓ Webhook event cleanup completed successfully"
                    )
                )

                # Log metrics for monitoring
                try:
                    from modules.core.telemetry import log_metric

                    log_metric(
                        "data_retention.webhook_events_deleted",
                        count=stats["total"],
                        retention_days=retention_days,
                    )
                except ImportError:
                    pass

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during webhook cleanup: {str(e)}")
            )
            logger.error(f"Webhook cleanup failed: {e}", exc_info=True)
            raise

    def _cleanup_stripe_webhooks(self, cutoff_date, dry_run):
        """Clean up Stripe webhook events older than cutoff date."""
        try:
            from modules.finance.models import StripeWebhookEvent

            old_events = StripeWebhookEvent.objects.filter(
                processed_at__lt=cutoff_date
            )
            count = old_events.count()

            if not dry_run and count > 0:
                with transaction.atomic():
                    old_events.delete()

            return count

        except Exception as e:
            logger.error(f"Error cleaning up Stripe webhooks: {e}", exc_info=True)
            return 0

    def _cleanup_square_webhooks(self, cutoff_date, dry_run):
        """Clean up Square webhook events older than cutoff date."""
        try:
            from modules.finance.models import SquareWebhookEvent

            old_events = SquareWebhookEvent.objects.filter(
                processed_at__lt=cutoff_date
            )
            count = old_events.count()

            if not dry_run and count > 0:
                with transaction.atomic():
                    old_events.delete()

            return count

        except Exception as e:
            logger.error(f"Error cleaning up Square webhooks: {e}", exc_info=True)
            return 0

    def _cleanup_docusign_webhooks(self, cutoff_date, dry_run):
        """Clean up DocuSign webhook events older than cutoff date."""
        try:
            from modules.esignature.models import WebhookEvent

            old_events = WebhookEvent.objects.filter(
                received_at__lt=cutoff_date
            )
            count = old_events.count()

            if not dry_run and count > 0:
                with transaction.atomic():
                    old_events.delete()

            return count

        except Exception as e:
            logger.error(
                f"Error cleaning up DocuSign webhooks: {e}", exc_info=True
            )
            return 0

    def _cleanup_sms_webhooks(self, cutoff_date, dry_run):
        """Clean up SMS webhook events older than cutoff date."""
        try:
            from modules.sms.models import SMSWebhookEvent

            old_events = SMSWebhookEvent.objects.filter(
                received_at__lt=cutoff_date
            )
            count = old_events.count()

            if not dry_run and count > 0:
                with transaction.atomic():
                    old_events.delete()

            return count

        except Exception as e:
            logger.error(f"Error cleaning up SMS webhooks: {e}", exc_info=True)
            return 0
