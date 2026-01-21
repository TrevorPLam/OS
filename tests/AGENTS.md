# AGENTS.md — Tests

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `tests/`

## Purpose

Test suite for ConsultantPro backend. Organized to mirror `src/` structure.

## Directory Structure

```
tests/
├── conftest.py           # Shared fixtures
├── safety/               # Security invariant tests
├── test_*.py             # Module test files
└── utils/                # Test utilities
```

## Running Tests

```bash
# All tests
make test

# Specific file
pytest tests/test_clients.py -v

# Specific test
pytest tests/test_clients.py::test_client_list -v

# With coverage
pytest --cov=src --cov-report=html

# Safety tests only
pytest tests/safety/ -v
```

## Key Fixtures (conftest.py)

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `db` | function | Database access (rollback per test) |
| `client` | function | Django test client |
| `api_client` | function | DRF API client |
| `firm` | function | Test firm instance |
| `user` | function | Test user (staff) |
| `admin_user` | function | Admin user |
| `portal_user` | function | Portal (client) user |
| `auth_client` | function | Authenticated API client |

## Fixture Usage

```python
def test_something(api_client, firm, user):
    """Test with authenticated user in a firm context."""
    api_client.force_authenticate(user)
    response = api_client.get('/api/v1/clients/')
    assert response.status_code == 200
```

### Multi-Tenant Testing

```python
def test_firm_isolation(api_client, firm):
    """Test that users can't see other firms' data."""
    other_firm = Firm.objects.create(name='Other Firm')
    other_client = Client.objects.create(firm=other_firm, name='Other')
    
    user = User.objects.create(firm=firm)
    api_client.force_authenticate(user)
    
    response = api_client.get('/api/v1/clients/')
    assert other_client.id not in [c['id'] for c in response.data]
```

## Test Patterns

### Model Tests

```python
class TestClientModel:
    def test_create_client(self, firm):
        client = Client.objects.create(firm=firm, name='Test')
        assert client.id is not None
        
    def test_firm_required(self, db):
        with pytest.raises(IntegrityError):
            Client.objects.create(name='No Firm')
```

### API Tests

```python
class TestClientAPI:
    def test_list_clients(self, auth_client, firm):
        Client.objects.create(firm=firm, name='Test')
        response = auth_client.get('/api/v1/clients/')
        assert response.status_code == 200
        assert len(response.data) == 1
        
    def test_unauthorized(self, api_client):
        response = api_client.get('/api/v1/clients/')
        assert response.status_code == 401
```

### Service Tests

```python
class TestInvoiceService:
    def test_create_invoice(self, firm, client):
        invoice = InvoiceService.create(
            firm=firm,
            client=client,
            amount=Decimal('100.00')
        )
        assert invoice.status == 'draft'
```

## Safety Tests (`safety/`)

Critical security invariant tests that MUST pass:

| Test File | Invariant |
|-----------|-----------|
| `test_tenant_isolation.py` | Firm data isolation |
| `test_portal_boundary.py` | Portal users can't access staff endpoints |
| `test_no_content_logging.py` | Sensitive data not in logs |
| `test_encryption.py` | PII fields encrypted at rest |
| `test_break_glass.py` | Impersonation logging |

## CI Integration

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    pytest --cov=src --cov-fail-under=80
```

## Dependencies

- **pytest** - Test framework
- **pytest-django** - Django integration
- **pytest-cov** - Coverage reporting
- **factory-boy** - Test data factories
- **faker** - Fake data generation
