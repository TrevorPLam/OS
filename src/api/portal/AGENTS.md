# AGENTS.md — Portal API (Client Self-Service)

Last Updated: 2026-01-06
Applies To: `src/api/portal/`

## Purpose

Client portal endpoints. **CRITICAL SECURITY BOUNDARY** — portal users can ONLY access these endpoints.

## Security Rules

1. **Default Deny**: Portal users cannot access any endpoint outside `/api/v1/portal/`
2. **Data Scoping**: All queries scoped to the portal user's client
3. **Limited Fields**: Serializers expose only client-safe fields
4. **No Internal Notes**: Internal notes, staff comments hidden

## Key Components

| File | Purpose |
|------|---------|
| `views.py` | Portal-specific ViewSets |
| `serializers.py` | Client-safe serializers |
| `throttling.py` | Portal-specific rate limits |
| `urls.py` | Portal URL routes |

## Available Endpoints

```
GET        /profile/               # Client's own profile
GET        /engagements/           # Their engagements
GET        /projects/              # Their projects
GET        /documents/             # Shared documents
GET        /invoices/              # Their invoices
POST       /invoices/{id}/pay/     # Pay invoice
GET        /messages/              # Conversations
POST       /messages/              # Send message
GET        /support/tickets/       # Support tickets
POST       /support/tickets/       # Create ticket
```

## Permission Classes

```python
from api.portal.permissions import IsPortalUser

class PortalViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsPortalUser]
    
    def get_queryset(self):
        # CRITICAL: Scope to portal user's client only
        return self.model.objects.filter(
            client=self.request.user.portal_profile.client
        )
```

## Testing Portal Containment

See `tests/safety/test_portal_containment.py` — verifies portal users cannot escape boundary.
