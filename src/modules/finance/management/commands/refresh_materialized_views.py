"""
Django management command to refresh materialized views (Sprint 5.4).

This command refreshes all materialized views for reporting.
Can be scheduled via cron or task scheduler for daily refresh.

Usage:
    python manage.py refresh_materialized_views
    python manage.py refresh_materialized_views --view revenue
    python manage.py refresh_materialized_views --firm-id 123
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from modules.finance.models import RevenueByProjectMonthMV, MVRefreshLog
from modules.projects.models import UtilizationByUserWeekMV, UtilizationByProjectMonthMV


class Command(BaseCommand):
    help = "Refresh materialized views for reporting (Sprint 5.4)"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--view",
            type=str,
            choices=["all", "revenue", "utilization_user", "utilization_project"],
            default="all",
            help="Which view(s) to refresh (default: all)",
        )
        parser.add_argument(
            "--firm-id",
            type=int,
            help="Firm ID to refresh (not supported - refreshes all data)",
        )
        parser.add_argument(
            "--no-concurrent",
            action="store_true",
            help="Disable concurrent refresh (blocks reads during refresh)",
        )
    
    def handle(self, *args, **options):
        view_choice = options["view"]
        firm_id = options.get("firm_id")
        concurrently = not options["no_concurrent"]
        
        self.stdout.write(self.style.SUCCESS(
            f"Starting materialized view refresh at {timezone.now()}"
        ))
        
        if firm_id:
            self.stdout.write(self.style.WARNING(
                f"Note: firm_id={firm_id} specified but PostgreSQL MV refresh is all-or-nothing"
            ))
        
        results = []
        
        # Refresh revenue view
        if view_choice in ["all", "revenue"]:
            self.stdout.write("Refreshing mv_revenue_by_project_month...")
            result = RevenueByProjectMonthMV.refresh(firm_id=firm_id, concurrently=concurrently)
            results.append(result)
            
            if result["status"] == "success":
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ Revenue view refreshed: {result['rows_affected']} rows in {result['duration_seconds']}s"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"  ✗ Revenue view failed: {result.get('error', 'Unknown error')}"
                ))
        
        # Refresh utilization user week view
        if view_choice in ["all", "utilization_user"]:
            self.stdout.write("Refreshing mv_utilization_by_user_week...")
            result = UtilizationByUserWeekMV.refresh(firm_id=firm_id, concurrently=concurrently)
            results.append(result)
            
            if result["status"] == "success":
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ User utilization view refreshed: {result['rows_affected']} rows in {result['duration_seconds']}s"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"  ✗ User utilization view failed: {result.get('error', 'Unknown error')}"
                ))
        
        # Refresh utilization project month view
        if view_choice in ["all", "utilization_project"]:
            self.stdout.write("Refreshing mv_utilization_by_project_month...")
            result = UtilizationByProjectMonthMV.refresh(firm_id=firm_id, concurrently=concurrently)
            results.append(result)
            
            if result["status"] == "success":
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ Project utilization view refreshed: {result['rows_affected']} rows in {result['duration_seconds']}s"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"  ✗ Project utilization view failed: {result.get('error', 'Unknown error')}"
                ))
        
        # Summary
        self.stdout.write("\n" + "="*60)
        success_count = sum(1 for r in results if r["status"] == "success")
        total_count = len(results)
        
        if success_count == total_count:
            self.stdout.write(self.style.SUCCESS(
                f"All {total_count} materialized view(s) refreshed successfully!"
            ))
            return 0
        else:
            self.stdout.write(self.style.ERROR(
                f"Only {success_count}/{total_count} materialized view(s) succeeded"
            ))
            return 1
