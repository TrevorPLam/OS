# AGENTS.md — API Layer

Last Updated: 2026-01-06
Applies To: `src/api/`

## Purpose

Public-facing REST API endpoints. This layer wraps `modules/` with serializers and views.

## Directory Structure

```
api/
├── assets/           # Asset management endpoints
├── clients/          # Client endpoints (staff + public)
├── crm/              # CRM endpoints
├── documents/        # Document endpoints (staff + public)
├── finance/          # Finance endpoints + payment webhooks
├── portal/           # Client portal endpoints (CRITICAL BOUNDARY)
├── projects/         # Project endpoints
└── webhooks/         # General webhook endpoints
```

## Critical Security Boundary

### Staff Endpoints vs Portal Endpoints

```
/api/v1/clients/      → Staff only (full client management)
/api/v1/crm/          → Staff only (leads, prospects, deals)
/api/v1/projects/     → Staff only (project management)

/api/v1/portal/       → Portal users ONLY (client self-service)
```

**Portal users MUST NOT access staff endpoints.**

## Common Patterns

### ViewSet Structure

```python
from rest_framework import viewsets
from modules.firm.utils import FirmScopedMixin

class MyViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    serializer_class = MySerializer
    model = MyModel
    
    # Permissions
    permission_classes = [IsAuthenticated, IsFirmMember]
```

### Public Views

For endpoints without authentication:

```python
from rest_framework.permissions import AllowAny

class PublicViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    # Must still validate firm context from URL/token
```

### Serializer Pattern

```python
from rest_framework import serializers

class MySerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = [...]
        read_only_fields = ["id", "created_at", "firm"]
    
    def create(self, validated_data):
        # Add firm from request context
        validated_data["firm"] = self.context["request"].firm
        return super().create(validated_data)
```

## Payment Webhooks

Special handling in `api/finance/`:

- `webhooks.py` — Stripe webhooks
- `square_webhooks.py` — Square webhooks

These verify signatures and update payment records.

## Public Endpoints

Some endpoints allow unauthenticated access:

| Path | Purpose |
|------|---------|
| `/api/v1/public/file-requests/` | Upload files via public link |
| `/api/v1/public/shares/` | Access shared documents |
| `/api/v1/public/confirm-opt-in/` | Email opt-in confirmation |
| `/api/v1/public/unsubscribe/` | Email unsubscribe |

## Dependencies

- **Wraps**: All `modules/`
- **Used by**: Frontend, external integrations
