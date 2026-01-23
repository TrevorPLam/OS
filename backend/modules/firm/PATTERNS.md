# Code Patterns - Firm Module

**Folder:** `backend/modules/firm/`

This document contains common code patterns for the firm module. Use these patterns to maintain consistency.

## Firm-Scoped Model Pattern

```python
from modules.firm.utils import FirmScopedMixin
from django.db import models

class ModelName(FirmScopedMixin, models.Model):
    """
    Model with firm-scoped multi-tenancy.
    """
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='model_names',
        help_text='Firm (workspace) this belongs to'
    )

    # Business fields
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['-created_at']
```

## Viewset with Firm Scoping Pattern

```python
from modules.firm.utils import FirmScopedMixin
from rest_framework import viewsets
from .models import ModelName
from .serializers import ModelSerializer

class ModelViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet automatically scoped to request.firm.
    """
    queryset = ModelName.objects.all()
    serializer_class = ModelSerializer
```

## Firm-Scoped Query Pattern

```python
from modules.firm.utils import get_request_firm, firm_scoped_queryset

def my_view(request):
    # Get firm from request
    firm = get_request_firm(request)

    # Get firm-scoped queryset
    queryset = firm_scoped_queryset(ModelName, firm)

    # Or use the utility
    queryset = ModelName.firm_scoped.for_firm(firm)
```

## Firm Context Validation Pattern

```python
from modules.firm.utils import validate_firm_access, get_request_firm

def update_model(request, model_id):
    firm = get_request_firm(request)
    model = ModelName.objects.get(id=model_id)

    # Ensure model belongs to request firm
    validate_firm_access(model, firm)

    # Safe to proceed...
```

## Anti-Patterns (Don't Do This)

```python
# ❌ Bad: Query without firm scoping
def get_models(request):
    return ModelName.objects.all()  # Returns all firms' data!

# ✅ Good: Firm-scoped query
def get_models(request):
    firm = get_request_firm(request)
    return firm_scoped_queryset(ModelName, firm)

# ❌ Bad: Viewset without FirmScopedMixin
class ModelViewSet(viewsets.ModelViewSet):
    queryset = ModelName.objects.all()  # Not firm-scoped!

# ✅ Good: Viewset with FirmScopedMixin
class ModelViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    queryset = ModelName.objects.all()  # Automatically firm-scoped
```

---

**Note:** These patterns are examples. Always check existing code in this folder for the most current patterns.
