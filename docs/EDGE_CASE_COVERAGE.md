# Edge Case Coverage Implementation (DOC-23.1)

**Status:** ✅ Complete
**Last Updated:** December 30, 2025
**Complies with:** docs/03-reference/requirements/DOC-23.md EDGE_CASES_CATALOG

---

## Overview

This document describes the implementation of DOC-23.1: Comprehensive edge case coverage from the EDGE_CASES_CATALOG (docs/03-reference/requirements/DOC-23.md).

The implementation provides:
1. **Test coverage** for all edge cases listed in docs/03-reference/requirements/DOC-23.md
2. **Implementation verification** that edge cases are handled correctly
3. **Regression prevention** through automated test suite

---

## 1. Edge Case Categories (docs/03-reference/requirements/DOC-23.md)

### 1.1 Recurrence (docs/03-reference/requirements/DOC-23.md section 1)

| Edge Case | Status | Test Location | Implementation |
|-----------|--------|---------------|----------------|
| DST spring forward: missing local times | ✅ Tested | `test_edge_cases.py::RecurrenceEdgeCasesTest.test_dst_spring_forward_missing_time` | `modules/recurrence/services.py::RecurrenceGenerator` |
| DST fall back: ambiguous local times | ✅ Tested | `test_edge_cases.py::RecurrenceEdgeCasesTest.test_dst_fall_back_ambiguous_time` | `modules/recurrence/services.py::RecurrenceGenerator` |
| leap year Feb 29 rules | ✅ Tested | `test_edge_cases.py::RecurrenceEdgeCasesTest.test_leap_year_feb_29_rules` | `modules/recurrence/services.py::RecurrenceGenerator` |
| pause mid-period then resume (no duplicates) | ✅ Tested | `test_edge_cases.py::RecurrenceEdgeCasesTest.test_pause_mid_period_then_resume_no_duplicates` | `modules/recurrence/models.py::RecurrenceRule.pause/resume` |
| backfill window overlaps previously generated periods | ✅ Tested | `test_edge_cases.py::RecurrenceEdgeCasesTest.test_backfill_window_overlaps_previously_generated` | `modules/recurrence/backfill.py::BackfillService` |

**Implementation Notes:**
- DST handling uses pytz timezone-aware datetime calculations
- Leap year handling: Feb 29 yearly recurrences either skip non-leap years or use Feb 28
- Pause/resume uses RecurrenceGeneration dedupe ledger to prevent duplicates
- Backfill service checks existing generations before creating new ones

### 1.2 Email Ingestion (docs/03-reference/requirements/DOC-23.md section 2)

| Edge Case | Status | Test Location | Implementation |
|-----------|--------|---------------|----------------|
| shared email address across multiple accounts | ✅ Tested | `test_edge_cases.py::EmailIngestionEdgeCasesTest.test_shared_email_address_across_multiple_accounts` | `modules/email_ingestion/staleness_service.py::StalenessDetector` |
| thread contains mixed clients | ✅ Tested | `test_edge_cases.py::EmailIngestionEdgeCasesTest.test_thread_contains_mixed_clients` | `modules/email_ingestion/staleness_service.py::StalenessDetector` |
| subject changes mid-thread | ✅ Tested | `test_edge_cases.py::EmailIngestionEdgeCasesTest.test_subject_changes_mid_thread` | `modules/email_ingestion/staleness_service.py::StalenessDetector` |
| attachments renamed across replies | ✅ Tested | `test_edge_cases.py::EmailIngestionEdgeCasesTest.test_attachments_renamed_across_replies` | `modules/email_ingestion/models.py::EmailAttachment` |
| re-ingestion after connection reset (idempotency) | ✅ Tested | `test_edge_cases.py::EmailIngestionEdgeCasesTest.test_reingestion_after_connection_reset_idempotency` | `modules/email_ingestion/services.py::EmailIngestionService` |

**Implementation Notes:**
- Staleness detection applies penalties for multi-account contacts (-0.25), mixed client threads (-0.35), subject changes (-0.15)
- Attachments are tracked separately even if renamed; each creates its own EmailAttachment record
- Idempotency is enforced by unique constraint on (connection, external_message_id)

### 1.3 Permissions (docs/03-reference/requirements/DOC-23.md section 3)

| Edge Case | Status | Test Location | Implementation |
|-----------|--------|---------------|----------------|
| portal identity linked to multiple accounts; account switcher scope correctness | ✅ Tested | `test_edge_cases.py::PermissionsEdgeCasesTest.test_portal_identity_linked_to_multiple_accounts` | `modules/clients/models.py::PortalIdentity` |
| document linked to multiple objects with mixed portal visibility | ✅ Tested | `test_edge_cases.py::PermissionsEdgeCasesTest.test_document_linked_to_multiple_objects_mixed_visibility` | `modules/documents/models.py::Document.visibility` |
| role changes mid-session; token refresh and cached permissions | ✅ Tested | `test_edge_cases.py::PermissionsEdgeCasesTest.test_role_changes_mid_session_permission_refresh` | User model + token refresh flow |

**Implementation Notes:**
- PortalIdentity allows multiple client associations; queries must filter by active client context
- Document visibility field controls portal access; "internal" docs are filtered out
- Role changes require token refresh to update cached permissions

### 1.4 Billing Ledger (docs/03-reference/requirements/DOC-23.md section 4)

| Edge Case | Status | Test Location | Implementation |
|-----------|--------|---------------|----------------|
| partial payments across multiple invoices | ✅ Tested | `test_edge_cases.py::BillingLedgerEdgeCasesTest.test_partial_payments_across_multiple_invoices` | `modules/finance/billing_ledger.py::allocate_payment_to_invoice` |
| retainer partially applied, then invoice voided (compensation entries) | ✅ Tested | `test_edge_cases.py::BillingLedgerEdgeCasesTest.test_retainer_partially_applied_then_invoice_voided` | `modules/finance/billing_ledger.py::BillingAllocation` |
| idempotency key reuse across retries | ✅ Tested | `test_edge_cases.py::BillingLedgerEdgeCasesTest.test_idempotency_key_reuse_across_retries` | `modules/finance/billing_ledger.py::BillingLedgerEntry` |
| allocation rounding/currency precision | ✅ Tested | `test_edge_cases.py::BillingLedgerEdgeCasesTest.test_allocation_rounding_currency_precision` | Decimal precision with 2 decimal places |

**Implementation Notes:**
- Partial payments use BillingAllocation to track payment → invoice mappings
- Multiple allocations supported; get_unapplied_amount() calculates remaining balance
- Idempotency enforced by unique constraint on (firm, entry_type, idempotency_key)
- Decimal field type ensures currency precision without rounding errors

### 1.5 Documents (docs/03-reference/requirements/DOC-23.md section 5)

| Edge Case | Status | Test Location | Implementation |
|-----------|--------|---------------|----------------|
| concurrent uploads without locks (should create versions or block) | ✅ Tested | `test_edge_cases.py::DocumentsEdgeCasesTest.test_concurrent_uploads_without_locks_create_versions` | `modules/documents/models.py::DocumentVersion` |
| lock override by admin (audit) | ✅ Tested | `test_edge_cases.py::DocumentsEdgeCasesTest.test_lock_override_by_admin_creates_audit` | `modules/documents/models.py::DocumentLock.override_lock` |
| malware scan pending: portal download blocked | ✅ Tested | `test_edge_cases.py::DocumentsEdgeCasesTest.test_malware_scan_pending_portal_download_blocked` | `modules/documents/malware_scan.py::DownloadPolicy` |
| signed URL reuse after expiry | ✅ Tested | `test_edge_cases.py::DocumentsEdgeCasesTest.test_signed_url_reuse_after_expiry` | S3 presigned URL expiry (production S3 config) |

**Implementation Notes:**
- Concurrent uploads create new DocumentVersion records (versioning system)
- DocumentLock.override_lock() creates audit event "document_lock_overridden"
- DownloadPolicy.can_download_version() blocks portal downloads for pending/flagged scans
- Signed URLs expire after configured TTL (typically 15 minutes); reuse is prevented by S3

---

## 2. Test Organization

### 2.1 Test File Structure

```
src/tests/
├── edge_cases/
│   ├── __init__.py
│   └── test_edge_cases.py  # NEW: Comprehensive edge case tests
├── contract_tests.py       # Existing: Contract tests (DOC-22.1)
└── [other test directories]
```

### 2.2 Test Classes

| Test Class | Coverage | Lines |
|------------|----------|-------|
| `RecurrenceEdgeCasesTest` | DST, leap year, pause/resume, backfill | 5 tests |
| `EmailIngestionEdgeCasesTest` | Shared addresses, mixed threads, attachments | 5 tests |
| `PermissionsEdgeCasesTest` | Portal multi-account, visibility, role changes | 3 tests |
| `BillingLedgerEdgeCasesTest` | Partial payments, retainer compensation, precision | 4 tests |
| `DocumentsEdgeCasesTest` | Concurrent uploads, locks, malware, URLs | 4 tests |
| **Total** | **21 edge case tests** | **~800 lines** |

---

## 3. Running Edge Case Tests

### 3.1 Run All Edge Case Tests

```bash
# Run entire edge case test suite
pytest src/tests/edge_cases/test_edge_cases.py -v

# Run specific category
pytest src/tests/edge_cases/test_edge_cases.py::RecurrenceEdgeCasesTest -v
pytest src/tests/edge_cases/test_edge_cases.py::EmailIngestionEdgeCasesTest -v
pytest src/tests/edge_cases/test_edge_cases.py::PermissionsEdgeCasesTest -v
pytest src/tests/edge_cases/test_edge_cases.py::BillingLedgerEdgeCasesTest -v
pytest src/tests/edge_cases/test_edge_cases.py::DocumentsEdgeCasesTest -v

# Run specific test
pytest src/tests/edge_cases/test_edge_cases.py::RecurrenceEdgeCasesTest::test_dst_spring_forward_missing_time -v
```

### 3.2 Run All Tests (Edge Cases + Contract Tests)

```bash
# Run both edge case and contract tests
pytest src/tests/edge_cases/ src/tests/contract_tests.py -v
```

---

## 4. Edge Case Handling Patterns

### 4.1 DST Handling (Recurrence)

**Pattern:** Use pytz timezone-aware datetime with explicit localization

```python
from datetime import datetime
import pytz

# Localize to timezone (handles DST transitions)
ny_tz = pytz.timezone("America/New_York")
naive_dt = datetime(2025, 3, 9, 2, 30)  # During DST spring forward

# pytz handles DST transition (2:30 AM → 3:30 AM)
aware_dt = ny_tz.localize(naive_dt, is_dst=None)  # Raises exception for missing time
aware_dt = ny_tz.localize(naive_dt, is_dst=False)  # Use standard time
```

**Result:** Missing times are adjusted forward; ambiguous times use deterministic fold (DST vs standard)

### 4.2 Staleness Detection (Email Ingestion)

**Pattern:** Apply penalties for ambiguous signals

```python
from modules.email_ingestion.staleness_service import StalenessDetector

detector = StalenessDetector()
staleness_result = detector.detect_staleness(email, suggested_confidence)

# Penalties:
# - Multi-account contact: -0.25
# - Mixed client thread: -0.35
# - Subject change: -0.15
# - Stale mapping threshold (>90 days): -0.30

# If adjusted_confidence < TRIAGE_THRESHOLD (0.3): requires_triage = True
```

**Result:** Ambiguous emails are sent to triage for manual resolution

### 4.3 Idempotency (Billing Ledger, Email Ingestion, Jobs)

**Pattern:** Unique constraint on (firm, idempotency_key)

```python
# Attempt to create entry
entry = BillingLedgerEntry.objects.create(
    firm=firm,
    client=client,
    entry_type="invoice_issued",
    amount=Decimal("100.00"),
    idempotency_key="invoice-12345-retry",  # Unique per firm
    created_by=user,
)

# Retry with same key returns existing entry (or raises IntegrityError)
existing = BillingLedgerEntry.objects.filter(
    firm=firm, idempotency_key="invoice-12345-retry"
).first()
```

**Result:** Duplicate entries are prevented; retries are safe

### 4.4 Portal Multi-Account Scope (Permissions)

**Pattern:** Filter by active client context

```python
from modules.clients.models import PortalIdentity

# Portal user can be linked to multiple clients
identities = PortalIdentity.objects.filter(firm=firm, user=portal_user)

# When viewing documents, filter by active client context
active_client = request.client  # From middleware or session
docs = Document.objects.filter(
    firm=firm,
    client=active_client,  # ← Scope to active client
    visibility="client"
)
```

**Result:** Portal users see only documents for their active client context

### 4.5 Document Versioning (Concurrent Uploads)

**Pattern:** Create new DocumentVersion records for each upload

```python
from modules.documents.models import Document, DocumentVersion

# Upload 1 (creates version 1)
version1 = DocumentVersion.objects.create(
    document=doc,
    version_number=1,
    file_size_bytes=10000,
    s3_version_id="v1",
    uploaded_by=user1,
)

# Upload 2 (creates version 2, even if concurrent)
version2 = DocumentVersion.objects.create(
    document=doc,
    version_number=2,
    file_size_bytes=12000,
    s3_version_id="v2",
    uploaded_by=user2,
)

# Document current_version tracks latest
doc.current_version = 2
doc.save()
```

**Result:** Concurrent uploads create separate versions; no data loss

---

## 5. Compliance Matrix

| Category | Edge Cases | Tests Written | Implementation Complete | Status |
|----------|------------|---------------|-------------------------|--------|
| Recurrence | 5 | 5 | ✅ | 100% |
| Email Ingestion | 5 | 5 | ✅ | 100% |
| Permissions | 3 | 3 | ✅ | 100% |
| Billing Ledger | 4 | 4 | ✅ | 100% |
| Documents | 4 | 4 | ✅ | 100% |
| **Total** | **21** | **21** | **21/21** | **100%** |

**Overall Compliance:** 21/21 edge cases (100% coverage per docs/03-reference/requirements/DOC-23.md)

---

## 6. Related Documentation

- **docs/03-reference/requirements/DOC-23.md**: EDGE_CASES_CATALOG (canonical edge case list)
- **docs/03-reference/requirements/DOC-22.md**: TEST_STRATEGY (contract tests framework)
- **src/tests/contract_tests.py**: Contract tests (DOC-22.1)
- **src/tests/edge_cases/test_edge_cases.py**: Edge case tests (this implementation)

---

## 7. Implementation Files

### 7.1 Test Files (NEW)

- **src/tests/edge_cases/__init__.py**: Package init
- **src/tests/edge_cases/test_edge_cases.py**: Comprehensive edge case test suite (21 tests)

### 7.2 Related Implementation Files (Existing)

**Recurrence:**
- `src/modules/recurrence/services.py::RecurrenceGenerator`
- `src/modules/recurrence/models.py::RecurrenceRule`
- `src/modules/recurrence/backfill.py::BackfillService`

**Email Ingestion:**
- `src/modules/email_ingestion/services.py::EmailIngestionService`
- `src/modules/email_ingestion/staleness_service.py::StalenessDetector`
- `src/modules/email_ingestion/models.py::EmailArtifact, EmailAttachment`

**Permissions:**
- `src/modules/clients/models.py::PortalIdentity`
- `src/modules/documents/models.py::Document`
- `src/modules/auth/permissions.py`

**Billing Ledger:**
- `src/modules/finance/billing_ledger.py::BillingLedgerEntry, BillingAllocation`

**Documents:**
- `src/modules/documents/models.py::Document, DocumentVersion, DocumentLock`
- `src/modules/documents/malware_scan.py::DownloadPolicy`

---

## 8. Summary

DOC-23.1 implementation provides:

✅ **21 edge case tests** covering all scenarios from docs/03-reference/requirements/DOC-23.md
✅ **5 test categories**: Recurrence, Email Ingestion, Permissions, Billing Ledger, Documents
✅ **Implementation verification**: All edge cases are handled correctly in existing code
✅ **Regression prevention**: Automated test suite prevents future breakage
✅ **100% compliance** with docs/03-reference/requirements/DOC-23.md EDGE_CASES_CATALOG

The implementation ensures that tricky edge cases are:
1. **Documented** in docs/03-reference/requirements/DOC-23.md
2. **Tested** in src/tests/edge_cases/test_edge_cases.py
3. **Implemented** correctly in respective modules
4. **Verified** through CI/CD test runs

This provides confidence that the platform handles edge cases gracefully and prevents production issues from known tricky scenarios.
