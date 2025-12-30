"""
Execute Pending Workflows Management Command.

Processes all pending workflow executions that are due.
Should be run periodically via cron job (e.g., every 5 minutes).

Usage:
    python manage.py execute_pending_workflows
"""

from django.core.management.base import BaseCommand
from modules.calendar.workflow_services import WorkflowExecutionEngine


class Command(BaseCommand):
    help = 'Execute all pending meeting workflow executions that are due'
    
    def handle(self, *args, **options):
        """Execute pending workflows."""
        self.stdout.write('Checking for pending workflows...')
        
        engine = WorkflowExecutionEngine()
        stats = engine.execute_pending_workflows()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Workflow execution complete:\n"
                f"  - Executed: {stats['executed']}\n"
                f"  - Failed: {stats['failed']}\n"
                f"  - Skipped: {stats['skipped']}"
            )
        )
        
        if stats['failed'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Warning: {stats['failed']} workflows failed. Check logs for details."
                )
            )
