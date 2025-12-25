# Tier 3: Privacy-First Support Workflows

**Status**: 📋 DOCUMENTED (Implementation: Tier 4)
**Created**: 2025-12-25

## Overview

Support workflows that enable customer issue resolution without exposing content to platform operators.

## Principles

1. **Metadata-Only by Default**: Support uses IDs, timestamps, counts - never content
2. **Break-Glass When Necessary**: Content access only with customer consent + active break-glass
3. **Customer Self-Service First**: Export packages enable customers to resolve issues independently
4. **Secure Intake**: Support tickets limit retention, auto-purge sensitive data

## Workflows

### 1. Metadata-Only Diagnostics

**Use Cases**: 99% of support issues

**Available Data**:
- Error counts, timestamps, HTTP status codes
- Resource IDs (document ID, invoice ID, etc.)
- File sizes, MIME types, upload dates
- User counts, activity patterns
- Billing totals (not line items)

**Example**: "Document upload failing"
- Check: document.id, upload timestamp, file_size, mime_type, error_trace
- NO ACCESS to: document content, file path, S3 key

### 2. Customer Export Package

**Use Case**: Customer needs to self-diagnose or provide to support

**Contents**:
- All metadata in JSON/CSV format
- Document list with IDs, names, dates (NO files)
- Activity logs (who did what, when)
- Invoice summaries (totals, dates, status)
- Error logs (technical details, NO content)

**Implementation** (Tier 4):
- Self-service download from portal
- Expires after 7 days
- Logged in audit system

### 3. Break-Glass Content Access

**Use Case**: Rare cases requiring actual content review

**Requirements**:
- Customer explicit consent (email/phone)
- Active break-glass session with reason
- Time-limited (30 min max)
- All actions audited

**Process**:
1. Customer consents via support ticket
2. Platform operator activates break-glass
3. Issue diagnosed/resolved
4. Session expires automatically
5. Customer notified of access

### 4. Secure Support Ticket Intake

**Retention Policy**:
- Customer-provided content: 30 days max
- After resolution: auto-purge attachments
- Metadata preserved: ticket ID, resolution, timestamp

## Implementation Status

- ✅ Audit system supports break-glass tracking
- ✅ Purge system supports content removal
- [ ] Export package generation (Tier 4)
- [ ] Self-service diagnostic tools (Tier 4)
- [ ] Support dashboard (metadata-only views) (Tier 4)
