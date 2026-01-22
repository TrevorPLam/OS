# Test Integrity Verification Guide

**Purpose:** This guide documents how to verify that tests actually catch regressions and don't provide false confidence.

---

## Quick Start: Verify a Test Works

To check if a test truly validates its claimed behavior:

1. **Run the test to confirm it passes**
2. **Inject a defect in the code being tested**
3. **Verify the test now fails**
4. **Revert the defect**

If the test still passes after step 2, it's a **false positive risk**.

---

## Manual Canary Mutation Testing

### Basic Process

```bash
# 1. Identify a test to validate
TEST_PATH="tests/safety/test_portal_containment.py::TestPortalContainment::test_denyportalaccess_blocks_portal_users"

# 2. Run the test (should PASS)
pytest $TEST_PATH -v

# 3. Inject a defect (example: remove permission check)
# Edit: modules/clients/permissions.py - comment out the denial logic

# 4. Run the test again (should FAIL)
pytest $TEST_PATH -v

# 5. Revert the change
git checkout modules/clients/permissions.py
```

### Common Defects to Inject

**For permission tests:**
- Remove the permission check
- Invert boolean logic (`if portal_user:` → `if not portal_user:`)
- Return True instead of False
- Remove middleware from MIDDLEWARE list

**For serializer tests:**
- Remove a field from serializer
- Change field type (CharField → IntegerField)
- Remove validation logic
- Return empty dict instead of data

**For business logic tests:**
- Skip a critical step (don't save to database)
- Return wrong value (swap user assignments)
- Remove error handling
- Skip validation

---

## Test Trustworthiness Anti-Patterns

### ❌ Always-Pass Tests

**Problem:**
```python
def test_feature_works(self):
    """Document that feature works."""
    assert True, "Feature documented in README"
```

**Why it's bad:** Test never fails, even if feature is completely broken.

**Fix:**
```python
def test_feature_works(self):
    """Verify feature actually works."""
    result = execute_feature()
    assert result.success, f"Feature failed: {result.error}"
```

### ❌ Presence-Only Assertions

**Problem:**
```python
def test_serializer_includes_name(self):
    serializer = MySerializer(obj)
    assert 'name' in serializer.data  # Only checks key exists!
```

**Why it's bad:** Test passes even if `name` is empty string, null, or wrong value.

**Fix:**
```python
def test_serializer_includes_correct_name(self):
    serializer = MySerializer(obj)
    assert 'name' in serializer.data
    assert serializer.data['name'] == obj.name  # Verify actual value
```

### ❌ Missing Negative Cases

**Problem:**
```python
def test_admin_can_access(self, admin_user):
    # Only tests that admins CAN access
    assert can_access(admin_user, '/admin/')
```

**Why it's bad:** Doesn't verify that non-admins are blocked.

**Fix:**
```python
def test_admin_can_access(self, admin_user):
    assert can_access(admin_user, '/admin/')

def test_regular_user_cannot_access(self, regular_user):
    # Negative test: verify denial
    assert not can_access(regular_user, '/admin/')
```

### ❌ Over-Mocking

**Problem:**
```python
@patch('module.database')
@patch('module.network')
@patch('module.business_logic')  # Mocked the actual code under test!
def test_feature(mock_logic, mock_network, mock_db):
    # Test only exercises mocks, not real code
    result = feature()
    assert result == "success"
```

**Why it's bad:** Test passes even if actual business logic is broken.

**Fix:**
```python
@patch('module.database')  # Only mock external dependencies
@patch('module.network')
def test_feature(mock_network, mock_db):
    # Real business logic is executed
    result = feature()
    assert result.status == "success"
    assert result.data is not None
```

---

## Test Quality Checklist

Before committing a test, verify:

- [ ] **Test has at least one real assertion** (not `assert True`)
- [ ] **Test fails when expected behavior breaks** (inject defect to verify)
- [ ] **Test checks actual values, not just existence** (`== expected`, not `in data`)
- [ ] **Test has clear failure message** explaining what broke
- [ ] **Test is isolated** (doesn't depend on test execution order)
- [ ] **Test uses real objects, not excessive mocks** (mock boundaries only)
- [ ] **Test covers both happy path AND error cases**
- [ ] **Test name clearly states what is being protected**
- [ ] **Test has no commented-out assertions** (remove or implement)
- [ ] **Test cleanup is guaranteed** (use fixtures/teardown)

---

**Last Updated:** 2026-01-22  
**Maintained by:** Engineering Team  
**Questions?** See `TEST_TRUST_REPORT.md` for detailed analysis
