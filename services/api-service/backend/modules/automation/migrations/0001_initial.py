# Generated migration for automation module

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("firm", "0001_initial"),
        ("crm", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Workflow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Human-readable workflow name", max_length=255)),
                ("description", models.TextField(blank=True, help_text="Workflow description and purpose")),
                ("status", models.CharField(choices=[("draft", "Draft"), ("active", "Active"), ("paused", "Paused"), ("archived", "Archived")], default="draft", max_length=20)),
                ("activated_at", models.DateTimeField(blank=True, help_text="When workflow was first activated", null=True)),
                ("version", models.IntegerField(default=1, help_text="Workflow version number")),
                ("canvas_data", models.JSONField(default=dict, help_text="Visual canvas state (zoom, pan, etc.)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_workflows", to=settings.AUTH_USER_MODEL)),
                ("firm", models.ForeignKey(help_text="Firm (workspace) this workflow belongs to", on_delete=django.db.models.deletion.CASCADE, related_name="automation_workflows", to="firm.firm")),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_workflows", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "automation_workflow",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="WorkflowNode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("node_id", models.CharField(help_text="Unique node identifier within workflow", max_length=100)),
                ("node_type", models.CharField(choices=[("send_email", "Send Email"), ("send_sms", "Send SMS"), ("create_task", "Create Task"), ("create_deal", "Create Deal"), ("update_deal", "Update Deal"), ("update_contact", "Update Contact Field"), ("add_tag", "Add Tag"), ("remove_tag", "Remove Tag"), ("add_to_list", "Add to List"), ("remove_from_list", "Remove from List"), ("webhook", "Send Webhook"), ("internal_notification", "Send Internal Notification"), ("condition", "If/Else Condition"), ("wait_time", "Wait for Time"), ("wait_until", "Wait Until Date"), ("wait_condition", "Wait for Condition"), ("split", "A/B Split Test"), ("goal", "Goal Reached")], help_text="Type of node", max_length=50)),
                ("label", models.CharField(help_text="Human-readable node label", max_length=255)),
                ("position_x", models.IntegerField(default=0, help_text="X coordinate on canvas")),
                ("position_y", models.IntegerField(default=0, help_text="Y coordinate on canvas")),
                ("configuration", models.JSONField(default=dict, help_text="Node-specific configuration")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workflow_nodes", to="firm.firm")),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="nodes", to="automation.workflow")),
            ],
            options={
                "db_table": "automation_workflow_node",
                "ordering": ["workflow", "position_y", "position_x"],
                "unique_together": {("workflow", "node_id")},
            },
        ),
        migrations.CreateModel(
            name="WorkflowTrigger",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("trigger_type", models.CharField(choices=[("form_submitted", "Form Submitted"), ("email_opened", "Email Opened"), ("email_clicked", "Email Link Clicked"), ("email_replied", "Email Replied"), ("email_bounced", "Email Bounced"), ("email_unsubscribed", "Email Unsubscribed"), ("page_visited", "Page Visited"), ("site_activity", "Site Activity Detected"), ("contact_created", "Contact Created"), ("contact_updated", "Contact Updated"), ("contact_tag_added", "Contact Tag Added"), ("contact_tag_removed", "Contact Tag Removed"), ("contact_list_added", "Added to List"), ("contact_list_removed", "Removed from List"), ("deal_created", "Deal Created"), ("deal_stage_changed", "Deal Stage Changed"), ("deal_value_changed", "Deal Value Changed"), ("deal_won", "Deal Won"), ("deal_lost", "Deal Lost"), ("score_threshold_reached", "Score Threshold Reached"), ("score_threshold_dropped", "Score Dropped Below Threshold"), ("date_reached", "Specific Date Reached"), ("date_field_reached", "Date Field Reached"), ("time_delay", "Time Delay Elapsed"), ("anniversary", "Anniversary"), ("manual", "Manual Trigger"), ("api", "API Trigger")], help_text="Type of trigger event", max_length=50)),
                ("configuration", models.JSONField(default=dict, help_text="Trigger-specific settings (form_id, tag_id, threshold, etc.)")),
                ("filter_conditions", models.JSONField(default=dict, help_text="Additional conditions to evaluate (field comparisons, segments, etc.)")),
                ("is_active", models.BooleanField(default=True, help_text="Whether this trigger is actively monitoring")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workflow_triggers", to="firm.firm")),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="triggers", to="automation.workflow")),
            ],
            options={
                "db_table": "automation_workflow_trigger",
                "ordering": ["workflow", "trigger_type"],
            },
        ),
        migrations.CreateModel(
            name="WorkflowEdge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("condition_type", models.CharField(blank=True, help_text="Condition type (yes/no for if/else, etc.)", max_length=50)),
                ("condition_config", models.JSONField(blank=True, default=dict, help_text="Condition configuration")),
                ("label", models.CharField(blank=True, help_text="Edge label (Yes, No, etc.)", max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workflow_edges", to="firm.firm")),
                ("source_node", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="outgoing_edges", to="automation.workflownode")),
                ("target_node", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incoming_edges", to="automation.workflownode")),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="edges", to="automation.workflow")),
            ],
            options={
                "db_table": "automation_workflow_edge",
                "ordering": ["workflow", "source_node"],
            },
        ),
        migrations.CreateModel(
            name="WorkflowExecution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("workflow_version", models.IntegerField(help_text="Workflow version at execution time")),
                ("status", models.CharField(choices=[("running", "Running"), ("waiting", "Waiting"), ("completed", "Completed"), ("goal_reached", "Goal Reached"), ("failed", "Failed"), ("canceled", "Canceled")], default="running", max_length=20)),
                ("execution_path", models.JSONField(default=list, help_text="Ordered list of nodes executed")),
                ("context_data", models.JSONField(default=dict, help_text="Execution context and variables")),
                ("trigger_type", models.CharField(help_text="What triggered this execution", max_length=50)),
                ("trigger_data", models.JSONField(default=dict, help_text="Trigger event data")),
                ("goal_reached", models.BooleanField(default=False, help_text="Whether execution reached a goal")),
                ("goal_reached_at", models.DateTimeField(blank=True, null=True)),
                ("error_count", models.IntegerField(default=0, help_text="Number of errors encountered")),
                ("last_error", models.TextField(blank=True, help_text="Last error message")),
                ("idempotency_key", models.CharField(help_text="Execution idempotency key", max_length=64, unique=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("waiting_until", models.DateTimeField(blank=True, help_text="Resume execution at this time", null=True)),
                ("waiting_for_condition", models.JSONField(blank=True, default=dict, help_text="Condition to wait for")),
                ("contact", models.ForeignKey(help_text="Contact being processed through workflow", on_delete=django.db.models.deletion.CASCADE, related_name="workflow_executions", to="crm.contact")),
                ("current_node", models.ForeignKey(blank=True, help_text="Current node being executed or waited on", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="current_executions", to="automation.workflownode")),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workflow_executions", to="firm.firm")),
                ("goal_node", models.ForeignKey(blank=True, help_text="Goal node that was reached", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="goal_executions", to="automation.workflownode")),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="executions", to="automation.workflow")),
            ],
            options={
                "db_table": "automation_workflow_execution",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="ContactFlowState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entered_at", models.DateTimeField(auto_now_add=True, help_text="When contact entered this node")),
                ("exited_at", models.DateTimeField(blank=True, help_text="When contact exited this node", null=True)),
                ("action_status", models.CharField(blank=True, help_text="Status of action execution (sent, delivered, clicked, etc.)", max_length=20)),
                ("action_result", models.JSONField(blank=True, default=dict, help_text="Action execution result data")),
                ("variant", models.CharField(blank=True, help_text="A/B test variant assigned", max_length=50)),
                ("execution", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="flow_states", to="automation.workflowexecution")),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contact_flow_states", to="firm.firm")),
                ("node", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="flow_states", to="automation.workflownode")),
            ],
            options={
                "db_table": "automation_contact_flow_state",
                "ordering": ["execution", "entered_at"],
            },
        ),
        migrations.CreateModel(
            name="WorkflowGoal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Goal name", max_length=255)),
                ("description", models.TextField(blank=True, help_text="Goal description")),
                ("goal_value", models.DecimalField(decimal_places=2, default=0, help_text="Revenue or value assigned to this goal", max_digits=10)),
                ("tracking_window_days", models.IntegerField(default=30, help_text="Days to track conversions")),
                ("total_conversions", models.IntegerField(default=0, help_text="Total number of conversions")),
                ("conversion_rate", models.DecimalField(decimal_places=2, default=0, help_text="Conversion rate percentage", max_digits=5)),
                ("total_value", models.DecimalField(decimal_places=2, default=0, help_text="Total value from conversions", max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workflow_goals", to="firm.firm")),
                ("goal_node", models.ForeignKey(help_text="Node that represents goal completion", on_delete=django.db.models.deletion.CASCADE, related_name="goals", to="automation.workflownode")),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="goals", to="automation.workflow")),
            ],
            options={
                "db_table": "automation_workflow_goal",
                "ordering": ["workflow", "name"],
            },
        ),
        migrations.CreateModel(
            name="WorkflowAnalytics",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("period_start", models.DateField(help_text="Analytics period start date")),
                ("period_end", models.DateField(help_text="Analytics period end date")),
                ("total_executions", models.IntegerField(default=0, help_text="Total executions started")),
                ("completed_executions", models.IntegerField(default=0, help_text="Executions that completed")),
                ("failed_executions", models.IntegerField(default=0, help_text="Executions that failed")),
                ("goal_reached_executions", models.IntegerField(default=0, help_text="Executions that reached goal")),
                ("avg_completion_time_seconds", models.IntegerField(default=0, help_text="Average time to completion in seconds")),
                ("median_completion_time_seconds", models.IntegerField(default=0, help_text="Median time to completion in seconds")),
                ("drop_off_points", models.JSONField(default=dict, help_text="Map of node IDs to drop-off counts")),
                ("node_performance", models.JSONField(default=dict, help_text="Per-node performance metrics")),
                ("goal_conversion_rate", models.DecimalField(decimal_places=2, default=0, help_text="Overall goal conversion rate", max_digits=5)),
                ("calculated_at", models.DateTimeField(auto_now=True, help_text="When these analytics were last calculated")),
                ("firm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workflow_analytics", to="firm.firm")),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="analytics", to="automation.workflow")),
            ],
            options={
                "db_table": "automation_workflow_analytics",
                "ordering": ["-period_end", "workflow"],
                "unique_together": {("workflow", "period_start", "period_end")},
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name="workflow",
            index=models.Index(fields=["firm", "status"], name="auto_wf_firm_status_idx"),
        ),
        migrations.AddIndex(
            model_name="workflow",
            index=models.Index(fields=["firm", "-created_at"], name="auto_wf_firm_created_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowtrigger",
            index=models.Index(fields=["firm", "trigger_type", "is_active"], name="auto_trg_firm_type_act_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowtrigger",
            index=models.Index(fields=["workflow"], name="auto_trg_workflow_idx"),
        ),
        migrations.AddIndex(
            model_name="workflownode",
            index=models.Index(fields=["firm", "workflow"], name="auto_node_firm_wf_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowedge",
            index=models.Index(fields=["firm", "workflow"], name="auto_edge_firm_wf_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowedge",
            index=models.Index(fields=["source_node"], name="auto_edge_source_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowedge",
            index=models.Index(fields=["target_node"], name="auto_edge_target_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowexecution",
            index=models.Index(fields=["firm", "status"], name="auto_exec_firm_status_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowexecution",
            index=models.Index(fields=["workflow", "-started_at"], name="auto_exec_wf_started_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowexecution",
            index=models.Index(fields=["contact", "-started_at"], name="auto_exec_contact_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowexecution",
            index=models.Index(fields=["idempotency_key"], name="auto_exec_idem_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowexecution",
            index=models.Index(fields=["waiting_until"], name="auto_exec_waiting_idx"),
        ),
        migrations.AddIndex(
            model_name="contactflowstate",
            index=models.Index(fields=["firm", "node", "-entered_at"], name="auto_flow_firm_node_idx"),
        ),
        migrations.AddIndex(
            model_name="contactflowstate",
            index=models.Index(fields=["execution", "entered_at"], name="auto_flow_exec_entered_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowgoal",
            index=models.Index(fields=["firm", "workflow"], name="auto_goal_firm_wf_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowanalytics",
            index=models.Index(fields=["firm", "workflow", "-period_end"], name="auto_analytics_firm_wf_idx"),
        ),
    ]
