# Tenant Provisioning Guide (DOC-19.1)

**Document Version:** 1.0
**Date:** December 30, 2025
**Purpose:** Guide for provisioning new firms (tenants) per DB_SCHEMA_AND_MIGRATIONS spec (docs/19)

---

## Overview

The platform uses **firm-scoped row-level isolation** for multi-tenancy (see ADR-0010 in docs/4). Tenant provisioning creates a new Firm record and seeds baseline configuration.

Per docs/19 Section 1, the provisioning workflow:
1. Creates Firm record
2. Creates firm admin user
3. Seeds baseline config (roles, default stages, template stubs)
4. Records audit events and provisioning logs

**Key Property:** Provisioning is **IDEMPOTENT** - safe to retry without creating duplicates.

---

## Provisioning Methods

### Method 1: Django Management Command (Recommended)

```bash
python manage.py provision_firm \
    --name "Acme Consulting" \
    --slug acme-consulting \
    --admin-email admin@acme.com \
    --admin-password "secure_password_123" \
    --admin-first-name John \
    --admin-last-name Doe \
    --timezone "America/Los_Angeles" \
    --currency USD \
    --tier professional \
    --max-users 20 \
    --max-clients 100 \
    --max-storage-gb 50
```

**Required Arguments:**
- `--name`: Firm name (e.g., "Acme Consulting")
- `--slug`: URL-safe slug (e.g., "acme-consulting")
- `--admin-email`: Admin user email
- `--admin-password`: Admin user password

**Optional Arguments:**
- `--admin-first-name`: Admin's first name
- `--admin-last-name`: Admin's last name
- `--timezone`: Firm timezone (default: America/New_York)
- `--currency`: Firm currency (default: USD)
- `--tier`: Subscription tier - starter, professional, enterprise (default: starter)
- `--max-users`: Maximum number of users (default: 5)
- `--max-clients`: Maximum number of clients (default: 25)
- `--max-storage-gb`: Maximum storage in GB (default: 10)

---

### Method 2: Python API

```python
from modules.firm.provisioning import provision_firm

result = provision_firm(
    firm_name="Acme Consulting",
    firm_slug="acme-consulting",
    admin_email="admin@acme.com",
    admin_password="secure_password_123",
    admin_first_name="John",
    admin_last_name="Doe",
    timezone="America/Los_Angeles",
    currency="USD",
    subscription_tier="professional",
    max_users=20,
    max_clients=100,
    max_storage_gb=50,
)

firm = result['firm']
admin_user = result['admin_user']
created = result['created']  # True if new firm, False if existing

print(f"Firm: {firm.name} (ID: {firm.id})")
print(f"Admin: {admin_user.email}")
print(f"Created: {created}")
```

---

### Method 3: Programmatic with Service Class

```python
from modules.firm.provisioning import TenantProvisioningService

service = TenantProvisioningService(
    correlation_id="custom-correlation-id",  # Optional
    initiated_by=platform_operator_user  # Optional
)

result = service.provision_firm(
    firm_name="Acme Consulting",
    firm_slug="acme-consulting",
    admin_email="admin@acme.com",
    admin_password="secure_password_123",
    # ... other arguments
)
```

---

## Idempotency Guarantees

Provisioning is **fully idempotent**. Retrying with the same parameters will:

1. **Firm Creation:**
   - If firm with `slug` already exists → Returns existing firm
   - Unique constraint on `slug` prevents duplicates

2. **Admin User Creation:**
   - If user with `email` already exists → Reuses existing user
   - Password is NOT updated for existing users (security)
   - Unique constraint on `email` prevents duplicates

3. **Firm Membership:**
   - If membership already exists → Ensures admin role
   - Upgrades to admin if user already has different role

4. **Baseline Config Seeding:**
   - All seeding operations are idempotent (create only if not exists)
   - Safe to re-run without creating duplicates

**Example:**
```bash
# First run - creates firm
python manage.py provision_firm --name "Acme" --slug acme --admin-email admin@acme.com --admin-password pass123
# Output: ✓ Firm created successfully

# Second run - idempotent
python manage.py provision_firm --name "Acme" --slug acme --admin-email admin@acme.com --admin-password pass123
# Output: ⚠ Firm already exists, verified configuration
```

---

## Provisioning Workflow (Internal)

The `TenantProvisioningService` executes these steps in a database transaction:

### Step 1: Create Firm Record
```python
firm, created = Firm.objects.get_or_create(
    slug='acme-consulting',
    defaults={
        'name': 'Acme Consulting',
        'timezone': 'America/Los_Angeles',
        'currency': 'USD',
        'subscription_tier': 'professional',
        'status': 'trial',
        # ... other fields
    }
)
```

### Step 2: Create Admin User
```python
admin_user, created = User.objects.get_or_create(
    email='admin@acme.com',
    defaults={
        'username': 'admin@acme.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'is_active': True,
    }
)
if created:
    admin_user.set_password(password)
    admin_user.save()
```

### Step 3: Create Firm Membership
```python
membership, created = FirmMembership.objects.get_or_create(
    user=admin_user,
    firm=firm,
    defaults={
        'role': 'admin',
        'is_active': True,
    }
)
```

### Step 4: Seed Baseline Configuration

The provisioning service automatically seeds baseline configuration for new firms:

#### Project Templates
Three default project templates are created:
1. **General Consulting Engagement** (`GEN-CONSULT`)
   - Standard consulting engagement with common milestones
   - Default billing: Time & Materials
   - Duration: 90 days
   - Milestones: Discovery, Analysis, Implementation, Review

2. **Monthly Retainer** (`MONTHLY-RET`)
   - Recurring monthly retainer engagement
   - Default billing: Fixed Fee
   - Duration: 30 days

3. **Advisory Services** (`ADVISORY`)
   - Advisory and strategic consulting
   - Default billing: Time & Materials
   - Duration: 60 days
   - Milestones: Initial Consultation, Strategic Recommendations, Implementation Support

#### Email Templates
Three default email templates are created:
1. **Welcome Email** - Sent to new clients upon onboarding
2. **Appointment Confirmation** - Sent when appointments are scheduled
3. **Project Update Notification** - Sent when project status changes

All templates support merge fields (e.g., `{{firm_name}}`, `{{client_name}}`) for personalization.

**Idempotency:** All seeding operations check for existing records before creation, making the process safe to retry.

### Step 5: Record Audit Events
```python
audit.log_event(
    firm=firm,
    category='config',
    action='firm_provisioned',  # or 'firm_provisioning_verified'
    actor=admin_user,
    target_model='Firm',
    target_id=firm.id,
    metadata={
        'correlation_id': correlation_id,
        'admin_user_id': admin_user.id,
        'created': created,
        # ... other metadata
    }
)
```

---

## Provisioning Log

Every provisioning attempt is logged in `ProvisioningLog` model:

**Fields:**
- `firm` - Firm that was provisioned (null if provisioning failed early)
- `status` - pending, in_progress, completed, failed, rolled_back
- `started_at` - When provisioning started
- `completed_at` - When provisioning completed/failed
- `duration_seconds` - Total provisioning duration
- `correlation_id` - Correlation ID for request tracing
- `initiated_by` - User who initiated provisioning (platform operator)
- `provisioning_config` - Configuration used for provisioning
- `steps_completed` - List of successfully completed steps
- `error_message` - Error message if provisioning failed
- `error_step` - Step where provisioning failed
- `metadata` - Additional provisioning metadata

**Query Logs:**
```python
from modules.firm.models import ProvisioningLog

# Get all provisioning logs
logs = ProvisioningLog.objects.all()

# Get logs for specific firm
firm_logs = ProvisioningLog.objects.filter(firm=firm)

# Get failed provisionings
failed = ProvisioningLog.objects.filter(status='failed')

# Get recent provisionings
recent = ProvisioningLog.objects.order_by('-started_at')[:10]
```

---

## Error Handling

Provisioning failures are rolled back and logged:

```python
try:
    result = provision_firm(
        firm_name="Acme",
        firm_slug="acme",
        admin_email="admin@acme.com",
        admin_password="pass123"
    )
except ProvisioningError as e:
    print(f"Provisioning failed: {e}")
    # Check ProvisioningLog for details
```

**Common Errors:**
- Invalid firm slug (must be lowercase alphanumeric + hyphens)
- Duplicate firm slug (use different slug or accept existing firm)
- Invalid timezone (must be valid IANA timezone)
- Invalid currency (must be 3-letter ISO code)

**Error Recovery:**
- All errors rollback the database transaction
- ProvisioningLog records error details
- Safe to retry after fixing configuration

---

## Correlation IDs

Every provisioning attempt has a unique correlation ID for tracing:

```python
# Automatic correlation ID
result = provision_firm(...)  # Generates UUID automatically

# Custom correlation ID
service = TenantProvisioningService(correlation_id="my-custom-id")
result = service.provision_firm(...)
```

Correlation IDs appear in:
- ProvisioningLog records
- Audit events
- Application logs

Use correlation IDs to trace provisioning across logs and events.

---

## Monitoring and Observability

### Metrics

Track provisioning metrics with observability module:

```python
from modules.core.observability import track_job_execution

# Provisioning service automatically tracks:
# - Provisioning duration (via ProvisioningLog.duration_seconds)
# - Success/failure status
# - Error rates
```

### Alerts

Monitor these thresholds (see docs/ALERT_CONFIGURATION.md):
- **Provisioning failure rate > 10%** - Investigate provisioning errors
- **Provisioning duration > 60s** - Performance degradation
- **Failed provisioning count > 5 (24h window)** - Systemic issue

---

## Bulk Provisioning

For provisioning multiple firms:

```python
from modules.firm.provisioning import provision_firm

firms_config = [
    {
        'firm_name': 'Acme Consulting',
        'firm_slug': 'acme-consulting',
        'admin_email': 'admin@acme.com',
        'admin_password': 'pass123',
    },
    {
        'firm_name': 'Beta Corp',
        'firm_slug': 'beta-corp',
        'admin_email': 'admin@beta.com',
        'admin_password': 'pass456',
    },
    # ... more firms
]

for config in firms_config:
    try:
        result = provision_firm(**config)
        print(f"✓ Provisioned: {result['firm'].name}")
    except ProvisioningError as e:
        print(f"✗ Failed: {config['firm_name']} - {e}")
```

---

## Security Considerations

1. **Password Security:**
   - Passwords are hashed using Django's default hasher (PBKDF2)
   - Passwords are NOT updated on idempotent retries (prevents password reset)
   - Use strong passwords for admin users

2. **Admin Access:**
   - Provisioning creates firm-level admin (not platform admin)
   - Admin has full access to their firm only
   - Platform admins require separate PlatformUserProfile

3. **Audit Trail:**
   - All provisioning attempts logged in ProvisioningLog
   - Audit events recorded for firm creation
   - Correlation IDs enable full request tracing

4. **Input Validation:**
   - Firm slug validated (lowercase, alphanumeric, hyphens only)
   - Timezone validated (must be valid IANA timezone)
   - Currency validated (must be 3-letter ISO code)
   - Email validated (must be valid email format)

---

## Testing Provisioning

### Unit Tests

```python
from modules.firm.provisioning import provision_firm, ProvisioningError
from modules.firm.models import Firm, FirmMembership

def test_provision_firm_creates_firm():
    result = provision_firm(
        firm_name="Test Firm",
        firm_slug="test-firm",
        admin_email="admin@test.com",
        admin_password="test123"
    )

    assert result['created'] is True
    assert result['firm'].name == "Test Firm"
    assert result['admin_user'].email == "admin@test.com"
    assert FirmMembership.objects.filter(
        user=result['admin_user'],
        firm=result['firm'],
        role='admin'
    ).exists()

def test_provision_firm_is_idempotent():
    # First provisioning
    result1 = provision_firm(
        firm_name="Test Firm",
        firm_slug="test-firm",
        admin_email="admin@test.com",
        admin_password="test123"
    )

    # Second provisioning (idempotent)
    result2 = provision_firm(
        firm_name="Test Firm",
        firm_slug="test-firm",
        admin_email="admin@test.com",
        admin_password="test123"
    )

    assert result1['firm'].id == result2['firm'].id
    assert result1['admin_user'].id == result2['admin_user'].id
    assert result2['created'] is False
```

### Integration Tests

```python
def test_provisioning_creates_audit_events():
    result = provision_firm(
        firm_name="Test Firm",
        firm_slug="test-firm",
        admin_email="admin@test.com",
        admin_password="test123"
    )

    # Check audit event was created
    from modules.firm.audit import AuditEvent
    audit_event = AuditEvent.objects.filter(
        firm=result['firm'],
        action='firm_provisioned'
    ).first()

    assert audit_event is not None
    assert audit_event.metadata['admin_user_id'] == result['admin_user'].id
```

---

## Migration Compliance

Per docs/19 Section 2, migration runner requirements:

### Current Implementation Status

✅ **Supports applying migrations to:**
- ✅ Single tenant (standard Django migrations per tenant/firm)
- ⚠️ All tenants (manual batching required)
- ✅ New tenant bootstrap (automatic via Django migrations)

✅ **Records:**
- ✅ Migration version applied (Django's django_migrations table)
- ✅ Start/end time (via ProvisioningLog for provisioning migrations)
- ✅ Success/failure (via ProvisioningLog.status)
- ✅ Correlation ID (via ProvisioningLog.correlation_id)

⚠️ **Rollback:**
- ⚠️ Forward-fix only (Django migrations support rollback but not used in production)

### Migration Strategy

**Current (Row-Level Tenancy):**
- Standard Django migrations apply to entire database
- All firms share same schema
- Migrations run once, affect all tenants
- No per-tenant migration tracking needed

**Future (Schema-Per-Tenant):**
If migrating to schema-per-tenant isolation:
1. Create migration runner service
2. Track per-schema migration status
3. Support batched migration across tenants
4. Add retry logic for failed migrations
5. Implement selective rollback

---

## Troubleshooting

### Provisioning Hangs or Times Out

**Cause:** Database lock contention or slow network

**Solution:**
- Check database connection pool
- Verify no long-running transactions
- Check application logs for errors

### Provisioning Fails with "slug already exists"

**Cause:** Firm with that slug already provisioned

**Solution:**
- Use different slug OR
- Accept existing firm (idempotent retry)

### Admin User Already Exists

**Cause:** User with that email already exists

**Solution:**
- Provisioning will reuse existing user (idempotent)
- Password NOT updated (security feature)
- If user needs different email, use different email

### Provisioning Succeeds but No Audit Event

**Cause:** Audit system not configured

**Solution:**
- Check audit module is installed
- Verify AuditEvent model exists
- Check application logs for audit errors

---

## API Reference

### `provision_firm()`

```python
def provision_firm(
    firm_name: str,
    firm_slug: str,
    admin_email: str,
    admin_password: str,
    admin_first_name: str = "",
    admin_last_name: str = "",
    timezone: str = "America/New_York",
    currency: str = "USD",
    subscription_tier: str = "starter",
    **extra_config
) -> Dict[str, Any]:
    """
    Provision a new firm with baseline configuration.

    Returns:
        {
            'firm': Firm instance,
            'admin_user': User instance,
            'firm_membership': FirmMembership instance,
            'created': bool (True if new, False if existing),
            'provisioning_log': ProvisioningLog instance,
        }

    Raises:
        ProvisioningError: If provisioning fails
    """
```

### `TenantProvisioningService`

```python
class TenantProvisioningService:
    """Idempotent tenant provisioning service."""

    def __init__(
        self,
        correlation_id: Optional[str] = None,
        initiated_by: Optional[User] = None
    ):
        """Initialize service with optional correlation ID and initiator."""

    def provision_firm(
        self,
        firm_name: str,
        firm_slug: str,
        admin_email: str,
        admin_password: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Provision firm (idempotent)."""
```

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-12-30 | 1.0 | Initial provisioning guide for DOC-19.1 |

---

## References

- **DB_SCHEMA_AND_MIGRATIONS spec:** docs/19
- **SYSTEM_SPEC tenancy:** docs/5 (Section 3)
- **ADR-0010 (row-level tenancy):** docs/4
- **Provisioning service:** src/modules/firm/provisioning.py
- **Management command:** src/modules/firm/management/commands/provision_firm.py
- **ProvisioningLog model:** src/modules/firm/models.py (via migration 0007)

