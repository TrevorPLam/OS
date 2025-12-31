# Onboarding Notifications Implementation

**Document Version:** 1.0
**Date:** December 31, 2025
**Purpose:** Document the client notification system for onboarding workflows

---

## Overview

The onboarding system automatically sends email notifications to clients when:
1. Task reminders are sent for incomplete onboarding tasks
2. Document reminders are sent for missing or rejected documents

This ensures clients are kept informed and engaged throughout the onboarding process.

---

## OnboardingTask Reminders

When an onboarding task is assigned to a client and a reminder is sent, the system automatically emails the client with:

- Task title and description
- Due date (if specified)
- Firm name and contact information

**Trigger Conditions:**
- Task is assigned to client (`assigned_to_client = True`)
- Task status is `pending` or `in_progress`
- `send_reminder()` method is called on the task

**Email Format:**
```
Subject: Reminder: [Task Title] - [Process Name]

Dear [Client Name],

This is a friendly reminder about the following onboarding task:

Task: [Task Title]
Description: [Task Description]
Due Date: [Due Date]

Please complete this task at your earliest convenience to continue 
with your onboarding process.

Best regards,
[Firm Name]
```

**Example Usage:**
```python
from modules.onboarding.models import OnboardingTask

task = OnboardingTask.objects.get(id=123)
if task.send_reminder():
    print("Reminder sent successfully")
```

---

## OnboardingDocument Reminders

When a document reminder is sent for missing or rejected documents, the system automatically emails the client with:

- Document name and description
- Document status (required/requested/rejected)
- Rejection reason (if applicable)
- Firm name and contact information

**Trigger Conditions:**
- Document status is `required`, `requested`, or `rejected`
- `send_reminder()` method is called on the document

**Email Format:**
```
Subject: Document Reminder: [Document Name] - [Process Name]

Dear [Client Name],

This is a reminder about the following document for your onboarding process:

Document: [Document Name]
Description: [Document Description]
Status: This document [status message]

[Rejection Reason if applicable]

Please upload this document at your earliest convenience to continue 
with your onboarding process.

Best regards,
[Firm Name]
```

**Example Usage:**
```python
from modules.onboarding.models import OnboardingDocument

document = OnboardingDocument.objects.get(id=456)
if document.send_reminder():
    print("Document reminder sent successfully")
```

---

## Implementation Details

### Email Service

Notifications are sent using the `EmailNotification` service from `modules.core.notifications`:

```python
from modules.core.notifications import EmailNotification

EmailNotification.send(
    to=client.primary_contact_email,
    subject="Reminder: Task Title",
    html_content="<html>...</html>",
)
```

### Client Email Address

The system sends emails to the client's `primary_contact_email` field:

```python
client = self.process.client
recipient = client.primary_contact_email
```

### Error Handling

If email sending fails:
- The error is logged with context (task/document ID, client ID)
- The reminder is still marked as sent (state is updated)
- The system continues processing (fail-safe behavior)

### Logging

All notification events are logged with appropriate context:

```python
logger.info(
    f"Sent onboarding task reminder to client {client.id}",
    extra={'task_id': self.id, 'client_id': client.id}
)
```

---

## Configuration

### Email Settings

Ensure Django email backend is configured in settings:

```python
# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@yourfirm.com'
```

### Template Customization

Email templates use HTML with inline styles for compatibility. To customize:

1. Edit the HTML content in the respective `send_reminder()` methods
2. Add custom merge fields as needed (e.g., `{{custom_field}}`)
3. Ensure all client-specific data is properly escaped

---

## Future Enhancements

Potential improvements for the notification system:

1. **Template-based emails**: Use Django template files instead of inline HTML
2. **Batch notifications**: Send daily digest emails instead of individual reminders
3. **Notification preferences**: Allow clients to configure notification frequency
4. **Multi-channel notifications**: Support SMS and in-app notifications
5. **Localization**: Support multiple languages based on client preferences
6. **Rich formatting**: Include branded headers/footers and custom styling

---

## Related Documentation

- [Core Notifications Service](../src/modules/core/notifications.py)
- [Onboarding Models](../src/modules/onboarding/models.py)
- [Client Models](../src/modules/clients/models.py)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | December 31, 2025 | Initial implementation of task and document reminders |
