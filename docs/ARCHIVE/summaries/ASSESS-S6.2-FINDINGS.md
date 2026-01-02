# ASSESS-S6.2: Multi-Tenancy Gaps in Async/Signals - Security Audit

**Date:** 2025-12-31
**Severity:** HIGH - IDOR (Insecure Direct Object Reference) vulnerabilities found
**Status:** Gaps identified, fixes required

## Executive Summary

Comprehensive audit of async tasks and Django signals revealed **CRITICAL multi-tenancy gaps** that could allow cross-firm data access (IDOR vulnerability). The main issues are:

1. **Signal handlers fetch old instances without firm filtering** - 6 instances
2. **Billing functions process cross-firm data** - 3 critical instances
3. **Management command dry-run mode lacks firm filtering** - 1 instance

**Risk Level:** HIGH - Exploitable IDOR vulnerabilities in production code

---

## Critical Vulnerabilities Found

### 1. Signal Handler IDOR Gaps (6 instances)

Signal handlers use `.get(pk=instance.pk)` without firm filtering when fetching the old instance to detect changes. While these run in the context of a save operation (which should be firm-scoped at the API layer), **they don't validate firm ownership**, creating a potential IDOR risk if an attacker can manipulate request data.

#### Finance Module
**File:** `src/modules/finance/signals.py`

```python
# Line 46 - IDOR GAP
old_instance = Bill.objects.get(pk=instance.pk)
```

**Impact:** An attacker could potentially modify bills from other firms if they can inject a cross-firm Bill ID.

#### CRM Module
**File:** `src/modules/crm/signals.py`

```python
# Line 34 - IDOR GAP
old_instance = Proposal.objects.get(pk=instance.pk)

# Line 100 - IDOR GAP
old_instance = Contract.objects.get(pk=instance.pk)
```

**Impact:** Cross-firm access to proposals and contracts.

#### Projects Module
**File:** `src/modules/projects/signals.py`

```python
# Line 33 - IDOR GAP
old_instance = Task.objects.get(pk=instance.pk)

# Line 92 - IDOR GAP
old_instance = TimeEntry.objects.get(pk=instance.pk)

# Line 140 - IDOR GAP
old_instance = Project.objects.get(pk=instance.pk)

# Line 255 - IDOR GAP
old_instance = Expense.objects.get(pk=instance.pk)
```

**Impact:** Cross-firm access to tasks, time entries, projects, and expenses.

---

### 2. Billing Function Cross-Firm Processing (3 CRITICAL instances)

#### CRITICAL: `process_recurring_invoices()` - Cross-Firm Invoice Processing
**File:** `src/modules/finance/billing.py:295-324`

```python
def process_recurring_invoices(reference_time=None, payment_service=StripeService):
    """Find invoices marked for autopay and execute charges."""
    now = reference_time or timezone.now()

    # Line 299-302: NO FIRM FILTERING!
    due_invoices = Invoice.objects.filter(
        autopay_opt_in=True,
        status__in=["sent", "partial", "overdue"],
    ).select_related("client")

    # Processes invoices across ALL firms!
    for invoice in due_invoices:
        # ... charge logic
```

**Impact:**
- **CRITICAL SEVERITY** - Processes invoices across all firms without isolation
- Could leak payment data cross-firm
- No firm parameter accepted
- Used by management command `process_recurring_charges.py`

**Recommended Fix:** Add optional `firm` parameter and filter by it (similar to `process_dunning_for_overdue_invoices`).

#### CRITICAL: `handle_dispute_opened()` - No Firm Validation
**File:** `src/modules/finance/billing.py:401-434`

```python
def handle_dispute_opened(stripe_dispute_data: dict):
    # Line 403: NO FIRM FILTERING!
    invoice = Invoice.objects.get(stripe_invoice_id=stripe_dispute_data["invoice_id"])

    dispute = PaymentDispute.objects.create(
        firm=invoice.firm,  # Uses invoice's firm without validation
        # ...
    )
```

**Impact:**
- **HIGH SEVERITY** - Webhook handler doesn't validate firm context
- Stripe webhook could be manipulated to access invoices across firms
- Should validate webhook signature AND firm ownership

**Recommended Fix:** Add firm validation or use `.get(stripe_invoice_id=..., firm=...)` if firm context is available.

#### CRITICAL: `handle_dispute_closed()` - No Firm Validation
**File:** `src/modules/finance/billing.py:437-468`

```python
def handle_dispute_closed(stripe_dispute_data: dict):
    # Line 439: NO FIRM FILTERING!
    dispute = PaymentDispute.objects.get(stripe_dispute_id=stripe_dispute_data["id"])
    # ...
```

**Impact:** Same as `handle_dispute_opened()`.

---

### 3. Management Command Dry-Run Mode Gap

#### `process_recurring_charges` - Dry Run Missing Firm Filter
**File:** `src/modules/finance/management/commands/process_recurring_charges.py:22-36`

```python
if dry_run:
    # Lines 25-29: NO FIRM FILTERING!
    queued = Invoice.objects.filter(
        autopay_opt_in=True,
        status__in=["sent", "partial", "overdue"],
    )
    for invoice in queued:
        # ... displays ALL invoices across ALL firms
```

**Impact:**
- **MEDIUM SEVERITY** - Dry-run mode shows invoices across all firms
- Information disclosure vulnerability
- Actual processing function also lacks firm filtering (see billing.py above)

**Recommended Fix:** Mirror the firm filtering logic from `generate_package_invoices.py` (lines 59-66).

---

## Safe Implementations Found ✅

### Background Jobs (All Safe)
**File:** `src/modules/firm/jobs.py`

All background jobs use `require_firm_for_job(firm_id)` guard:
```python
def expire_overdue_break_glass_sessions_job(*, firm_id=None):
    firm = require_firm_for_job(firm_id)  # ✅ Enforced
    return expire_overdue_break_glass_sessions(firm)
```

**Status:** ✅ **SECURE** - All 4 background jobs properly enforce firm isolation.

### Management Command: `generate_package_invoices`
**File:** `src/modules/finance/management/commands/generate_package_invoices.py`

Properly implements firm scoping:
```python
# Lines 60-66
if firm_id:
    firms = [Firm.objects.get(id=firm_id, status__in=["active", "trial"])]
else:
    firms = Firm.objects.filter(status__in=["active", "trial"])

# Line 103-105
engagements = ClientEngagement.objects.filter(
    firm=firm,
    status="current",
    # ...
)
```

**Status:** ✅ **SECURE** - Properly scopes all queries to firm.

### Clients Module Signals
**File:** `src/modules/clients/signals.py`

All object creation uses explicit firm scoping:
```python
client = Client.objects.create(
    firm=proposal.firm,  # ✅ TIER 2: Explicit tenant context
    # ...
)
```

**Status:** ✅ **SECURE** - All created objects explicitly set firm context.

---

## Recommendations

### Immediate Actions Required (Priority: CRITICAL)

1. **Fix `process_recurring_invoices()` billing function:**
   ```python
   def process_recurring_invoices(reference_time=None, payment_service=StripeService, firm=None):
       # Add firm parameter and filtering
       due_invoices = Invoice.objects.filter(
           autopay_opt_in=True,
           status__in=["sent", "partial", "overdue"],
       )

       if firm:
           due_invoices = due_invoices.filter(firm=firm)

       # ... rest of logic
   ```

2. **Fix dispute webhook handlers:**
   - Add firm validation to `handle_dispute_opened()` and `handle_dispute_closed()`
   - Verify Stripe webhook signature before processing
   - Consider adding firm_id to webhook metadata if possible

3. **Fix `process_recurring_charges` management command:**
   - Add `--firm-id` parameter (mirror `generate_package_invoices.py`)
   - Filter invoices by firm in dry-run mode
   - Update help text to document firm isolation

4. **Fix signal handler queries:**
   - Add `.filter(firm=instance.firm)` to all `.get(pk=instance.pk)` calls
   - Or use `Model.objects.for_firm(instance.firm).get(pk=instance.pk)` if using FirmScopedManager
   - Example:
     ```python
     # Before
     old_instance = Bill.objects.get(pk=instance.pk)

     # After
     old_instance = Bill.objects.filter(firm=instance.firm, pk=instance.pk).first()
     if not old_instance:
         # Handle missing/cross-firm case
         return
     ```

### Medium Priority Actions

5. **Add defensive validation to signal handlers:**
   - Validate that `instance.firm` matches the authenticated user's firm context
   - Add logging for potential IDOR attempts
   - Consider adding `@require_firm_isolation` decorator for signal handlers

6. **Create regression tests:**
   - Test cross-firm IDOR scenarios for all identified gaps
   - Verify that signal handlers reject cross-firm modifications
   - Test webhook handlers with cross-firm data

### Long-term Improvements

7. **Consider using FirmScopedManager globally:**
   - Replace direct `objects` manager with `for_firm()` scoped manager
   - Enforce at ORM level rather than per-query

8. **Add monitoring/alerting:**
   - Log when cross-firm queries are attempted
   - Alert on IDOR-like patterns in production

9. **Code review process:**
   - Add automated checks for `.objects.get()` without firm filtering
   - Require explicit firm scoping in all new signal handlers

---

## Attack Scenarios

### Scenario 1: Cross-Firm Bill Modification
**Vulnerability:** `finance/signals.py:46`

1. Attacker discovers Bill ID from another firm (e.g., via timing attack, enumeration)
2. Attacker crafts request to modify Bill with cross-firm ID
3. Signal handler fetches old instance without firm validation
4. Bill from other firm is modified

**Mitigation:** Add firm filtering to `.get()` query.

### Scenario 2: Cross-Firm Invoice Processing
**Vulnerability:** `billing.py:299-302`

1. Cron job runs `process_recurring_charges` command
2. Function processes invoices across ALL firms without isolation
3. Invoice from Firm A could be charged using payment method intended for Firm B
4. Data leakage and financial transaction errors

**Mitigation:** Add firm parameter and process per-firm.

### Scenario 3: Stripe Webhook Manipulation
**Vulnerability:** `billing.py:403, 439`

1. Attacker intercepts or crafts Stripe webhook payload
2. Webhook handler looks up invoice/dispute without firm validation
3. Dispute from Firm A could be applied to Firm B's invoice
4. Financial records corrupted across firms

**Mitigation:** Validate firm context in webhook handlers.

---

## Testing Recommendations

```python
# Example test case for signal handler IDOR
def test_bill_signal_prevents_cross_firm_modification():
    firm_a = Firm.objects.create(name="Firm A", slug="firm-a")
    firm_b = Firm.objects.create(name="Firm B", slug="firm-b")

    bill_a = Bill.objects.create(firm=firm_a, total_amount=100)

    # Attempt to modify with cross-firm context
    bill_a.firm = firm_b  # Attacker changes firm
    bill_a.total_amount = 200

    with pytest.raises(PermissionDenied):
        bill_a.save()  # Should be blocked by signal handler
```

---

## Conclusion

**Total Vulnerabilities:** 10 (6 signal handlers + 3 billing functions + 1 management command)

**Severity Distribution:**
- CRITICAL: 3 (billing cross-firm processing, webhook handlers)
- HIGH: 6 (signal handler IDOR gaps)
- MEDIUM: 1 (management command dry-run)

**Status:** ✅ **COMPLETED** (December 2025)

**Fix Summary:**
- All 10 IDOR vulnerabilities fixed with firm filtering
- Regression tests added to `src/tests/security/test_tenant_isolation.py`
- All fixes verified and tested

**Next Steps:**
1. ✅ Review and approve fixes - **COMPLETED**
2. ✅ Implement changes (priority: billing.py first) - **COMPLETED**
3. ✅ Add regression tests - **COMPLETED**
4. Deploy with monitoring
5. Conduct follow-up security audit
