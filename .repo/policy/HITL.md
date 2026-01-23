# Human-In-The-Loop (HITL) System

This document defines the Human-In-The-Loop (HITL) system for handling external integrations, clarifications, risks, and unknowns.

## Purpose

The HITL system ensures critical decisions involve human oversight and approval. When automated systems encounter uncertainty, risk, or external dependencies, HITL provides the safety net.

## Storage Model

**Model**: `split_same_folder`

### Storage Locations

- **Index**: `/.repo/policy/HITL.md` (this file)
- **Items Directory**: `/.repo/hitl/`
- **Active Items**: `/.repo/hitl/active/`
- **Resolved Items**: `/.repo/hitl/resolved/`

### Item Naming Convention

```
/.repo/hitl/active/HITL-{YYYY-MM-DD}-{short-description}.md
/.repo/hitl/resolved/HITL-{YYYY-MM-DD}-{short-description}-resolved.md
```

Examples:
- `/.repo/hitl/active/HITL-2024-01-15-dependency-vulnerability.md`
- `/.repo/hitl/resolved/HITL-2024-01-10-external-api-integration-resolved.md`

---

## Sync Model

**Model**: `auto_sync_pr_and_hitl`

### How Auto-Sync Works

1. **Creation**: HITL item automatically created when trigger detected
2. **Linking**: HITL item linked to PR (stored in PR description and HITL metadata)
3. **Status Sync**: HITL status syncs with PR status
4. **Merge Block**: PR cannot merge until HITL item is resolved
5. **Resolution**: HITL resolution automatically updates PR
6. **Archive**: Resolved HITL items moved to resolved folder

### Sync States

| PR State | HITL State | Action Required |
|----------|------------|-----------------|
| Open | Active | Human review and decision |
| Open | Resolved - Approved | PR can proceed to merge |
| Open | Resolved - Rejected | PR must be closed or reworked |
| Merged | Resolved - Approved | HITL archived |
| Closed | Resolved - Cancelled | HITL archived |

---

## External System Detection

**Detection**: `keywords_plus_manifest_plus_change_type`

### Keyword Detection

These keywords in code or PR description trigger HITL:

**External Services**:
- `fetch('http://external`
- `axios.get('http://third-party`
- API calls to domains not in whitelist
- Webhook handlers
- OAuth integrations

**Data Privacy**:
- `PII`, `PersonalData`, `SensitiveInformation`
- Email, phone, address collection
- GDPR, CCPA mentions

**Security**:
- `password`, `secret`, `apiKey`, `token`
- Authentication changes
- Authorization changes
- Cryptographic operations

**Financial**:
- `payment`, `billing`, `charge`, `refund`
- Transaction processing
- Money calculations

**Infrastructure**:
- `deploy`, `production`, `environment`
- Database migrations
- Configuration changes

### Manifest Detection

External systems listed in `repo.manifest.yaml` trigger HITL:

```yaml
external_systems:
  - name: "Stripe"
    type: "payment"
    hitl_required: true
    approved_by: "finance@example.com"
  
  - name: "SendGrid"
    type: "email"
    hitl_required: true
    approved_by: "ops@example.com"
  
  - name: "Auth0"
    type: "authentication"
    hitl_required: true
    approved_by: "security@example.com"
```

### Change Type Detection

These change types automatically trigger HITL:

1. **Authentication/Authorization**: Any changes to login, permissions, RBAC
2. **Data Schema**: Database migrations, model changes
3. **External API Integration**: New third-party service
4. **Payment Processing**: Any financial transaction code
5. **File Upload**: File handling endpoints
6. **Configuration**: Environment or infrastructure changes
7. **Security**: Cryptography, secrets, security controls
8. **PII Collection**: New personal data collection

---

## HITL Triggers

### When HITL Is Required

**Automatic Triggers**:
1. External system integration detected
2. Security baseline violation
3. Dependency vulnerability (always_hitl policy)
4. Explicit UNKNOWN declared
5. Risk level marked as High or Critical
6. Cross-domain boundary violation
7. Production deployment
8. Database migration

**Manual Triggers**:
- Developer declares uncertainty
- Complex architectural decision
- Unclear requirements
- Ambiguous specifications
- Need for stakeholder approval

---

## HITL Item Template

```markdown
# HITL-2024-01-15-external-api-integration

## Status
- [ ] Active
- [ ] Under Review
- [ ] Resolved - Approved
- [ ] Resolved - Rejected
- [ ] Resolved - Cancelled

## Metadata
- **Created**: 2024-01-15
- **Author**: @username
- **PR**: #234
- **Type**: External Integration
- **Priority**: High
- **Assigned To**: security@example.com

## Context

### What Needs Human Decision
[Clear description of what requires human input]

### Why HITL Was Triggered
[Automatic trigger or manual reason]

### Current State
[What has been done so far]

### Options Considered
1. Option A: [Description]
   - Pros: [List]
   - Cons: [List]
   
2. Option B: [Description]
   - Pros: [List]
   - Cons: [List]

## Questions for Human

1. [Specific question requiring human judgment]
2. [Another question]

## Impact Analysis

**Scope**: [What parts of system are affected]
**Risk Level**: 🔴 High | 🟡 Medium | 🟢 Low
**Users Affected**: [Percentage or description]
**Rollback Complexity**: Easy | Medium | Hard

## Recommendation

[Agent's recommendation if applicable, or "UNKNOWN - Human decision required"]

## Security Considerations

[Any security implications]

## Compliance Considerations

[GDPR, CCPA, SOC2, etc.]

## Decision

**Date**: [YYYY-MM-DD]
**Decided By**: [Name/Email]
**Decision**: Approved | Rejected | Needs More Info

**Rationale**:
[Why this decision was made]

**Conditions** (if approved):
- [ ] Condition 1
- [ ] Condition 2

**Follow-Up Actions**:
- [ ] Action 1
- [ ] Action 2

## Resolution

**Resolved Date**: [YYYY-MM-DD]
**Resolution**: [Summary of how this was resolved]
**PR Status**: Merged | Closed | Pending

## Lessons Learned

[What was learned from this HITL item]

## Related Documents

- PR: #234
- ADR: ADR-XXX (if applicable)
- Security Review: [Link]
```

---

## HITL Workflow

### 1. Detection Phase

```
Trigger Detected → HITL Item Created → Notification Sent
```

**Automatic Creation**:
- CI/CD detects trigger (keyword, manifest, change type)
- HITL item generated from template
- Assigned to appropriate reviewer
- PR status updated to "HITL Required"
- Notification sent to reviewer

### 2. Review Phase

```
Review Assignment → Investigation → Decision Making
```

**Reviewer Actions**:
- Read HITL item context
- Review PR and code changes
- Investigate security/compliance implications
- Consult with stakeholders if needed
- Make decision (Approve, Reject, More Info)

### 3. Resolution Phase

```
Decision Made → HITL Updated → PR Unblocked/Closed → Archive
```

**Resolution Steps**:
- Update HITL item with decision and rationale
- Add conditions if approved with caveats
- Update PR status
- If approved: PR can proceed to merge
- If rejected: PR must be closed or reworked
- Move HITL item to resolved folder

---

## HITL Response SLA

| Priority | Initial Response | Decision | Rationale |
|----------|------------------|----------|-----------|
| Critical | 1 hour | 4 hours | Production down, security breach |
| High | 4 hours | 24 hours | Security risk, external integration |
| Medium | 24 hours | 3 days | Architectural decision, unclear requirements |
| Low | 3 days | 1 week | Documentation, minor clarifications |

### Escalation

If SLA is missed:
1. Automatic reminder sent to reviewer
2. Escalate to manager after 2x SLA
3. Escalate to director after 4x SLA

---

## HITL Categories

### 1. External Integration HITL
- New third-party service
- API integration
- Webhook setup
- OAuth flow

**Assigned To**: Security Team + Tech Lead

### 2. Security HITL
- Vulnerability found
- Security pattern violation
- Cryptographic changes
- Secrets handling

**Assigned To**: Security Team

### 3. Compliance HITL
- PII data collection
- GDPR/CCPA requirements
- Privacy policy changes
- Data retention

**Assigned To**: Legal + Compliance

### 4. Architecture HITL
- Cross-domain dependency
- Major refactoring
- Technology choice
- Design pattern decision

**Assigned To**: Architect + Tech Lead

### 5. Production HITL
- Production deployment
- Database migration
- Infrastructure changes
- Configuration updates

**Assigned To**: DevOps + Tech Lead

### 6. Financial HITL
- Payment processing
- Billing logic
- Refund flows
- Pricing changes

**Assigned To**: Finance + Tech Lead

### 7. Clarification HITL
- Unclear requirements
- Ambiguous specifications
- Unknown constraints
- Need stakeholder input

**Assigned To**: Product Manager

### 8. Risk HITL
- High-risk change
- Complex change
- Multiple unknowns
- Low confidence

**Assigned To**: Tech Lead + Relevant Experts

---

## Human Effort Goal

**Goal**: `minimal; agent does mechanical sync`

### Minimize Human Effort

**Agent Responsibilities**:
- Automatically detect triggers
- Create HITL items from template
- Fill in all known information
- Provide clear context and options
- Sync status between PR and HITL
- Archive resolved items
- Generate follow-up tasks

**Human Responsibilities** (only):
- Make final decision
- Provide judgment on ambiguous situations
- Approve high-risk changes
- Ensure compliance
- Review security implications

### Efficiency Tips

- Provide all context upfront (reduce back-and-forth)
- Include clear options with pros/cons
- Reference relevant documentation
- Show evidence (logs, benchmarks, tests)
- Suggest recommendation when possible
- Make decision criteria explicit

---

## HITL Metrics

### Track These Metrics

- **HITL Items Created**: Count per week/month
- **Response Time**: Time from creation to first response
- **Resolution Time**: Time from creation to resolution
- **Approval Rate**: Percentage approved vs rejected
- **False Positives**: Unnecessary HITL triggers
- **SLA Compliance**: Percentage meeting SLA

### Dashboard

Location: `/.repo/metrics/hitl-dashboard.md`

Updated automatically with each HITL resolution.

---

## HITL Best Practices

### For Developers

1. **Be Explicit**: State unknowns clearly
2. **Provide Context**: Include all relevant information
3. **Show Research**: Document what you've already investigated
4. **Suggest Options**: Provide alternatives with analysis
5. **Respect Process**: Don't bypass HITL for convenience

### For Reviewers

1. **Respond Quickly**: Meet SLA targets
2. **Be Clear**: Provide unambiguous decisions
3. **Explain Rationale**: Help developers learn
4. **Be Consistent**: Apply policies uniformly
5. **Document Lessons**: Capture learnings for future

### For System

1. **Reduce False Positives**: Refine detection rules
2. **Improve Templates**: Make HITL items clearer
3. **Automate**: More mechanical work by agents
4. **Track Trends**: Identify patterns to improve process
5. **Learn**: Use historical data to improve decisions

---

## Related Documents

- **Governance**: `/.repo/GOVERNANCE.md`
- **Principles**: `/.repo/policy/PRINCIPLES.md` (P7: UNKNOWN Is First-Class State, P10: Risk Triggers a Stop)
- **Security Baseline**: `/.repo/policy/SECURITY_BASELINE.md`
- **Quality Gates**: `/.repo/policy/QUALITY_GATES.md`
- **Template**: `/.repo/templates/HITL.md`
