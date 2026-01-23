# Code Patterns - Clients Module

**Folder:** `backend/modules/clients/`

This document contains common code patterns for the clients module. Use these patterns to maintain consistency.

## Model Pattern

```python
from modules.firm.utils import FirmScopedMixin
from django.db import models

class Client(FirmScopedMixin, models.Model):
    """
    Client model with firm-scoped multi-tenancy.
    """
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='clients',
        help_text='Firm (workspace) this client belongs to'
    )

    # Business fields
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
```

## Viewset Pattern

```python
from modules.firm.utils import FirmScopedMixin
from rest_framework import viewsets
from .models import Client
from .serializers import ClientSerializer

class ClientViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Client CRUD operations.

    Automatically scoped to request.firm via FirmScopedMixin.
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    # get_queryset() is automatically implemented to scope to request.firm
```

## Serializer Pattern

```python
from rest_framework import serializers
from .models import Client

class ClientSerializer(serializers.ModelSerializer):
    """
    Serializer for Client model.
    """
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['firm', 'created_at', 'updated_at']
```

## Test Pattern

```python
import pytest
from django.contrib.auth import get_user_model
from modules.firm.models import Firm
from modules.clients.models import Client

@pytest.fixture
def firm():
    return Firm.objects.create(name='Test Firm', slug='test-firm')

@pytest.fixture
def client(firm):
    return Client.objects.create(firm=firm, name='Test Client')

def test_client_creation(client):
    assert client.firm is not None
    assert client.name == 'Test Client'
```

## Anti-Patterns (Don't Do This)

```python
# ❌ Bad: Missing firm ForeignKey
class Client(models.Model):
    name = models.CharField(max_length=255)
    # Missing: firm = models.ForeignKey(...)

# ✅ Good: Firm-scoped model
class Client(FirmScopedMixin, models.Model):
    firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

# ❌ Bad: Viewset without FirmScopedMixin
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()  # Not firm-scoped!

# ✅ Good: Viewset with FirmScopedMixin
class ClientViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    queryset = Client.objects.all()  # Automatically firm-scoped
```

---

**Note:** These patterns are examples. Always check existing code in this folder for the most current patterns.
