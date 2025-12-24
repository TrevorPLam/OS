# Metadata vs. Content Separation (TIER 0)

**Date:** December 24, 2025
**Status:** Implemented (Tier 0.5)
**Authority:** NOTES_TO_CLAUDE.md

---

## Purpose

This document defines the boundary between **customer content** (private, end-to-end encrypted) and **operational metadata** (accessible to platform operators for diagnostics and support).

**CRITICAL PRINCIPLE:**
> Platform operators can NEVER access customer content by default.
> Break-glass access is rare, explicit, time-limited, and fully audited.

---

## Definitions

### Customer Content (Private, E2EE)

Content that represents the **substance** of customer work and communication. Platform operators CANNOT access this without an active break-glass session.

#### Content Models:
- **Documents**: `Document`, `Version`
  - File content (via S3 keys)
  - Document text/body
  - Version change descriptions (future)

- **Communications** (future):
  - `Message.content` / `Message.body`
  - `Comment.text`
  - `Note.body`

- **Billing Context**:
  - `Invoice.line_items` (itemized billing details)
  - Time entry descriptions (work performed)

#### Content Fields:
Any field containing:
- `content`
- `text`
- `body`
- `message`
- `description` (in content contexts)
- `notes` (in client-facing contexts)
- `s3_key`, `bucket_name` (enables content retrieval)
- `line_items` (invoice billing context)

---

### Operational Metadata (Accessible)

Metadata that enables **platform operations, diagnostics, and support** WITHOUT exposing customer content.

#### Metadata Categories:

**1. Identity & Relationships**
- IDs: `id`, `uuid`, `slug`
- Foreign keys: `firm_id`, `client_id`, `user_id`, `project_id`
- Names: `firm.name`, `client.company_name`, `user.email`

**2. Lifecycle & Status**
- Timestamps: `created_at`, `updated_at`, `activated_at`, `expires_at`
- Status: `status`, `is_active`, `is_deleted`
- Counts: `version_number`, `current_users_count`, `current_clients_count`

**3. Technical Metadata**
- File attributes: `file_size`, `mime_type`, `checksum`
- System info: `ip_address`, `user_agent`, `error_trace`
- Performance: `request_duration`, `query_count`

**4. Billing Metadata (Safe)**
- Totals: `invoice.total`, `invoice.amount_paid`, `invoice.amount_due`
- Subscription: `subscription_tier`, `trial_ends_at`
- Payment events: `payment.status`, `payment.amount`, `payment.processor_response` (not content)

**5. Audit & Compliance**
- Actor: `created_by`, `updated_by`, `deleted_by`
- Actions: `action`, `event_type`, `reason` (for platform actions)
- Break-glass: `operator`, `activated_at`, `expires_at`, `reviewed_at`

---

## Permission Enforcement

### Platform Operator (Default)
- **Allowed**: All metadata fields
- **Denied**: All content fields
- **Use Case**: Diagnostics, support, operations

### Break-Glass Operator (Active Session)
- **Allowed**: Metadata + content fields (time-limited)
- **Denied**: Nothing (full access within session scope)
- **Use Case**: Emergency support, legal compliance, incident response

### Firm Users (Normal)
- **Allowed**: All data within their firm scope
- **Denied**: Other firms' data (tenant isolation)

### Client Portal Users
- **Allowed**: Client-scoped data explicitly marked visible
- **Denied**: Internal firm data, other clients' data

---

## Implementation

### 1. Permission Classes

Located in `modules/firm/permissions.py`:

- **`DenyContentAccessByDefault`**: Default-deny for content models
- **`MetadataOnlyAccess`**: Restrict serializer fields to metadata
- **`RequireBreakGlassForContent`**: Strict content endpoint protection

### 2. Model Fields

All content-bearing models should:
- Clearly separate content fields from metadata fields
- Mark content fields in model docstrings
- Use explicit field names (`content`, `body`, `text`)

**Example:**
```python
class Document(models.Model):
    # === METADATA (Platform-visible) ===
    id = models.BigAutoField(primary_key=True)
    firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    # === CONTENT (Platform-denied, requires break-glass) ===
    s3_key = models.CharField(max_length=500)  # Enables content retrieval
    bucket_name = models.CharField(max_length=100)
```

### 3. Serializers (Future)

Future serializers should implement field filtering:

```python
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        # Filter content fields for platform operators
        if is_platform_operator(request.user) and not has_break_glass(request):
            self.fields.pop('s3_key', None)
            self.fields.pop('bucket_name', None)
```

### 4. ViewSets

Apply permissions to content-bearing endpoints:

```python
class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        DenyContentAccessByDefault,  # ← TIER 0
    ]

class DocumentDownloadView(APIView):
    permission_classes = [
        IsAuthenticated,
        RequireBreakGlassForContent,  # ← Strict content protection
    ]
```

---

## Content Encryption (E2EE)

**Status:** NOT YET IMPLEMENTED (Tier 0.5 - blocked)

### Requirements:
1. **Encryption at Rest**: All content fields encrypted in database
2. **Encryption in Transit**: HTTPS/TLS for all API requests
3. **Key Management**:
   - Firm-level encryption keys
   - Keys stored in secrets manager (not database)
   - Platform cannot decrypt without break-glass + key access
4. **Client-Side Encryption** (future):
   - Client portal encrypts before upload
   - Firm decrypts in browser
   - Platform never has plaintext

### Blocked By:
- [ ] Secrets management system (AWS KMS, HashiCorp Vault, etc.)
- [ ] Database field encryption library (django-cryptography, django-encrypted-model-fields)
- [ ] Key rotation policy
- [ ] Client-side encryption SDK

### Next Steps:
1. Choose encryption library (recommend: `django-cryptography`)
2. Set up secrets manager for key storage
3. Implement field-level encryption for content fields
4. Add migration to encrypt existing data
5. Update serializers to decrypt for authorized users
6. Document key rotation procedures

**NOTE:** E2EE implementation is a MAJOR undertaking and should be planned carefully with security audit before production use.

---

## Audit Logging (Future - Tier 3)

When audit system exists:
- Log all break-glass content access
- Record which fields were accessed
- Link to break-glass session
- Immutable audit records
- Retention policy (7+ years for compliance)

---

## Testing

Minimum test coverage required:
- [ ] Platform operator CANNOT access content without break-glass
- [ ] Platform operator CAN access metadata without break-glass
- [ ] Break-glass operator with active session CAN access content
- [ ] Break-glass operator without active session CANNOT access content
- [ ] Firm users can access their own content (normal flow)
- [ ] Serializers filter content fields for platform operators

---

## Compliance & Legal

This separation supports:
- **GDPR**: Data minimization, right to be forgotten
- **HIPAA**: Minimum necessary access (if handling health data)
- **SOC 2**: Logical access controls, segregation of duties
- **Attorney-Client Privilege**: Platform cannot read privileged communications

---

## Questions / Decisions Needed

**Q: Should we encrypt metadata too?**
- A: No. Metadata is needed for operations. Encrypt only content.

**Q: What about document filenames?**
- A: Filenames are metadata (visible to platform). Content is private.

**Q: Can we use platform logging for debugging?**
- A: Yes, but NEVER log content fields. Log IDs, counts, errors only.

**Q: What if a client requests we delete everything?**
- A: Purge content, preserve metadata tombstones (see TIER 3).

---

## Related Documents

- `docs/claude/NOTES_TO_CLAUDE.md` - Authoritative rules
- `docs/tier0/PORTAL_CONTAINMENT.md` - Client portal isolation
- `src/modules/firm/permissions.py` - Permission implementations
- `TODO.md` - Tier 0.5 and Tier 3 tasks

---

**Status Legend:**
- ✅ Implemented: Permission classes, model separation
- 🟡 Partial: Documentation complete, E2EE not implemented
- 🔴 Blocked: E2EE requires secrets management infrastructure
