# Tier 3: Document Signing Lifecycle & Evidence Retention

**Status**: 📋 DOCUMENTED (Full Implementation: Tier 4)
**Created**: 2025-12-25

## Overview

Signed documents (contracts, proposals, agreements) require immutable signing events and evidence retention that survives content purge.

## Requirements (from NOTES_TO_CLAUDE.md)

> Signature evidence must be retained even if document content is purged.
> Signing metadata (who, when, version) must remain auditable.

## Signing Lifecycle

### 1. Document Preparation
- Document created and finalized
- Version locked (no further edits)
- Hash computed (SHA-256 of content)

### 2. Signature Request
- Signer invited via email
- Expiration date set (e.g., 30 days)
- Audit event: `signature_requested`

### 3. Signing Event
- Signer reviews and signs
- Timestamp captured (ISO 8601 UTC)
- IP address logged (for non-repudiation)
- Document version hash linked

**Audit Event**:
```python
audit.log_event(
    firm=firm,
    category=AuditEvent.CATEGORY_DATA_ACCESS,
    action='document_signed',
    actor=signer,
    target_model='Document',
    target_id=document.id,
    metadata={
        'version_hash': document_version_hash,
        'signed_at_iso': signed_timestamp,
        'ip_address': signer_ip,
        'document_name': document.name  # metadata only
    }
)
```

### 4. Signature Evidence Storage

**What is Stored** (immutable):
- Signer identity (user ID, email)
- Signing timestamp (UTC, immutable)
- Document version hash (links to content at time of signing)
- Signer IP address
- User agent string
- Signature method (electronic, SMS verification, etc.)

**What is NOT Stored**:
- Document content (stored separately, can be purged)
- Plaintext version of document

### 5. Content Purge (If Legally Required)

When document content must be purged:

**Before Purge**:
1. Check if document is signed
2. Extract signing metadata
3. Create tombstone with signature evidence

**Purge Operation**:
```python
from modules.core.purge import purge_helper, PurgedContent

# Collect signature metadata
signature_metadata = {
    'signed_at': str(document.signed_at),
    'signed_by_email': document.signed_by.email,
    'signed_by_name': document.signed_by.get_full_name(),
    'version_hash': document.version_hash,
    'signing_ip': document.signing_ip,
    'signature_method': 'electronic',
}

# Purge content but preserve signature evidence
tombstone = purge_helper.purge_document(
    document=document,
    purged_by=master_admin,
    reason_category=PurgedContent.REASON_GDPR_RIGHT_TO_ERASURE,
    reason_detail="Customer GDPR request #12345",
    legal_reference="GDPR-2025-12345"
)

# Signature evidence preserved in tombstone.signature_metadata
```

**After Purge**:
- Document content: DELETED
- Signature evidence: PRESERVED in tombstone
- Audit trail: INTACT
- Legal proof: "Document X was signed by Y on Z" still available

## Evidence Requirements

### Minimum Signature Metadata

For legal validity, preserve:
1. **Who signed**: Email, full name (at time of signing)
2. **When signed**: UTC timestamp (ISO 8601)
3. **What was signed**: Document version hash
4. **How signed**: Signature method, IP address
5. **Where signed**: Platform URL, firm context

### Hash Linkage

```python
# At signing time
document.version_hash = hashlib.sha256(document.content.encode()).hexdigest()
document.signed_at = timezone.now()
document.signed_by = signer
document.save()

# After purge
# tombstone.signature_metadata contains version_hash
# Proves: "This hash was signed by X at time Y"
# Even though content is purged, signature is provable
```

## Audit Trail

All signature events are logged:

| Event | Category | Severity | Retention |
|-------|----------|----------|-----------|
| `signature_requested` | DATA_ACCESS | INFO | 7 years |
| `document_signed` | DATA_ACCESS | WARNING | 7 years |
| `signature_verified` | DATA_ACCESS | INFO | 7 years |
| `signed_document_purged` | PURGE | CRITICAL | 7 years |

## Compliance

### Legal Validity

Signature evidence survives purge to prove:
- Contract existence
- Mutual agreement
- Timestamp of commitment
- Non-repudiation

### Regulatory Requirements

- **ESIGN Act**: Electronic signatures legally binding
- **GDPR Article 17**: Right to erasure (content deleted, evidence preserved)
- **SOX**: Document retention (metadata sufficient)
- **HIPAA**: Audit trail (who accessed/signed what, when)

## Implementation Status

### Completed (Tier 3)
- ✅ Purge system preserves signature metadata in tombstones
- ✅ Audit system logs signing events
- ✅ Signature metadata schema defined

### Pending (Tier 4)
- [ ] E-signature workflow implementation
- [ ] Version hash computation
- [ ] Signature verification UI
- [ ] Certificate generation (PDF signing)

### Future (Tier 5)
- [ ] Third-party e-sign integration (DocuSign, Adobe Sign)
- [ ] Blockchain anchoring for additional proof
- [ ] Automated compliance reporting
