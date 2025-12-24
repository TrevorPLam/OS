# Platform Privacy & Encryption Strategy (TIER 0.5)

## Overview

This document outlines the privacy-first architecture for the ConsultantPro platform, implementing metadata-only access for platform operators and end-to-end encryption (E2EE) for customer content.

## Platform Roles

### 1. Firm User (Default)
- Regular users within a consulting firm
- Full access to their firm's data
- No platform-level access

### 2. Platform Operator
- Metadata-only access for operations and support
- **CANNOT** read customer content
- Can view:
  - Billing metadata (totals, dates, status)
  - Subscription state
  - Audit logs
  - Operational metadata (counts, timestamps, error traces)
- **CANNOT** view:
  - Document content
  - Messages, comments, notes
  - Invoice line item descriptions
  - Project/task descriptions
  - Any customer-provided content

### 3. Break-Glass Operator
- Can activate time-limited break-glass sessions
- Requires:
  - Explicit activation
  - Reason string (mandatory)
  - Time limit (auto-expiry)
  - Firm consent OR emergency policy
- All actions logged immutably
- Content access only during active session

## Content Field Protection

### Identified Content Fields

Content fields are explicitly marked on all models using the `CONTENT_FIELDS` attribute:

#### Documents Module
- `Folder.description`
- `Document.description`, `Document.s3_key`, `Document.s3_bucket`
- `Version.change_summary`, `Version.s3_key`, `Version.s3_bucket`

#### CRM Module
- `Lead.notes`
- `Prospect.notes`
- `Campaign.description`
- `Proposal.description`
- `Contract.description`, `Contract.notes`

#### Finance Module
- `Invoice.line_items`, `Invoice.notes`
- `Bill.description`, `Bill.line_items`
- `LedgerEntry.description`

#### Projects Module
- `Project.description`, `Project.notes`
- `Task.description`
- `TimeEntry.description`

### Enforcement Mechanism

1. **Permission Classes**: `DenyPlatformContentAccess` permission explicitly denies platform operators
2. **Serializer Filtering**: `MetadataOnlyMixin` removes content fields from responses
3. **Admin Interface**: UserProfile admin restricted to superusers only
4. **Break-Glass Gating**: Active session required for break-glass content access

## End-to-End Encryption (E2EE) Strategy

### Current State (TIER 0.5)
- Content fields identified and marked
- Platform operator access explicitly denied
- Break-glass framework in place

### Planned Implementation (Future Tier)

#### Encryption Approach
1. **Client-Side Encryption**
   - Content encrypted in browser before transmission
   - Firm-specific encryption keys
   - Zero-knowledge architecture (platform cannot decrypt)

2. **Key Management**
   - Per-firm encryption keys
   - Keys never stored on platform servers
   - Key derivation from firm credentials
   - Optional: Hardware security modules (HSM)

3. **Encrypted Fields**
   - All content fields marked in `CONTENT_FIELDS`
   - S3 objects encrypted at rest
   - Database fields encrypted (application-level)

4. **Metadata Separation**
   - Metadata remains unencrypted for operations
   - Content encrypted, metadata searchable
   - Audit logs never contain content

#### Break-Glass Decryption
1. Firm owner provides consent (includes key access)
2. Break-glass operator activates session
3. Temporary key access granted (time-limited)
4. All decryption actions logged
5. Key access revoked on session expiry

### Implementation Checklist (Future)
- [ ] Select encryption library (e.g., libsodium, nacl)
- [ ] Implement client-side encryption SDK
- [ ] Build key management service
- [ ] Add encrypted field type to Django models
- [ ] Update serializers to handle encryption
- [ ] Add decryption for break-glass sessions
- [ ] Test key rotation procedures
- [ ] Document recovery procedures

## Testing & Verification

### Automated Tests
- `tests/firm/test_platform_privacy.py` - Platform privacy enforcement tests
- Tests verify:
  - UserProfile auto-creation
  - Platform operator content denial
  - Break-glass session requirements
  - Content field marking

### Manual Verification
1. Create platform operator user
2. Attempt to access content endpoints
3. Verify 403 Forbidden responses
4. Activate break-glass session
5. Verify content access granted during session
6. Verify content access denied after expiry

## Compliance & Audit

### Audit Events (to be implemented in TIER 3)
- Break-glass activation
- Break-glass expiry/revocation
- Platform operator access attempts
- Content field access (when/by whom)

### Retention Policy
- Break-glass sessions: Permanent retention
- Audit logs: 7 years minimum
- Encryption keys: Secure deletion on firm offboarding

## References

- NOTES_TO_CLAUDE.md - Authoritative rules
- TIER0_FOUNDATIONAL_SAFETY.md - Tier 0 requirements
- modules/firm/permissions.py - Permission classes
- modules/firm/content_privacy.py - Content utilities
