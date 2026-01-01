# Generated migration for Sprint 5.2: Revenue Reporting Materialized View

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0011_chargeback_paymentfailure_stripewebhookevent_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Create materialized view for revenue reporting by project and month
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_revenue_by_project_month AS
            SELECT 
                p.firm_id,
                p.id as project_id,
                p.name as project_name,
                p.project_code,
                p.client_id,
                DATE_TRUNC('month', COALESCE(i.issue_date, te.date, e.date))::date as month,
                -- Revenue metrics
                COALESCE(SUM(CASE 
                    WHEN i.status IN ('paid', 'partial') 
                    THEN COALESCE(i.paid_amount, 0) 
                    ELSE 0 
                END), 0) as total_revenue,
                -- Cost metrics
                COALESCE(SUM(te.hours * te.hourly_rate), 0) as labor_cost,
                COALESCE(SUM(CASE 
                    WHEN e.status = 'approved' 
                    THEN e.amount 
                    ELSE 0 
                END), 0) as expense_cost,
                -- Overhead (20% of labor cost, calculated on refresh)
                COALESCE(SUM(te.hours * te.hourly_rate), 0) * 0.20 as overhead_cost,
                -- Team metrics
                COUNT(DISTINCT te.user_id) as team_members,
                COALESCE(SUM(te.hours), 0) as total_hours,
                COALESCE(SUM(CASE 
                    WHEN te.is_billable = true 
                    THEN te.hours 
                    ELSE 0 
                END), 0) as billable_hours,
                -- Invoice counts
                COUNT(DISTINCT i.id) as invoice_count,
                COUNT(DISTINCT CASE 
                    WHEN i.status = 'paid' 
                    THEN i.id 
                END) as paid_invoice_count,
                -- Metadata
                CURRENT_TIMESTAMP as refreshed_at
            FROM projects_projects p
            LEFT JOIN finance_invoices i ON p.id = i.project_id
            LEFT JOIN projects_time_entries te ON p.id = te.project_id
            LEFT JOIN projects_expenses e ON p.id = e.project_id
            WHERE 
                -- Only include records with activity (invoices, time entries, or expenses)
                (i.id IS NOT NULL OR te.id IS NOT NULL OR e.id IS NOT NULL)
                -- Filter to data from last 5 years to keep MV manageable
                AND DATE_TRUNC('month', COALESCE(i.issue_date, te.date, e.date)) >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '5 years')
            GROUP BY 
                p.firm_id,
                p.id,
                p.name,
                p.project_code,
                p.client_id,
                DATE_TRUNC('month', COALESCE(i.issue_date, te.date, e.date));
            
            -- Create indexes for efficient querying
            CREATE INDEX IF NOT EXISTS idx_mv_revenue_firm_month 
                ON mv_revenue_by_project_month(firm_id, month DESC);
            
            CREATE INDEX IF NOT EXISTS idx_mv_revenue_project 
                ON mv_revenue_by_project_month(project_id, month DESC);
            
            CREATE INDEX IF NOT EXISTS idx_mv_revenue_client_month 
                ON mv_revenue_by_project_month(client_id, month DESC);
            
            CREATE INDEX IF NOT EXISTS idx_mv_revenue_refreshed 
                ON mv_revenue_by_project_month(refreshed_at DESC);
            
            -- Create a tracking table for refresh metadata
            CREATE TABLE IF NOT EXISTS finance_mv_refresh_log (
                id SERIAL PRIMARY KEY,
                view_name VARCHAR(255) NOT NULL,
                firm_id INTEGER NULL,  -- NULL for full refresh, specific for partial
                refresh_started_at TIMESTAMP NOT NULL,
                refresh_completed_at TIMESTAMP NULL,
                refresh_status VARCHAR(20) NOT NULL DEFAULT 'running',  -- running, success, failed
                rows_affected INTEGER NULL,
                error_message TEXT NULL,
                triggered_by VARCHAR(50) NOT NULL  -- scheduled, manual, event
            );
            
            CREATE INDEX IF NOT EXISTS idx_mv_refresh_log_view_status 
                ON finance_mv_refresh_log(view_name, refresh_status, refresh_started_at DESC);
            """,
            reverse_sql="""
            -- Drop indexes first
            DROP INDEX IF EXISTS idx_mv_revenue_firm_month;
            DROP INDEX IF EXISTS idx_mv_revenue_project;
            DROP INDEX IF EXISTS idx_mv_revenue_client_month;
            DROP INDEX IF EXISTS idx_mv_revenue_refreshed;
            
            -- Drop materialized view
            DROP MATERIALIZED VIEW IF EXISTS mv_revenue_by_project_month;
            
            -- Drop refresh log table
            DROP TABLE IF EXISTS finance_mv_refresh_log;
            """,
        ),
    ]
