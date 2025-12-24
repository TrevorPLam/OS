# Portal Containment (TIER 0: Task 0.4)

**Status:** ✅ COMPLETE

Portal containment ensures that client portal users are fully isolated and can ONLY access portal-specific endpoints. This is a "default-deny" security model.

---

## Architecture

### 1. Portal Namespace

All portal endpoints are under `/api/portal/`:

```
/api/portal/projects/          - Portal user's projects (read-only)
/api/portal/comments/          - Comments on tasks
/api/portal/invoices/          - Portal user's invoices
/api/portal/chat-threads/      - Daily chat threads
/api/portal/messages/          - Chat messages
/api/portal/proposals/         - Proposals sent to client
/api/portal/contracts/         - Signed contracts
/api/portal/engagement-history/ - Engagement version history
```

### 2. Middleware Enforcement

**`PortalContainmentMiddleware`** enforces default-deny:

```python
# Portal users can ONLY access:
PORTAL_ALLOWED_PATHS = [
    '/api/portal/',        # All portal endpoints
    '/api/auth/login/',    # Login
    '/api/auth/logout/',   # Logout
    '/api/auth/profile/',  # Profile
]

# Portal users receive 403 on ALL other endpoints
```

**Middleware order (in settings.py):**
1. `FirmContextMiddleware` - Attaches firm to request
2. `PortalContainmentMiddleware` - Blocks portal users from firm admin endpoints

### 3. Permission Classes

**`DenyPortalAccess`** - Explicit firm-only permission:
```python
class MyFirmViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    # Portal users receive 403
```

**`IsPortalUser`** - Portal-only permission:
```python
class MyPortalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsPortalUser]
    # Only portal users can access
```

**`IsPortalUserOrFirmUser`** - Shared permission (different data):
```python
class MySharedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsPortalUserOrFirmUser]
    # Both can access, but get_queryset() filters differently
```

---

## Portal User Detection

Portal users are identified by the presence of a `ClientPortalUser` record:

```python
from modules.clients.models import ClientPortalUser

try:
    portal_user = ClientPortalUser.objects.get(user=request.user)
    # User is a portal user
except ClientPortalUser.DoesNotExist:
    # User is a firm user
```

---

## Firm Context Verification

Portal views verify that the portal user's client belongs to the request firm:

```python
def get_queryset(self):
    firm = get_request_firm(self.request)
    portal_user = ClientPortalUser.objects.get(user=self.request.user)

    # TIER 0: Verify portal user's client belongs to request firm
    if portal_user.client.firm_id != firm.id:
        return Model.objects.none()  # Security check

    # Return data for this client only
    return Model.objects.filter(client=portal_user.client)
```

---

## Portal Permissions (Granular)

Portal users have granular permission flags on `ClientPortalUser` model:

- `can_view_projects` - Can access /api/portal/projects/
- `can_view_billing` - Can access /api/portal/invoices/
- `can_message_team` - Can access /api/portal/chat-threads/ and messages
- `can_manage_users` - Can invite other portal users (future)

**Usage:**
```python
class ClientProjectViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        portal_user = ClientPortalUser.objects.get(user=self.request.user)

        if not portal_user.can_view_projects:
            return Project.objects.none()

        return Project.objects.filter(client=portal_user.client)
```

---

## Testing Portal Containment

### Test 1: Portal user accesses firm admin endpoint → 403

```bash
curl -H "Authorization: Bearer $PORTAL_TOKEN" \
     http://localhost:8000/api/crm/leads/

# Response: 403 Forbidden
{
    "error": "Access denied",
    "code": "PORTAL_ACCESS_DENIED",
    "message": "Portal users do not have access to this endpoint."
}
```

### Test 2: Portal user accesses portal endpoint → 200

```bash
curl -H "Authorization: Bearer $PORTAL_TOKEN" \
     http://localhost:8000/api/portal/projects/

# Response: 200 OK
[
    {
        "id": 1,
        "name": "Website Redesign",
        "status": "in_progress"
    }
]
```

### Test 3: Firm user accesses both → 200

```bash
# Firm user can access admin endpoints
curl -H "Authorization: Bearer $FIRM_TOKEN" \
     http://localhost:8000/api/crm/leads/
# Response: 200 OK

# Firm user can also access portal endpoints (sees all clients' data)
curl -H "Authorization: Bearer $FIRM_TOKEN" \
     http://localhost:8000/api/portal/projects/
# Response: 200 OK
```

---

## Files Created

1. **`modules/clients/permissions.py`** - Permission classes
2. **`modules/clients/middleware.py`** - PortalContainmentMiddleware
3. **`api/portal/urls.py`** - Portal namespace routing
4. **`config/urls.py`** - Added /api/portal/ namespace
5. **`config/settings.py`** - Added middleware

---

## Security Model

### Default-Deny Enforcement

```
┌─────────────────┐
│  Portal User    │
└────────┬────────┘
         │
         ├─ /api/auth/*          → ✅ Allowed (public)
         ├─ /api/portal/*        → ✅ Allowed (portal endpoints)
         ├─ /api/crm/*           → ❌ 403 Forbidden
         ├─ /api/clients/*       → ❌ 403 Forbidden
         ├─ /api/projects/*      → ❌ 403 Forbidden
         ├─ /api/finance/*       → ❌ 403 Forbidden
         ├─ /api/documents/*     → ❌ 403 Forbidden
         └─ /api/assets/*        → ❌ 403 Forbidden
```

### Firm User (No Restrictions)

```
┌─────────────────┐
│   Firm User     │
└────────┬────────┘
         │
         ├─ /api/auth/*          → ✅ Allowed
         ├─ /api/portal/*        → ✅ Allowed (sees all clients)
         ├─ /api/crm/*           → ✅ Allowed
         ├─ /api/clients/*       → ✅ Allowed
         ├─ /api/projects/*      → ✅ Allowed
         ├─ /api/finance/*       → ✅ Allowed
         ├─ /api/documents/*     → ✅ Allowed
         └─ /api/assets/*        → ✅ Allowed
```

---

## TIER 0 Compliance

**Task 0.4: Portal containment (default-deny)** ✅

- ✅ Portal-only permission classes created
- ✅ Separate routing namespace for portal (`/api/portal/`)
- ✅ Explicit allowlist of portal endpoints (8 ViewSets)
- ✅ Portal users receive 403 on non-portal endpoints (middleware)
- ✅ Defense-in-depth: Middleware + Permission classes
- ✅ Firm context verification in portal views

**Overall TIER 0 Progress: 67% (4/6 tasks complete)**

---

## Next Steps

**Task 0.5: Platform privacy enforcement (metadata-only)**
- Platform role separation (Operator vs Break-Glass)
- Explicit deny rules for content models
- Metadata/content separation
- Content encryption (E2EE)
