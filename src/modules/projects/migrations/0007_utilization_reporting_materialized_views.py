# Generated migration for Sprint 5.3: Utilization Reporting Materialized Views

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_expense_projecttemplate_tasktemplate_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Create materialized view for utilization reporting by user and week
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_utilization_by_user_week AS
            SELECT 
                p.firm_id,
                te.user_id,
                DATE_TRUNC('week', te.date)::date as week_start,
                -- Hour metrics
                COALESCE(SUM(te.hours), 0) as total_hours,
                COALESCE(SUM(CASE WHEN te.is_billable = true THEN te.hours ELSE 0 END), 0) as billable_hours,
                COALESCE(SUM(CASE WHEN te.is_billable = false THEN te.hours ELSE 0 END), 0) as non_billable_hours,
                -- Project metrics
                COUNT(DISTINCT te.project_id) as projects_worked,
                COUNT(DISTINCT te.date) as days_worked,
                -- Cost metrics
                COALESCE(SUM(te.hours * te.hourly_rate), 0) as total_cost,
                COALESCE(SUM(CASE WHEN te.is_billable = true THEN te.hours * te.hourly_rate ELSE 0 END), 0) as billable_cost,
                -- Metadata
                CURRENT_TIMESTAMP as refreshed_at
            FROM projects_time_entries te
            JOIN projects_projects p ON te.project_id = p.id
            WHERE 
                -- Filter to data from last 3 years to keep MV manageable
                DATE_TRUNC('week', te.date) >= DATE_TRUNC('week', CURRENT_DATE - INTERVAL '3 years')
            GROUP BY 
                p.firm_id,
                te.user_id,
                DATE_TRUNC('week', te.date);
            
            -- Create indexes for efficient querying
            CREATE INDEX IF NOT EXISTS idx_mv_util_user_firm_week 
                ON mv_utilization_by_user_week(firm_id, user_id, week_start DESC);
            
            CREATE INDEX IF NOT EXISTS idx_mv_util_user_week 
                ON mv_utilization_by_user_week(user_id, week_start DESC);
            
            CREATE INDEX IF NOT EXISTS idx_mv_util_firm_week 
                ON mv_utilization_by_user_week(firm_id, week_start DESC);
            
            CREATE INDEX IF NOT EXISTS idx_mv_util_user_refreshed 
                ON mv_utilization_by_user_week(refreshed_at DESC);
            
            -- Create materialized view for utilization reporting by project and month
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_utilization_by_project_month AS
            SELECT 
                p.firm_id,
                p.id as project_id,
                p.name as project_name,
                p.project_code,
                p.client_id,
                DATE_TRUNC('month', te.date)::date as month,
                -- Hour metrics
                COALESCE(SUM(te.hours), 0) as total_hours,
                COALESCE(SUM(CASE WHEN te.is_billable = true THEN te.hours ELSE 0 END), 0) as billable_hours,
                COALESCE(SUM(CASE WHEN te.is_billable = false THEN te.hours ELSE 0 END), 0) as non_billable_hours,
                -- Team metrics
                COUNT(DISTINCT te.user_id) as team_members,
                COUNT(DISTINCT te.date) as days_worked,
                -- Cost metrics
                COALESCE(SUM(te.hours * te.hourly_rate), 0) as total_cost,
                COALESCE(SUM(CASE WHEN te.is_billable = true THEN te.hours * te.hourly_rate ELSE 0 END), 0) as billable_cost,
                -- Task metrics
                COUNT(DISTINCT te.task_id) as tasks_worked,
                -- Metadata
                CURRENT_TIMESTAMP as refreshed_at
            FROM projects_time_entries te
            JOIN projects_projects p ON te.project_id = p.id
            WHERE 
                -- Filter to data from last 5 years to keep MV manageable
                DATE_TRUNC('month', te.date) >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '5 years')
            GROUP BY 
                p.firm_id,
                p.id,
                p.name,
                p.project_code,
                p.client_id,
                DATE_TRUNC('month', te.date);
            
            -- Create indexes for efficient querying
            CREATE INDEX IF NOT EXISTS idx_mv_proj_util_firm_month 
                ON mv_utilization_by_project_month(firm_id, month DESC);
            
            CREATE INDEX IF NOT EXISTS idx_mv_proj_util_project_month 
                ON mv_utilization_by_project_month(project_id, month DESC);
            
            CREATE INDEX IF NOT EXISTS idx_mv_proj_util_client_month 
                ON mv_utilization_by_project_month(client_id, month DESC);
            
            CREATE INDEX IF NOT EXISTS idx_mv_proj_util_refreshed 
                ON mv_utilization_by_project_month(refreshed_at DESC);
            """,
            reverse_sql="""
            -- Drop indexes first - user week view
            DROP INDEX IF EXISTS idx_mv_util_user_firm_week;
            DROP INDEX IF EXISTS idx_mv_util_user_week;
            DROP INDEX IF EXISTS idx_mv_util_firm_week;
            DROP INDEX IF EXISTS idx_mv_util_user_refreshed;
            
            -- Drop user week materialized view
            DROP MATERIALIZED VIEW IF EXISTS mv_utilization_by_user_week;
            
            -- Drop indexes - project month view
            DROP INDEX IF EXISTS idx_mv_proj_util_firm_month;
            DROP INDEX IF EXISTS idx_mv_proj_util_project_month;
            DROP INDEX IF EXISTS idx_mv_proj_util_client_month;
            DROP INDEX IF EXISTS idx_mv_proj_util_refreshed;
            
            -- Drop project month materialized view
            DROP MATERIALIZED VIEW IF EXISTS mv_utilization_by_project_month;
            """,
        ),
    ]
