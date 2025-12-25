# Tier 3: Audit Review Ownership & Cadence

**Status**: ✅ DOCUMENTED
**Created**: 2025-12-25
**Last Updated**: 2025-12-25

## Overview

This document defines who reviews audit events, how often, and what actions to take when anomalies are detected.

**Critical Requirement** (from NOTES_TO_CLAUDE.md):
> Ownership of audit review (who reviews, how often) must be defined.

## Review Ownership

### Platform Level

| Event Category | Primary Owner | Backup Owner | Escalation Path |
|----------------|---------------|--------------|-----------------|
| **BREAK_GLASS** | Security Team Lead | CTO | Incident Response Team |
| **PURGE** | Compliance Officer | Legal Team | Executive Leadership |
| **AUTH** (failed logins) | Security Operations | Platform Ops | Security Team Lead |
| **PERMISSIONS** | Security Operations | Platform Ops | Security Team Lead |
| **CONFIG** | Platform Operations | Engineering Lead | CTO |
| **BILLING_METADATA** | Finance Team | Accounting | CFO |

### Firm Level (Future Enhancement)

Planned for Tier 4:
- Firm Master Admins can review their own firm's events
- Filtered view: only firm-scoped events
- No access to platform operator actions
- Optional notifications for critical events

## Review Cadence

### Critical Events (CRITICAL Severity)

**Review Frequency**: Real-time to Daily

| Event Type | Cadence | Alert Threshold | Action Required |
|------------|---------|-----------------|-----------------|
| **Break-Glass Activation** | Real-time alert | Any activation | Review reason, verify legitimacy, confirm expiry |
| **Break-Glass Content Access** | Daily review | Any access | Verify ticket linkage, confirm necessity |
| **Content Purge** | Daily review | Any purge | Verify reason, confirm Master Admin approval |
| **Failed Login (Admin)** | Real-time alert | 3+ failures in 15min | Investigate potential breach, notify user |

### High-Risk Events (WARNING Severity)

**Review Frequency**: Weekly

| Event Type | Cadence | Alert Threshold | Action Required |
|------------|---------|-----------------|-----------------|
| **Permission Changes** | Weekly | Bulk changes (5+ in 1 hour) | Verify authorization, check for compromise |
| **Config Changes** | Weekly | Production config changes | Verify change control process |
| **Role Escalation** | Weekly | Staff → Admin promotions | Confirm with Firm owner |

### Standard Events (INFO Severity)

**Review Frequency**: Monthly

| Event Type | Cadence | Sample Size | Action Required |
|------------|---------|-------------|-----------------|
| **Successful Logins** | Monthly spot check | 1% random sample | Detect unusual patterns |
| **Billing Events** | Monthly reconciliation | All events | Verify against invoices |
| **Data Exports** | Monthly review | All exports | Verify business purpose |
| **System Events** | Monthly | Error events only | Operational improvements |

## Automated Monitoring

### Real-Time Alerts

Triggers for immediate notification:

1. **Break-Glass Activation**
   - Alert: Security Team Lead + CTO
   - Channel: PagerDuty + Slack #security-alerts
   - SLA: Acknowledge within 15 minutes

2. **Multiple Failed Logins**
   - Threshold: 3+ failures for admin/platform users within 15 minutes
   - Alert: Security Operations
   - Channel: Slack #security-alerts
   - Action: Auto-lock account after 5 failures

3. **Suspicious Permission Changes**
   - Pattern: Multiple role escalations by same actor
   - Alert: Security Team Lead
   - Channel: Slack #security-alerts
   - Action: Freeze account pending review

4. **Unexpected Purge**
   - Trigger: Purge without recent support ticket
   - Alert: Compliance Officer + Legal
   - Channel: Email + Slack #compliance
   - Action: Verify legal basis

### Anomaly Detection (Future - Tier 5)

Machine learning patterns to detect:
- Unusual login times/locations
- Abnormal data access patterns
- Privilege escalation attempts
- Data exfiltration indicators

## Review Process

### Weekly Review (WARNING+ Events)

**Schedule**: Every Monday, 10:00 AM
**Duration**: 30-60 minutes
**Attendees**: Security Ops + Platform Ops

**Procedure**:
1. Query all WARNING+ events from past week
2. For each CRITICAL event:
   - Verify reason field is complete
   - Confirm authorization (ticket/approval)
   - Check for follow-up actions
   - Mark as reviewed in system
3. For WARNING events:
   - Review in aggregate
   - Flag suspicious patterns
   - Document any anomalies
4. Update review notes in audit system

**Query**:
```python
from modules.firm.audit import AuditEvent
from datetime import timedelta
from django.utils import timezone

last_week = timezone.now() - timedelta(days=7)
events = AuditEvent.objects.filter(
    timestamp__gte=last_week,
    severity__in=[AuditEvent.SEVERITY_WARNING, AuditEvent.SEVERITY_CRITICAL],
    reviewed_at__isnull=True
).order_by('-timestamp')
```

### Monthly Review (All Events)

**Schedule**: First Monday of each month, 2:00 PM
**Duration**: 1-2 hours
**Attendees**: Security Team Lead + Compliance Officer + Platform Ops Lead

**Procedure**:
1. Review statistics for all event categories
2. Analyze trends (increasing/decreasing patterns)
3. Review sample of INFO events (1% random)
4. Reconcile billing events with finance team
5. Update retention policies if needed
6. Generate compliance report

**Metrics to Track**:
- Total events by category
- Critical events: count and resolution time
- Average review lag (time from event to review)
- Unreviewed events over 30 days old
- Break-glass session count and average duration

## Escalation Procedures

### Level 1: Routine Anomaly

**Examples**: Single failed login, minor config change

**Action**:
1. Security Ops reviews within 24 hours
2. Document findings in review notes
3. No escalation if explainable

### Level 2: Suspicious Pattern

**Examples**: Multiple failed logins, unusual permission changes

**Action**:
1. Security Ops investigates immediately
2. Notify Security Team Lead
3. Freeze affected accounts if needed
4. Document in incident tracking system

### Level 3: Confirmed Incident

**Examples**: Unauthorized break-glass, confirmed breach

**Action**:
1. Activate Incident Response Team
2. Notify CTO + Affected Firm (if applicable)
3. Follow incident response playbook
4. Preserve all audit logs (legal hold)
5. Post-incident review required

### Level 4: Legal/Compliance Issue

**Examples**: Improper purge, data breach, regulatory violation

**Action**:
1. Notify Legal + Compliance Officer immediately
2. Activate legal hold on all related audit events
3. Engage external counsel if needed
4. Regulatory notification (GDPR, CCPA, etc.)
5. Executive briefing required

## Review Tracking

### Marking Events as Reviewed

```python
from modules.firm.audit import AuditEvent
from django.utils import timezone

event = AuditEvent.objects.get(id=event_id)

# Platform operator review
event.reviewed_at = timezone.now()
event.reviewed_by = request.user
event.review_notes = """
Reviewed break-glass activation for Ticket #12345.
Reason verified with customer support.
Access lasted 25 minutes (within 30min limit).
No anomalies detected.
"""
event.save(update_fields=['reviewed_at', 'reviewed_by', 'review_notes'])
```

**Note**: Only `reviewed_*` fields can be updated (immutability exception).

### Review Metrics Dashboard (Future - Tier 4)

Planned dashboard showing:
- Events pending review (by category)
- Average review lag time
- Critical events in last 7/30/90 days
- Top actors by event count
- Firms with most audit activity

## Retention After Review

Reviewed events follow same retention as unreviewed:
- Event data retained per category retention policy
- Review metadata (reviewed_at, reviewed_by, notes) retained with event
- Reviewed events can be re-reviewed if new information emerges

## Compliance Reporting

### Quarterly Audit Report

Generated for executive review:
- Total events by category and severity
- Critical events: count, resolution status
- Break-glass usage: frequency, duration, purpose
- Purge requests: count, legal basis
- Anomalies detected and resolved
- Review coverage: % of events reviewed on time

### Annual Compliance Report

For external auditors:
- Full year event statistics
- Break-glass access justification summary
- Purge operations with legal documentation
- Security incidents and resolution
- Policy compliance rate

## Training Requirements

### Platform Operators

**Frequency**: Onboarding + Annual Refresher

**Topics**:
- How to review audit events
- Recognizing suspicious patterns
- Escalation procedures
- Privacy and confidentiality

### Security Team

**Frequency**: Quarterly

**Topics**:
- Threat detection in audit logs
- Incident response procedures
- New attack patterns
- Tool updates

## Next Steps

### Implementation (Tier 3)
- ✅ Define ownership structure
- ✅ Define review cadence
- ✅ Define escalation paths
- [ ] Set up alert integrations (PagerDuty, Slack)
- [ ] Create review dashboard (basic)
- [ ] Train platform operators

### Enhancement (Tier 4)
- [ ] Automated anomaly detection
- [ ] Real-time dashboards
- [ ] Firm-level audit access
- [ ] Compliance report generation

### Future (Tier 5)
- [ ] Machine learning for threat detection
- [ ] SIEM integration
- [ ] Predictive analytics
- [ ] Automated incident response
