"""
Django management command for firm provisioning (DOC-19.1).

Usage:
    python manage.py provision_firm \
        --name "Acme Consulting" \
        --slug acme-consulting \
        --admin-email admin@acme.com \
        --admin-password secure123 \
        --timezone "America/Los_Angeles" \
        --currency USD \
        --tier professional
"""

from django.core.management.base import BaseCommand, CommandError
from modules.firm.provisioning import provision_firm, ProvisioningError


class Command(BaseCommand):
    help = 'Provision a new firm with baseline configuration (DOC-19.1)'

    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Firm name (e.g., "Acme Consulting")'
        )
        parser.add_argument(
            '--slug',
            type=str,
            required=True,
            help='URL-safe slug (e.g., "acme-consulting")'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            required=True,
            help='Admin user email address'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            required=True,
            help='Admin user password'
        )

        # Optional arguments
        parser.add_argument(
            '--admin-first-name',
            type=str,
            default='',
            help='Admin user first name'
        )
        parser.add_argument(
            '--admin-last-name',
            type=str,
            default='',
            help='Admin user last name'
        )
        parser.add_argument(
            '--timezone',
            type=str,
            default='America/New_York',
            help='Firm timezone (default: America/New_York)'
        )
        parser.add_argument(
            '--currency',
            type=str,
            default='USD',
            help='Firm currency (default: USD)'
        )
        parser.add_argument(
            '--tier',
            type=str,
            default='starter',
            choices=['starter', 'professional', 'enterprise'],
            help='Subscription tier (default: starter)'
        )
        parser.add_argument(
            '--max-users',
            type=int,
            default=5,
            help='Maximum number of users (default: 5)'
        )
        parser.add_argument(
            '--max-clients',
            type=int,
            default=25,
            help='Maximum number of clients (default: 25)'
        )
        parser.add_argument(
            '--max-storage-gb',
            type=int,
            default=10,
            help='Maximum storage in GB (default: 10)'
        )

    def handle(self, *args, **options):
        firm_name = options['name']
        firm_slug = options['slug']
        admin_email = options['admin_email']
        admin_password = options['admin_password']

        self.stdout.write(
            self.style.NOTICE(f"Provisioning firm: {firm_name} (slug={firm_slug})")
        )

        try:
            result = provision_firm(
                firm_name=firm_name,
                firm_slug=firm_slug,
                admin_email=admin_email,
                admin_password=admin_password,
                admin_first_name=options['admin_first_name'],
                admin_last_name=options['admin_last_name'],
                timezone=options['timezone'],
                currency=options['currency'],
                subscription_tier=options['tier'],
                max_users=options['max_users'],
                max_clients=options['max_clients'],
                max_storage_gb=options['max_storage_gb'],
            )

            firm = result['firm']
            admin_user = result['admin_user']
            created = result['created']
            provisioning_log = result['provisioning_log']

            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ Firm created successfully"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠ Firm already exists, verified configuration"))

            self.stdout.write("")
            self.stdout.write("Provisioning Details:")
            self.stdout.write(f"  Firm ID:            {firm.id}")
            self.stdout.write(f"  Firm Name:          {firm.name}")
            self.stdout.write(f"  Firm Slug:          {firm.slug}")
            self.stdout.write(f"  Status:             {firm.status}")
            self.stdout.write(f"  Subscription Tier:  {firm.subscription_tier}")
            self.stdout.write(f"  Timezone:           {firm.timezone}")
            self.stdout.write(f"  Currency:           {firm.currency}")
            self.stdout.write("")
            self.stdout.write(f"  Admin User ID:      {admin_user.id}")
            self.stdout.write(f"  Admin Email:        {admin_user.email}")
            self.stdout.write(f"  Admin Name:         {admin_user.get_full_name() or '(not set)'}")
            self.stdout.write("")
            self.stdout.write(f"  Provisioning Log ID: {provisioning_log.id}")
            self.stdout.write(f"  Correlation ID:      {provisioning_log.correlation_id}")
            self.stdout.write(f"  Status:              {provisioning_log.status}")
            self.stdout.write(f"  Duration:            {provisioning_log.duration_seconds}s")
            self.stdout.write(f"  Steps Completed:     {', '.join(provisioning_log.steps_completed)}")
            self.stdout.write("")

            if created:
                self.stdout.write(self.style.SUCCESS("Firm provisioning completed successfully!"))
            else:
                self.stdout.write(self.style.SUCCESS("Firm provisioning verified (idempotent)!"))

        except ProvisioningError as e:
            raise CommandError(f"Provisioning failed: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error during provisioning: {e}")
