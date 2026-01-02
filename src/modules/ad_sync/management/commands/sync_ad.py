"""
Django management command to run Active Directory synchronization.

AD-4: Manual on-demand sync capability via management command.

Usage:
    # Sync all firms with scheduled sync
    python manage.py sync_ad

    # Sync specific firm (full sync)
    python manage.py sync_ad --firm-id 1 --full

    # Sync specific firm (delta sync)
    python manage.py sync_ad --firm-id 1 --delta

    # Dry run (preview without applying changes)
    python manage.py sync_ad --dry-run
"""

import json
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from modules.ad_sync.tasks import (
    run_scheduled_sync,
    run_full_sync_for_firm,
    run_delta_sync_for_firm,
)
from modules.firm.models import Firm


class Command(BaseCommand):
    """Management command to synchronize users from Active Directory."""
    
    help = 'Synchronize users from Active Directory'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--firm-id',
            type=int,
            help='Sync specific firm by ID (if not provided, syncs all firms)',
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Perform full sync (default is scheduled/delta sync)',
        )
        parser.add_argument(
            '--delta',
            action='store_true',
            help='Perform delta sync (sync only changed users)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview sync without applying changes (not yet implemented)',
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        firm_id = options.get('firm_id')
        is_full = options.get('full', False)
        is_delta = options.get('delta', False)
        is_dry_run = options.get('dry_run', False)
        
        if is_dry_run:
            self.stdout.write(
                self.style.WARNING('Dry-run mode is not yet implemented')
            )
            return
        
        if is_full and is_delta:
            raise CommandError('Cannot specify both --full and --delta')
        
        start_time = timezone.now()
        
        if firm_id:
            # Sync specific firm
            self._sync_firm(firm_id, is_full=is_full, is_delta=is_delta)
        else:
            # Sync all firms
            self._sync_all_firms()
        
        duration = (timezone.now() - start_time).total_seconds()
        self.stdout.write(
            self.style.SUCCESS(f'AD sync completed in {duration:.2f} seconds')
        )
    
    def _sync_firm(self, firm_id: int, is_full: bool = False, is_delta: bool = False):
        """
        Sync a specific firm.
        
        Args:
            firm_id: ID of the firm to sync
            is_full: Whether to perform full sync
            is_delta: Whether to perform delta sync
        """
        # Verify firm exists
        try:
            firm = Firm.objects.get(id=firm_id)
        except Firm.DoesNotExist:
            raise CommandError(f'Firm with ID {firm_id} does not exist')
        
        self.stdout.write(f'Syncing firm: {firm.name} (ID: {firm_id})')
        
        # Determine sync type
        if is_full:
            sync_type = 'full'
            result = run_full_sync_for_firm(firm_id)
        elif is_delta:
            sync_type = 'delta'
            result = run_delta_sync_for_firm(firm_id)
        else:
            sync_type = 'scheduled'
            result = run_delta_sync_for_firm(firm_id)
        
        # Display results
        self._display_result(result)
    
    def _sync_all_firms(self):
        """Sync all firms with AD sync enabled."""
        self.stdout.write('Syncing all firms with AD sync enabled...')
        
        result = run_scheduled_sync()
        
        # Display aggregate results
        self.stdout.write(
            f'Total firms: {result["total_firms"]}'
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Successful syncs: {result["successful_syncs"]}'
            )
        )
        
        if result['failed_syncs'] > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'Failed syncs: {result["failed_syncs"]}'
                )
            )
        
        # Display individual firm results
        for firm_result in result['results']:
            self._display_result(firm_result, indent=True)
    
    def _display_result(self, result: dict, indent: bool = False):
        """
        Display sync result.
        
        Args:
            result: Sync result dictionary
            indent: Whether to indent output
        """
        prefix = '  ' if indent else ''
        
        if result['success']:
            self.stdout.write(
                prefix + self.style.SUCCESS(
                    f'✓ {result.get("firm_name", "Firm")} synced successfully:'
                )
            )
            self.stdout.write(
                prefix + f'  - Created: {result.get("users_created", 0)} users'
            )
            self.stdout.write(
                prefix + f'  - Updated: {result.get("users_updated", 0)} users'
            )
            self.stdout.write(
                prefix + f'  - Disabled: {result.get("users_disabled", 0)} users'
            )
            self.stdout.write(
                prefix + f'  - Skipped: {result.get("users_skipped", 0)} users'
            )
            self.stdout.write(
                prefix + f'  - Groups synced: {result.get("groups_synced", 0)}'
            )
            self.stdout.write(
                prefix + f'  - Duration: {result.get("duration_seconds", 0)}s'
            )
        else:
            self.stdout.write(
                prefix + self.style.ERROR(
                    f'✗ {result.get("firm_name", "Firm")} sync failed:'
                )
            )
            self.stdout.write(
                prefix + f'  Error: {result.get("error", "Unknown error")}'
            )
