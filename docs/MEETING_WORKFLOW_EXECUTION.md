# Meeting Workflow Execution Engine

## Overview

The Meeting Workflow Execution Engine implements automated pre/post meeting workflows for appointments. This addresses a critical gap identified in MISSINGFEATURES.md where MeetingWorkflow models existed but workflows were never actually executed.

## Architecture

### Components

1. **WorkflowExecutionEngine** (`workflow_services.py`)
   - Core service that executes workflow actions
   - Handles email, SMS, task creation, survey, and CRM update actions
   - Provides workflow triggering and batch execution capabilities

2. **Django Signals** (`signals.py`)
   - Automatic workflow triggering on appointment lifecycle events
   - Triggers on: created, confirmed, completed, cancelled
   - Creates workflow execution records with proper timing

3. **Management Command** (`execute_pending_workflows.py`)
   - Cron-based batch processor
   - Executes all pending workflows that are due
   - Returns statistics on execution (executed, failed, skipped)

## Workflow Lifecycle

### 1. Workflow Creation (via Admin/API)

```python
workflow = MeetingWorkflow.objects.create(
    firm=firm,
    name="24-Hour Reminder",
    trigger='appointment_created',
    appointment_type=consultation_type,  # or None for all types
    delay_minutes=-1440,  # -24 hours (before appointment)
    action_type='send_email',
    action_config={
        'subject': 'Appointment Reminder',
        'template': 'Hi {{contact.name}}, your appointment is at {{appointment.start_time}}',
        'to_email': '{{contact.email}}',
        'from_email': 'noreply@firm.com'
    },
    status='active'
)
```

### 2. Automatic Triggering (via Signals)

When an appointment is created or changes status:

```python
# Appointment created
appointment = Appointment.objects.create(
    firm=firm,
    appointment_type=consultation_type,
    start_time=tomorrow_at_2pm,
    end_time=tomorrow_at_230pm,
    staff_user=consultant,
    status='requested'
)
# Signal automatically creates MeetingWorkflowExecution records
```

### 3. Scheduled Execution (via Cron)

Set up cron job to run every 5 minutes:

```bash
*/5 * * * * cd /path/to/app && python manage.py execute_pending_workflows
```

The command will:
- Find all pending executions scheduled for now or earlier
- Execute each workflow action (email, SMS, task, etc.)
- Update execution status (completed/failed)
- Skip workflows for cancelled appointments
- Create audit events for all executions

## Supported Action Types

### 1. Send Email (Fully Implemented)

```python
action_config = {
    'subject': 'Subject with {{variables}}',
    'template': 'Email body with {{variables}}',
    'to_email': '{{contact.email}}',  # or direct email
    'from_email': 'sender@example.com'  # optional
}
```

**Template Variables:**
- `{{appointment.*}}` - appointment_id, start_time, status, location_mode, location_details, duration_minutes
- `{{contact.*}}` - name, email
- `{{staff.*}}` - name, email
- `{{firm.*}}` - name

**Example:**
```
Subject: Reminder: Your appointment with {{staff.name}}
Body: Hi {{contact.name}}, this is a reminder that your appointment is scheduled for {{appointment.start_time}}.
```

### 2. Create Task (Stub - Requires Project)

```python
action_config = {
    'title': 'Follow up on {{appointment.id}}',
    'description': 'Send follow-up materials',
    'due_days': 2  # days from now
}
```

**Note:** Task creation currently skipped because Task model requires a Project association, which appointments don't have. Future enhancement needed.

### 3. Send SMS (Stub - Requires Twilio Integration)

```python
action_config = {
    'message': 'SMS message with {{variables}}',
    'to_phone': '+1234567890'
}
```

**Future Work:** Integrate Twilio or similar SMS service.

### 4. Send Survey (Stub - Requires Survey System)

```python
action_config = {
    'survey_id': 'satisfaction_survey_v1',
    'to_email': '{{contact.email}}'
}
```

**Future Work:** Build or integrate survey system.

### 5. Update CRM (Stub - Requires CRM Integration)

```python
action_config = {
    'update_type': 'add_note',  # or 'change_stage', 'add_tag'
    'value': 'Appointment completed successfully'
}
```

**Future Work:** Implement CRM update logic.

## Workflow Timing

### Before Appointment (Negative Delay)

Scheduled relative to appointment start time:

```python
delay_minutes = -1440  # 24 hours before
delay_minutes = -60    # 1 hour before
delay_minutes = -30    # 30 minutes before
```

### After Appointment (Positive Delay)

Scheduled relative to trigger time or appointment end:

```python
delay_minutes = 0      # Immediately after
delay_minutes = 60     # 1 hour after
delay_minutes = 1440   # 24 hours after
```

For `appointment_completed` trigger, delay is relative to appointment end time.
For other triggers, delay is relative to current time.

## Error Handling

### Execution Status States

- **pending** - Waiting for scheduled time
- **executing** - Currently running
- **completed** - Successfully executed
- **failed** - Execution failed (error message captured)
- **cancelled** - Appointment was cancelled

### Failure Handling

- Errors are logged with full traceback
- Error message stored in `MeetingWorkflowExecution.error_message`
- Failed executions don't block other workflows
- Manual retry possible via admin interface (future enhancement)

### Skipped Executions

Workflows are automatically skipped if:
- Appointment was cancelled
- Scheduled time is in the past when triggered

## Monitoring & Observability

### Audit Events

All workflow executions create audit events:

```python
AuditEvent.objects.create(
    firm=firm,
    event_type='workflow_executed',
    object_type='appointment',
    object_id=appointment_id,
    metadata={
        'workflow_id': workflow_id,
        'workflow_name': workflow_name,
        'action_type': action_type,
        'execution_id': execution_id,
        'result_summary': 'completed'
    }
)
```

### Execution Statistics

Management command returns statistics:

```python
{
    'executed': 15,  # Successfully executed
    'failed': 2,     # Failed with errors
    'skipped': 3     # Skipped (cancelled appointments)
}
```

### Logging

All workflow actions are logged:

```python
logger.info("Scheduled workflow 'X' for appointment Y at Z")
logger.info("Successfully executed workflow 'X' for appointment Y")
logger.error("Failed to execute workflow 'X': error message")
```

## Usage Examples

### Example 1: Appointment Reminder

Send reminder 24 hours before appointment:

```python
MeetingWorkflow.objects.create(
    firm=firm,
    name="24hr Reminder",
    trigger='appointment_created',
    delay_minutes=-1440,
    action_type='send_email',
    action_config={
        'subject': 'Appointment Tomorrow',
        'template': '''Hi {{contact.name}},
        
This is a reminder that you have an appointment tomorrow at {{appointment.start_time}}.

Location: {{appointment.location_details}}

Looking forward to speaking with you!

{{staff.name}}''',
        'to_email': '{{contact.email}}'
    },
    status='active'
)
```

### Example 2: Thank You Email

Send thank you 1 hour after appointment:

```python
MeetingWorkflow.objects.create(
    firm=firm,
    name="Thank You Email",
    trigger='appointment_completed',
    delay_minutes=60,
    action_type='send_email',
    action_config={
        'subject': 'Thank you for your time',
        'template': '''Hi {{contact.name}},
        
Thank you for meeting with me today. I've attached the materials we discussed.

Please let me know if you have any questions!

Best regards,
{{staff.name}}''',
        'to_email': '{{contact.email}}'
    },
    status='active'
)
```

### Example 3: Confirmation Workflow

Send confirmation when appointment is confirmed:

```python
MeetingWorkflow.objects.create(
    firm=firm,
    name="Confirmation Email",
    trigger='appointment_confirmed',
    delay_minutes=0,  # Send immediately
    action_type='send_email',
    action_config={
        'subject': 'Your appointment is confirmed',
        'template': '''Hi {{contact.name}},
        
Your appointment has been confirmed for {{appointment.start_time}}.

We'll send you a reminder 24 hours before the appointment.

{{firm.name}}''',
        'to_email': '{{contact.email}}'
    },
    status='active'
)
```

## Future Enhancements

### Priority 1: Task Creation
- Make Task.project optional OR
- Create default "System Tasks" project for workflow-generated tasks

### Priority 2: SMS Integration
- Integrate Twilio for SMS sending
- Add SMS templates
- Track SMS delivery status

### Priority 3: Survey System
- Build or integrate survey platform
- Support NPS, CSAT, custom surveys
- Track survey responses

### Priority 4: CRM Updates
- Implement CRM update actions
- Support note creation, stage changes, tag addition
- Link to specific CRM records

### Priority 5: Advanced Features
- Manual workflow retry interface
- Workflow templates library
- Conditional logic (if/then branches)
- Multiple actions per workflow
- Workflow analytics dashboard

## Testing

Comprehensive test suite with 19 test cases:

```bash
cd src
python -m pytest modules/calendar/test_workflow_execution.py -v
```

**Test Coverage:**
- Workflow triggering logic
- Appointment type filtering
- Scheduling calculations (before/after)
- Email action execution with template rendering
- Task creation action (with project requirement caveat)
- SMS/survey/CRM stub actions
- Error handling and failure recovery
- Batch execution processing
- Signal integration with appointment lifecycle

## Security & Privacy

### Tenant Isolation
- All workflows scoped to firm
- Cannot access other firms' appointments or workflows
- Audit events respect tenant boundaries

### Data Privacy
- No customer content in error messages
- Template context limited to necessary fields
- Email sending uses Django's email backend (secure by default)
- Audit events contain metadata only (no email content)

### Access Control
- Workflow creation requires staff permissions
- Portal users cannot create or edit workflows
- Execution engine runs with system permissions (no user context)

## Deployment Checklist

- [ ] Configure Django email backend (SMTP settings)
- [ ] Set up cron job: `*/5 * * * * python manage.py execute_pending_workflows`
- [ ] Test email sending in development environment
- [ ] Create initial workflow templates for common use cases
- [ ] Monitor workflow execution logs for first week
- [ ] Set up alerting for high failure rates (future enhancement)

## Troubleshooting

### Workflows Not Executing

1. Check cron job is running:
   ```bash
   crontab -l | grep execute_pending_workflows
   ```

2. Check for pending executions:
   ```python
   MeetingWorkflowExecution.objects.filter(
       status='pending',
       scheduled_for__lte=timezone.now()
   ).count()
   ```

3. Check execution logs:
   ```bash
   tail -f logs/workflow_execution.log
   ```

### Email Not Sending

1. Verify Django email settings:
   ```python
   from django.core.mail import send_mail
   send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
   ```

2. Check email backend configuration in settings.py

3. Check execution result_data for error messages:
   ```python
   execution = MeetingWorkflowExecution.objects.filter(status='failed').last()
   print(execution.error_message)
   ```

### Workflows Skipped

Check if appointments are being cancelled:
```python
appointments = Appointment.objects.filter(status='cancelled')
# These appointments will have their workflows skipped
```

## References

- MISSINGFEATURES.md: Meeting Workflow Execution Engine (Phase 1)
- DOC-34.1: Calendar domain implementation
- Calendly comparison: Pre/post meeting workflows
- Models: MeetingWorkflow, MeetingWorkflowExecution (modules/calendar/models.py)
