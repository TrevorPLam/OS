# AGENTS.md — Safety Tests

Last Updated: 2026-01-06
Applies To: `tests/safety/`

## Purpose

Security invariant tests that enforce critical system guarantees. These tests MUST pass for every commit and deployment.

## Critical Invariants

### 1. Tenant Isolation (`test_tenant_isolation.py`)

**Invariant**: Users can NEVER see data from other firms.

```python
def test_firm_isolation_on_all_endpoints():
    """Every list endpoint must filter by user's firm."""
    firm_a = Firm.objects.create(name='Firm A')
    firm_b = Firm.objects.create(name='Firm B')
    
    user_a = User.objects.create(firm=firm_a)
    
    # Create data in both firms
    Client.objects.create(firm=firm_a, name='Client A')
    Client.objects.create(firm=firm_b, name='Client B')
    
    api_client.force_authenticate(user_a)
    response = api_client.get('/api/v1/clients/')
    
    # User A must ONLY see Firm A's data
    assert all(c['firm'] == str(firm_a.id) for c in response.data)
```

### 2. Portal Boundary (`test_portal_boundary.py`)

**Invariant**: Portal users can only access `/api/portal/` endpoints.

```python
def test_portal_user_cannot_access_staff_endpoints():
    """Portal users must be blocked from staff endpoints."""
    portal_user = create_portal_user()
    api_client.force_authenticate(portal_user)
    
    STAFF_ENDPOINTS = [
        '/api/v1/clients/',
        '/api/v1/projects/',
        '/api/v1/invoices/',
        # ... all staff endpoints
    ]
    
    for endpoint in STAFF_ENDPOINTS:
        response = api_client.get(endpoint)
        assert response.status_code == 403
```

### 3. No Content Logging (`test_no_content_logging.py`)

**Invariant**: Sensitive data never appears in logs.

```python
def test_pii_not_logged(caplog):
    """PII must not appear in application logs."""
    sensitive_data = {
        'ssn': '123-45-6789',
        'email': 'test@example.com',
        'password': 'secret123',
    }
    
    # Perform operation that might log
    with caplog.at_level(logging.DEBUG):
        response = api_client.post('/api/v1/clients/', sensitive_data)
    
    log_text = '\n'.join(caplog.messages)
    assert sensitive_data['ssn'] not in log_text
    assert sensitive_data['password'] not in log_text
```

### 4. Encryption at Rest (`test_encryption.py`)

**Invariant**: PII fields are encrypted in database.

```python
def test_pii_encrypted_at_rest():
    """PII fields must be encrypted in the database."""
    client = Client.objects.create(
        firm=firm,
        name='Test Client',
        ssn='123-45-6789'
    )
    
    # Raw database query
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT ssn FROM clients_client WHERE id = %s",
            [client.id]
        )
        raw_ssn = cursor.fetchone()[0]
    
    # Must NOT be plaintext
    assert raw_ssn != '123-45-6789'
    assert raw_ssn.startswith('gAAAAA')  # Fernet prefix
```

### 5. Break-Glass Audit (`test_break_glass.py`)

**Invariant**: All impersonation actions are logged.

```python
def test_impersonation_logged():
    """Break-glass impersonation must create audit log."""
    admin = create_admin_user()
    target_user = create_user()
    
    response = api_client.post(
        '/api/v1/auth/impersonate/',
        {'user_id': target_user.id},
        HTTP_AUTHORIZATION=f'Bearer {admin_token}'
    )
    
    # Audit log must exist
    log = AuditLog.objects.filter(
        action='impersonate',
        actor=admin,
        target=target_user
    ).first()
    
    assert log is not None
    assert log.ip_address is not None
```

## Running Safety Tests

```bash
# Run all safety tests
pytest tests/safety/ -v

# Run specific invariant
pytest tests/safety/test_tenant_isolation.py -v

# Run in CI (must pass)
pytest tests/safety/ --tb=short --strict-markers
```

## CI/CD Gate

These tests are BLOCKING for deployment:

```yaml
# .github/workflows/safety.yml
safety-tests:
  runs-on: ubuntu-latest
  steps:
    - name: Run Safety Tests
      run: pytest tests/safety/ -v --tb=short
    - name: Block on Failure
      if: failure()
      run: |
        echo "SAFETY TESTS FAILED - BLOCKING DEPLOYMENT"
        exit 1
```

## Adding New Invariants

1. Identify the security property to test
2. Create test in appropriate file (or new file)
3. Document the invariant in this AGENTS.md
4. Ensure test fails when invariant is violated
5. Add to CI/CD gate if not already covered
