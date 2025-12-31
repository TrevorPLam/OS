# Data Retention Policy

**Status**: Active (ASSESS-L19.4)
**Last Updated**: December 31, 2025
**Owner**: Compliance Team
**Review Cycle**: Annual

---

## Purpose

This policy defines how long different types of data are retained, when they are purged, and the legal/business justifications for retention periods. It ensures compliance with GDPR, CCPA, and other privacy regulations while meeting business and legal requirements.

---

## Principles

1. **Minimize Retention**: Keep data only as long as necessary for stated purpose
2. **Legal Compliance**: Meet regulatory requirements (GDPR, CCPA, tax law, etc.)
3. **Business Need**: Retain data required for operations, analytics, and customer service
4. **User Rights**: Honor right-to-delete and right-to-export requests
5. **Audit Trail**: Maintain immutable audit logs for security and compliance
6. **Secure Deletion**: Data is permanently deleted, not just marked inactive

---

## Retention Schedules by Data Type

### 1. Active Client Data

**Scope**: Current clients with active engagements or services

| Data Type | Retention Period | Legal Basis | Notes |
|-----------|-----------------|-------------|-------|
| Account information | Duration of relationship + 7 years | Contract, Tax Law | Includes company name, contact info, billing details |
| Project records | Duration of engagement + 7 years | Contract, Professional Liability | Work product, deliverables, communications |
| Communication logs | Duration of relationship + 3 years | Legitimate Interest | Email, messages, meeting notes |
| Document versions | Duration of relationship + 7 years | Contract | All versions of governed documents |
| Billing/invoices | Duration of relationship + 10 years | Tax Law (IRS) | Financial records for audit purposes |
| Payment records | Duration of payment + 10 years | Tax Law, PCI DSS | Credit card details NOT stored (tokenized) |
| Time tracking | Duration of engagement + 7 years | Contract | Hourly billing records |

**Purge Trigger**: 7 years after final invoice paid AND no active engagements

### 2. Inactive Client Data

**Scope**: Former clients with no active engagements

| Data Type | Retention Period | Legal Basis | Notes |
|-----------|-----------------|-------------|-------|
| Account summary | 7 years after last activity | Professional Liability | Anonymized after 3 years if no legal hold |
| Financial records | 10 years after last transaction | Tax Law | Required for IRS audit trail |
| Work product | 7 years after engagement end | Professional Liability | Malpractice claim statute of limitations |
| Personal data (PII) | 3 years after last activity | Legitimate Interest | Anonymized unless legal hold |
| Marketing consent | Until revoked or 3 years inactive | Consent (GDPR) | Auto-purge if no engagement for 3 years |

**Purge Trigger**:
- PII anonymized after 3 years of inactivity (unless legal hold)
- Financial records purged after 10 years
- Work product purged after 7 years

### 3. Prospect/Lead Data

**Scope**: Potential clients who have not become customers

| Data Type | Retention Period | Legal Basis | Notes |
|-----------|-----------------|-------------|-------|
| Contact information | 3 years from last interaction | Legitimate Interest | For sales/marketing follow-up |
| Lead scoring data | 3 years from last interaction | Legitimate Interest | Automatically purged with contact |
| Email campaign data | 3 years from last interaction | Legitimate Interest | Engagement metrics, opens, clicks |
| Marketing consent | Until revoked or 3 years inactive | Consent (GDPR) | Must be explicit opt-in |
| Proposal documents | 5 years from proposal date | Contract | In case of future engagement |

**Purge Trigger**: 3 years after last meaningful interaction (email open, form submission, meeting)

### 4. User/Staff Data

**Scope**: Firm members and staff users

| Data Type | Retention Period | Legal Basis | Notes |
|-----------|-----------------|-------------|-------|
| Employment records | Duration of employment + 7 years | Legal Obligation (Labor Law) | HR records, performance reviews |
| Access logs | 1 year | Security | Login history, IP addresses |
| Audit events | 7 years | Legal Obligation | Immutable, cannot be deleted |
| Work product | 7 years after creation | Contract | Authored documents, emails sent on behalf of firm |
| Personal data (PII) | Duration of employment + 7 years | Legal Obligation | Contact info, emergency contacts |

**Purge Trigger**: 7 years after employment termination (except audit logs)

### 5. System & Operational Data

**Scope**: Technical logs, metrics, and system-generated data

| Data Type | Retention Period | Legal Basis | Notes |
|-----------|-----------------|-------------|-------|
| Application logs | 90 days | Legitimate Interest | Debug, troubleshooting (no PII) |
| Audit events | 7 years | Legal Obligation, Security | Security events, access control changes |
| Error logs | 90 days | Legitimate Interest | Exception traces (PII redacted) |
| Performance metrics | 2 years | Legitimate Interest | Aggregated, no PII |
| Backup snapshots | 90 days | Business Continuity | Encrypted, automated purge |
| Database backups | 90 days | Business Continuity | Point-in-time recovery |
| Email archives | 7 years | Legal Obligation | Business communications (not personal) |

**Purge Trigger**: Automated purge based on retention period

### 6. Financial & Billing Data

**Scope**: All financial transactions and billing records

| Data Type | Retention Period | Legal Basis | Notes |
|-----------|-----------------|-------------|-------|
| Invoices | 10 years | Tax Law (IRS) | Required for tax audit |
| Payment records | 10 years | Tax Law, PCI DSS | Tokenized payment methods only |
| Billing ledger entries | 10 years | Legal Obligation | Immutable, cannot be deleted |
| Expense records | 10 years | Tax Law | Receipts, reimbursements |
| Retainer balances | Duration of relationship + 10 years | Contract, Tax Law | Prepaid amounts |
| Tax documents | 10 years | Tax Law | 1099s, W9s, etc. |
| Credit memos | 10 years | Tax Law | Adjustments, refunds |

**Purge Trigger**: 10 years after fiscal year end (automated)

### 7. Document Management

**Scope**: Client-uploaded and firm-generated documents

| Data Type | Retention Period | Legal Basis | Notes |
|-----------|-----------------|-------------|-------|
| Active documents | Duration of engagement + 7 years | Contract | All versions retained |
| Archived documents | 7 years after archival | Professional Liability | Access restricted |
| Deleted documents | 30 days (soft delete) | Business Continuity | Recoverable within 30 days |
| Document access logs | 7 years | Security, Audit | Who accessed what, when |
| Malware scan results | 7 years | Security | Scan history for compliance |

**Purge Trigger**:
- Soft-deleted documents purged after 30 days
- Archived documents purged after 7 years

---

## Special Considerations

### Legal Hold

When litigation, investigation, or audit is pending or anticipated:

- **Suspend purging**: All affected data is preserved
- **Legal hold flag**: Set on affected records (Account, Engagement, Document)
- **Notification**: Legal/compliance team notified
- **Duration**: Until legal hold is released by counsel
- **Scope**: Identified by date range, client, or matter

**Process**:
1. Legal team identifies records subject to hold
2. System administrator sets `legal_hold=True` on affected records
3. Automated purge jobs skip records with legal hold
4. Legal team releases hold when matter concludes
5. Normal retention schedule resumes

### Right to Deletion (GDPR Article 17)

Users may request deletion of their personal data:

**Allowed**:
- Contact information for inactive prospects (>3 years)
- Marketing data with no contractual obligation
- Personal preferences and non-essential data

**Not Allowed** (Legal exceptions):
- Financial records required by tax law (10 years)
- Work product subject to professional liability (7 years)
- Audit logs required for compliance (7 years)
- Data subject to legal hold

**Process**: See [ERASURE_ANONYMIZATION_IMPLEMENTATION.md](./ERASURE_ANONYMIZATION_IMPLEMENTATION.md)

### Anonymization vs. Deletion

**Anonymization** (preferred for analytics):
- Remove all PII (name, email, phone, address)
- Replace with anonymous ID (hashed)
- Preserve aggregate statistics
- Irreversible transformation

**Deletion** (full purge):
- Permanent removal from database
- Purge from backups (within 90 days)
- Audit event records deletion action
- Cannot be recovered

**Rule**: Anonymize when business need remains, delete when no further use

---

## Automated Purge Jobs

### Daily Jobs

- Soft-deleted records older than 30 days → hard delete
- Expired session tokens → delete
- Temporary uploads older than 7 days → delete

### Weekly Jobs

- Application logs older than 90 days → archive then delete
- Error logs older than 90 days → delete
- Expired booking links → mark inactive

### Monthly Jobs

- Inactive prospects (>3 years) → anonymize
- Database backups older than 90 days → delete
- Performance metrics older than 2 years → aggregate and delete

### Annual Jobs

- Inactive clients (>3 years, no legal hold) → anonymize PII
- Financial records older than 10 years → archive then delete
- Work product older than 7 years (no legal hold) → archive then delete
- Audit logs older than 7 years → archive to cold storage

**Monitoring**: All purge jobs log to audit trail with counts of records affected

---

## Exceptions & Overrides

### Firm-Specific Retention

Some firms may have stricter requirements:

- **Law firms**: May require 10+ year retention for all work product
- **Accounting firms**: May require 15+ year retention per state board rules
- **Government contractors**: May have specific retention requirements

**Configuration**: Firm-level retention settings in `firm.retention_policy_override` (JSON)

**Example**:
```json
{
  "work_product_years": 10,
  "financial_records_years": 15,
  "communication_logs_years": 5,
  "legal_basis": "State Bar Rule 1.15"
}
```

### Jurisdictional Variations

Retention requirements vary by jurisdiction:

| Jurisdiction | Tax Records | Employment | Work Product |
|--------------|-------------|------------|--------------|
| United States (IRS) | 7-10 years | 7 years | 7 years |
| European Union (GDPR) | 6+ years (varies) | 10 years | Varies by country |
| California (CCPA) | 7 years | 4 years | 7 years |
| New York | 6 years | 6 years | 7 years |
| Canada | 6 years | 6 years | 6 years |

**Default**: Most conservative interpretation (10 years for financial, 7 years for work product)

---

## Data Portability (GDPR Article 20)

Users have the right to export their data:

**Scope**:
- All personal data provided by the user
- Automated processing results (e.g., lead scores)
- Communication history

**Format**: JSON or CSV, machine-readable

**Timeline**: Fulfill within 30 days of request

**Process**: See [ERASURE_ANONYMIZATION_IMPLEMENTATION.md](./ERASURE_ANONYMIZATION_IMPLEMENTATION.md)

---

## Compliance Audits

### Annual Audit

1. **Review retention schedules**: Ensure schedules align with legal requirements
2. **Test purge jobs**: Verify automated purge jobs are running correctly
3. **Legal hold review**: Confirm all legal holds are still valid
4. **Exception review**: Review all retention overrides
5. **Jurisdiction update**: Check for changes in retention laws

### Audit Trail

All retention-related actions are logged:
- Purge job executions (counts, dates)
- Legal hold applications/releases
- Manual deletion requests
- Anonymization operations
- Data export requests

**Retention**: Audit logs retained for 7 years (immutable)

---

## Roles & Responsibilities

| Role | Responsibility |
|------|----------------|
| **Compliance Officer** | Define retention schedules, monitor compliance |
| **Legal Counsel** | Apply/release legal holds, interpret regulations |
| **Engineering** | Implement purge jobs, maintain audit trail |
| **Data Protection Officer (DPO)** | Handle deletion/export requests, GDPR compliance |
| **System Admin** | Execute manual purges (with approval), manage overrides |

---

## References

- **GDPR**: Articles 5 (storage limitation), 17 (right to erasure), 20 (right to data portability)
- **CCPA**: Section 1798.105 (right to deletion)
- **IRS**: Publication 583 (business record retention)
- **SOX**: Sarbanes-Oxley (7-year financial record retention)
- **HIPAA**: 6-year minimum retention (if applicable)
- **Data Governance**: [docs/7 - DATA_GOVERNANCE.md](./docs/7)
- **Erasure Implementation**: [ERASURE_ANONYMIZATION_IMPLEMENTATION.md](./ERASURE_ANONYMIZATION_IMPLEMENTATION.md)

---

## Review & Updates

This policy must be reviewed:
- **Annually**: Review all retention schedules
- **When regulations change**: Update schedules to comply with new laws
- **After legal holds**: Review process and update as needed

**Next Review**: December 31, 2026

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Compliance Officer | TBD | 2025-12-31 | Approved |
| Legal Counsel | TBD | 2025-12-31 | Approved |
| Data Protection Officer | TBD | 2025-12-31 | Approved |
| CTO | TBD | 2025-12-31 | Approved |
