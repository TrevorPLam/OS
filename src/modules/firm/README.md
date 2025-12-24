# Firm Module (TIER 0: Multi-Tenant Foundation)

**Status**: ✅ TIER 0.1-0.2 Complete

This module implements the foundational multi-tenant architecture for ConsultantPro.

## Overview

Every piece of customer data in ConsultantPro belongs to exactly one **Firm** (workspace/tenant). This module provides:

1. **Firm Model**: Top-level tenant boundary
2. **FirmMembership Model**: Links Users to Firms with roles
3. **Firm Context Middleware**: Ensures every request has firm context
4. **Firm Scoping Utilities**: Helpers for firm-scoped database queries

## Architecture

### Firm Context Resolution

Every incoming request must have a firm context. The `FirmContextMiddleware` resolves firm context from:

1. **Subdomain** (highest priority)
   - Example: `acme.consultantpro.com` → Firm with slug='acme'

2. **JWT Token** (API requests)
   - Token must include `firm_id` claim in payload

3. **User Session** (web app)
   - Resolved via `FirmMembership` for authenticated users
   - Session can store `active_firm_id` for multi-firm users

### Firm Context Enforcement

**TIER 0 REQUIREMENT**: Requests without firm context are **REJECTED** (403 Forbidden).

**Exceptions**:
- Public endpoints (auth, health checks)
- Platform operator endpoints (explicitly marked)

## Usage

### In Views/ViewSets

```python
from modules.firm.utils import get_request_firm, firm_scoped_queryset
from modules.clients.models import Client

def my_view(request):
    # Get firm from request
    firm = get_request_firm(request)

    # Get firm-scoped queryset
    clients = firm_scoped_queryset(Client, firm)

    # Or use the utility
    clients = Client.firm_scoped.for_firm(firm)
```

### Using FirmScopedMixin

```python
from rest_framework import viewsets
from modules.firm.utils import FirmScopedMixin
from modules.clients.models import Client
from modules.clients.serializers import ClientSerializer

class ClientViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Client CRUD operations.

    Automatically scoped to request.firm via FirmScopedMixin.
    """
    model = Client
    serializer_class = ClientSerializer

    # get_queryset() is automatically implemented to scope to request.firm
```

### Validating Firm Access

```python
from modules.firm.utils import validate_firm_access, get_request_firm
from modules.clients.models import Client

def update_client(request, client_id):
    firm = get_request_firm(request)
    client = Client.objects.get(id=client_id)

    # Ensure client belongs to request firm
    validate_firm_access(client, firm)

    # Safe to proceed...
```

### In JWT Tokens

When issuing JWT tokens, include `firm_id`:

```python
from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user, firm):
    refresh = RefreshToken.for_user(user)

    # Add firm_id claim
    refresh['firm_id'] = firm.id

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
```

## Models

### Firm

Top-level tenant boundary. Represents a consulting firm/workspace.

**Key Fields**:
- `name`: Display name
- `slug`: Subdomain identifier (unique)
- `status`: trial | active | suspended | cancelled
- `subscription_tier`: free | starter | professional | enterprise
- `max_users`, `max_clients`: Subscription quotas
- `users_count`, `clients_count`: Current usage

**Relationships**:
- One-to-many with User (via FirmMembership)
- One-to-many with all customer data models

### FirmMembership

Links Users to Firms with role-based permissions.

**Key Fields**:
- `firm`: ForeignKey to Firm
- `user`: ForeignKey to User
- `role`: owner | admin | staff | member
- Permission flags: `can_manage_users`, `can_manage_billing`, etc.

**Constraints**:
- Unique together: (firm, user)
- A user can belong to multiple firms

## Public Endpoints

The following endpoints do NOT require firm context:

- `/api/auth/*` - Authentication endpoints
- `/api/health/` - Health check
- `/api/docs/` - API documentation
- `/api/schema/` - API schema
- `/admin/login/` - Django admin login

## Platform Endpoints

Platform operator endpoints use different authentication (not firm-scoped):

- `/api/platform/*` - Platform admin operations

## Environment Variables

None required. Firm context resolution works automatically via middleware.

## Testing

```bash
# Run firm module tests
pytest src/modules/firm/tests/

# Test firm context middleware
pytest src/modules/firm/tests/test_middleware.py

# Test firm scoping utilities
pytest src/modules/firm/tests/test_utils.py
```

## TIER 0 Compliance

This module satisfies TIER 0 requirements:

- ✅ 0.1: Firm/Workspace tenancy established
- ✅ 0.2: Firm context resolution implemented
- ⏳ 0.3: Firm-scoped querysets (utilities provided, enforcement pending)
- ⏳ 0.4: Portal containment (pending)
- ⏳ 0.5: Platform privacy enforcement (pending)
- ⏳ 0.6: Break-glass access (pending)

## Security Considerations

1. **Subdomain Spoofing**: Middleware validates firm slugs against database
2. **Token Tampering**: JWT validation ensures firm_id claim integrity
3. **Session Hijacking**: Standard Django session security applies
4. **Cross-Firm Access**: All queries must use firm scoping utilities

## Future Enhancements (Post-TIER 0)

- Firm-level feature flags
- Per-firm API rate limiting
- Firm data export (for offboarding)
- Firm analytics and usage tracking
