"""
Management command to execute data retention policies (ASSESS-L19.4).

Runs retention policies for all active firms and processes data according to
configured retention schedules.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from modules.core.retention import RetentionPolicy, RetentionService
from modules.firm.models import Firm


class Command(BaseCommand):
    help = "Execute data retention policies for all active firms (ASSESS-L19.4)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--firm-id',
            type=int,
            help='Execute policies for a specific firm only'
        )
        parser.add_argument(
            '--data-type',
            type=str,
            choices=[choice[0] for choice in RetentionPolicy.DATA_TYPE_CHOICES],
            help='Execute policies for a specific data type only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually modifying data'
        )

    def handle(self, *args, **options):
        firm_id = options.get('firm_id')
        data_type = options.get('data_type')
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No data will be modified"))
        
        # Get firms
        if firm_id:
            try:
                firms = [Firm.objects.get(id=firm_id, status__in=['active', 'trial'])]
            except Firm.DoesNotExist:
                raise CommandError(f"Firm with ID {firm_id} not found or not active")
        else:
            firms = Firm.objects.filter(status__in=['active', 'trial'])
        
        total_executions = 0
        total_processed = 0
        
        for firm in firms:
            self.stdout.write(f"\nProcessing retention policies for firm: {firm.name} (ID: {firm.id})")
            
            # Get active policies
            policies = RetentionPolicy.objects.filter(
                firm=firm,
                is_active=True
            )
            
            if data_type:
                policies = policies.filter(data_type=data_type)
            
            if not policies.exists():
                self.stdout.write(self.style.WARNING(f"  No active retention policies found for {firm.name}"))
                continue
            
            for policy in policies:
                self.stdout.write(f"  Executing policy: {policy.data_type} ({policy.retention_days} days, {policy.get_action_display()})")
                
                try:
                    execution = RetentionService.execute_policy(policy, dry_run=dry_run)
                    
                    self.stdout.write(
                        f"    Processed: {execution.records_processed}, "
                        f"Archived: {execution.records_archived}, "
                        f"Anonymized: {execution.records_anonymized}, "
                        f"Deleted: {execution.records_deleted}, "
                        f"Skipped: {execution.records_skipped}"
                    )
                    
                    total_executions += 1
                    total_processed += execution.records_processed
                    
                    if execution.status == 'failed':
                        self.stdout.write(self.style.ERROR(f"    ERROR: {execution.error_message}"))
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    ERROR executing policy: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"\nCompleted: {total_executions} policies executed, {total_processed} records processed"
        ))