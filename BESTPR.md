# BESTPR.md — Best Practices for Quality Code

Document Type: Best Practices Guide
Version: 1.1.0
Last Updated: 2026-01-21
Status: Active

## Purpose

Token-optimized, repo-specific guide to ship quality, complementary code the first time, every time. This guide consolidates critical patterns, conventions, and invariants specific to this codebase.

## Authority & Reading Order

**READ FIRST**: This document is subordinate to:
1. `CODEBASECONSTITUTION.md` (highest authority)
2. `READMEAI.md` (operating model)
3. `AGENTS.md` (agent behavior rules)
4. `P0TODO.md` / `P1TODO.md` / `P2TODO.md` / `P3TODO.md` (task truth source)

**USE THIS GUIDE**: When implementing features, fixing bugs, or reviewing code.

---

## 1. Architecture Overview

### System Type
**Multi-tenant SaaS platform** (ConsultantPro) for management consulting firms.

- **Backend**: Django 4.2 LTS (modular monolith)
- **Frontend**: React 18 + TypeScript (Vite)
- **Database**: PostgreSQL 15 with Row-Level Security (RLS)
- **Architecture**: Modular monolith, NOT microservices

### Directory Structure
```
/
├── src/
│   ├── modules/          # 30+ business domain modules (modular monolith)
│   ├── api/              # REST API endpoints (serializers, views)
│   ├── config/           # Django settings, URLs, middleware
│   ├── frontend/         # React + TypeScript (Vite)
│   └── templates/        # Django templates
├── tests/                # Test suite (pytest + Django test framework)
├── docs/                 # Documentation, runbooks, specs
├── benchmarks/           # Performance benchmarking
└── .github/workflows/    # GitHub Actions workflows
```

---

## 2. TIER 0 INVARIANTS (CRITICAL - NEVER VIOLATE)

### 2.1 Firm Isolation (Multi-Tenancy)

**RULE**: Every query MUST be scoped to a firm. Cross-tenant data access is a critical security vulnerability.

#### Required Patterns

**Models** (311 occurrences in codebase):
```python
from modules.firm.utils import FirmScopedManager

class MyModel(models.Model):
    # REQUIRED: Firm foreign key
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="my_models",
    )
    
    # REQUIRED: Use FirmScopedManager
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
```

**ViewSets**:
```python
from modules.firm.utils import FirmScopedMixin

class MyViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    model = MyModel
    serializer_class = MySerializer
    # get_queryset() automatically scopes to request.firm
```

**Manual Queries**:
```python
# CORRECT
queryset = MyModel.objects.for_firm(request.firm)

# WRONG - FORBIDDEN
queryset = MyModel.objects.all()  # Cross-tenant leak!
```

**Enforcement**: See `src/modules/firm/utils.py` for `FirmScopedQuerySet`, `FirmScopedManager`, and `FirmScopingError`.

### 2.2 Portal vs Staff Separation

**RULE**: Portal users (clients) and staff users have separate endpoints.

- **Staff**: `/api/v1/{module}/` (requires staff auth)
- **Portal**: `/api/v1/portal/` (client portal users only)

**Portal users MUST NOT access staff endpoints.**

### 2.3 No Content Logging

**RULE**: Customer content MUST NOT appear in logs.

```python
# CORRECT
from modules.core.structured_logging import log_event

log_event("document_uploaded", {
    "document_id": doc.id,
    "firm_id": firm.id,
    # DO NOT include document content, names, or PII
})

# WRONG
logger.info(f"Document content: {doc.content}")  # FORBIDDEN
```

### 2.4 Immutability Rules

**RULE**: Published entities are immutable.

- `pricing.RuleSet` (status='published')
- `crm.QuoteVersion` (is_locked=True)
- `delivery.DeliveryTemplate` (status='published')

Once published, create new versions instead of modifying.

---

## 3. Module Organization (Modular Monolith)

### 3.1 Module Tiers

**TIER 0 - Foundation (CRITICAL)**:
- `firm/` — Multi-tenant boundary (ALL isolation depends on this)
- `auth/` — Authentication, authorization, MFA

**Core Business**:
- `crm/` — Pre-sale: Lead → Prospect → Proposal workflow
- `clients/` — Post-sale: Client management, portal
- `projects/` — Project execution, tasks, time tracking
- `finance/` — Billing, invoicing, payments
- `documents/` — Document management, versioning

**Engines**:
- `pricing/` — Versioned pricing rulesets
- `delivery/` — Delivery template DAGs
- `recurrence/` — Recurring event generation
- `orchestration/` — Multi-step workflow execution
- `automation/` — Visual workflow builder

**Communications**:
- `email_ingestion/` — Gmail/Outlook ingestion
- `calendar/` — Scheduling, booking links
- `sms/` — Twilio messaging
- `communications/` — Conversations, threads

**Integrations**:
- `accounting_integrations/` — QuickBooks, Xero
- `esignature/` — DocuSign
- `ad_sync/` — Active Directory
- `webhooks/` — Webhook platform

### 3.2 Module Structure

Each module follows this pattern:
```
modules/{module_name}/
├── AGENTS.md           # Module-specific agent instructions
├── models.py           # Django models
├── views.py            # ViewSets for staff API
├── serializers.py      # DRF serializers
├── urls.py             # URL routing
├── signals.py          # Post-save hooks (optional)
├── tasks.py            # Background jobs (optional)
└── migrations/         # Database migrations
```

### 3.3 Adding a New Module

1. Create module directory under `src/modules/`
2. Create `AGENTS.md` referencing `BESTPR.md`
3. Define models with `FirmScopedManager`
4. Create serializers and viewsets with `FirmScopedMixin`
5. Register URLs in `src/config/urls.py`
6. Add tests in `tests/{module_name}/`

---

## 4. Django Patterns

### 4.1 Models

**Required**:
```python
from django.db import models
from modules.firm.utils import FirmScopedManager

class MyModel(models.Model):
    """
    Brief description.
    
    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    
    # TIER 0: Firm foreign key (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="my_models",
        help_text="Firm this entity belongs to",
    )
    
    # Fields
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=[("active", "Active"), ("archived", "Archived")],
        default="active",
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Managers (REQUIRED for firm-scoped models)
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "myapp_mymodel"
        indexes = [
            models.Index(fields=["firm", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["firm", "name"],
                name="unique_mymodel_per_firm",
            ),
        ]
    
    def __str__(self):
        return f"{self.name} (Firm: {self.firm_id})"
```

### 4.2 ViewSets

**Standard Pattern**:
```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from config.query_guards import QueryTimeoutMixin
from modules.auth.role_permissions import IsStaffUser, IsManager
from modules.firm.utils import FirmScopedMixin

class MyModelViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for MyModel.
    
    QueryTimeoutMixin: Applies statement timeout to list queries (default 3000ms)
    FirmScopedMixin: Automatically scopes queries to request.firm
    """
    model = MyModel
    serializer_class = MyModelSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    # get_queryset() is handled by FirmScopedMixin
    
    def perform_create(self, serializer):
        # Firm is set automatically by FirmScopedMixin
        serializer.save()
    
    # Custom actions
    @action(detail=True, methods=["post"], url_path="custom-action")
    def custom_action(self, request, pk=None):
        """Custom action on a single object."""
        obj = self.get_object()
        # Perform action
        return Response({"status": "success"})
    
    @action(detail=False, methods=["post"], url_path="bulk-action")
    def bulk_action(self, request):
        """Custom action on multiple objects."""
        # Perform bulk action
        return Response({"processed": 0})
```

**Permission Classes**:
- `IsAuthenticated` — User must be logged in
- `IsStaffUser` — Staff member (not portal user)
- `IsManager` — Manager-level permissions
- `IsFirmAdmin` — Firm admin role

**Mixin Order Matters**:
```python
# CORRECT ORDER: QueryTimeoutMixin first, then FirmScopedMixin
class MyViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    pass

# WRONG: FirmScopedMixin first breaks query timeout
class MyViewSet(FirmScopedMixin, QueryTimeoutMixin, viewsets.ModelViewSet):
    pass  # Query timeout won't work properly
```

### 4.3 Serializers

**Standard Pattern**:
```python
from rest_framework import serializers

class MyModelSerializer(serializers.ModelSerializer):
    # Computed fields
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MyModel
        fields = [
            "id",
            "name",
            "status",
            "created_at",
            "updated_at",
            "display_name",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_display_name(self, obj):
        return f"{obj.name} ({obj.status})"
    
    def validate_name(self, value):
        """Field-level validation."""
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate(self, data):
        """Object-level validation."""
        if data.get("status") == "archived" and not data.get("archived_reason"):
            raise serializers.ValidationError({
                "archived_reason": "Required when status is archived"
            })
        return data
```

**Validation Patterns**:
```python
# Field-level validation
def validate_<field_name>(self, value):
    if not is_valid(value):
        raise serializers.ValidationError("Error message")
    return value

# Object-level validation
def validate(self, data):
    if condition:
        raise serializers.ValidationError({
            "field_name": "Error message"
        })
    return data

# Validation with multiple fields
def validate(self, data):
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    if end_date and end_date < start_date:
        raise serializers.ValidationError({
            "end_date": "End date must be after start date"
        })
    return data
```

### 4.4 URLs

**Standard Pattern**:
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyModelViewSet

router = DefaultRouter()
router.register(r"mymodels", MyModelViewSet, basename="mymodel")

urlpatterns = [
    path("", include(router.urls)),
]
```

### 4.5 Signals

**Pattern** (7 signal files in codebase):
```python
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import MyModel

@receiver(pre_save, sender=MyModel)
def validate_before_save(sender, instance, **kwargs):
    """Validation that runs before save."""
    if instance.status == "published" and not instance.reviewed_by:
        raise ValueError("Published items must be reviewed")

@receiver(post_save, sender=MyModel)
def trigger_downstream_actions(sender, instance, created, **kwargs):
    """Actions to take after save."""
    if created:
        # Trigger notifications, create related objects, etc.
        notify_team(instance)
```

**When to Use Signals**:
- ✅ Cross-module notifications (avoid circular imports)
- ✅ Audit logging
- ✅ Triggering background jobs
- ❌ Business logic (put in model methods or services)
- ❌ Data validation (use model clean() or serializer validate())

**Signal Files in Codebase**:
- `accounting_integrations/signals.py`
- `calendar/signals.py`
- `projects/signals.py`
- `crm/signals.py`
- `clients/signals.py`
- `finance/signals.py`
- `webhooks/signals.py`

### 4.6 Config Imports

**Common config utilities** (from `src/config/`):

```python
# Query timeouts for API endpoints
from config.query_guards import QueryTimeoutMixin, query_timeout

# Custom filters
from config.filters import BoundedSearchFilter

# Error handling
from config.sentry import capture_exception_with_context, capture_message_with_context

# Pagination
from config.pagination import StandardResultsSetPagination

# Throttling
from config.throttling import BurstRateThrottle, SustainedRateThrottle
```

**Example Usage**:
```python
from config.query_guards import QueryTimeoutMixin, query_timeout

class MyViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    # Applies 3000ms timeout to list() queries
    query_timeout_ms = 3000

# Manual timeout
with query_timeout(5000):
    # Query runs with 5 second timeout
    expensive_query()
```

### 4.7 Dynamic QuerySets & Serializers

**Pattern** (common in codebase):

```python
class MyViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    model = MyModel
    
    def get_queryset(self):
        """
        Override to add filtering, prefetching, or custom logic.
        IMPORTANT: Always call super() to maintain firm scoping.
        """
        queryset = super().get_queryset()  # Gets firm-scoped queryset
        
        # Add prefetching for performance
        queryset = queryset.select_related('owner', 'firm')
        queryset = queryset.prefetch_related('tags', 'attachments')
        
        # Add filtering based on query params
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'list':
            return MyModelListSerializer  # Lightweight for lists
        elif self.action == 'retrieve':
            return MyModelDetailSerializer  # Full detail
        return MyModelSerializer  # Default
```

**CRITICAL**: Always call `super().get_queryset()` in firm-scoped ViewSets to maintain tenant isolation.

---

## 4.8 Common Anti-Patterns (AVOID)

**❌ WRONG: Direct Model.objects.all()**:
```python
# SECURITY VULNERABILITY - Cross-tenant leak
clients = Client.objects.all()
```

**✅ CORRECT: Use firm scoping**:
```python
clients = Client.objects.for_firm(request.firm)
# OR in ViewSet (automatic)
clients = self.get_queryset()
```

**❌ WRONG: Forgetting super() in get_queryset()**:
```python
def get_queryset(self):
    # BUG: Bypasses firm scoping!
    return MyModel.objects.filter(status='active')
```

**✅ CORRECT: Always call super()**:
```python
def get_queryset(self):
    queryset = super().get_queryset()  # Maintains firm scoping
    return queryset.filter(status='active')
```

**❌ WRONG: Wrong mixin order**:
```python
# BUG: Query timeout doesn't work
class MyViewSet(FirmScopedMixin, QueryTimeoutMixin, viewsets.ModelViewSet):
    pass
```

**✅ CORRECT: QueryTimeoutMixin first**:
```python
class MyViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    pass
```

**❌ WRONG: N+1 queries**:
```python
# Slow - hits database for each client
for client in clients:
    print(client.account_manager.name)  # Extra query!
```

**✅ CORRECT: Use select_related**:
```python
clients = Client.objects.select_related('account_manager')
for client in clients:
    print(client.account_manager.name)  # No extra query
```

---

## 5. Frontend Patterns (React + TypeScript)

### 5.1 Tech Stack

- React 18 + TypeScript
- Vite (build tool)
- React Router (routing)
- React Query / TanStack Query (data fetching)
- Axios (HTTP client)
- React Flow (visual workflow builder)

### 5.2 API Client

**Pattern**:
```typescript
// src/api/client.ts
import apiClient from './api/client'

// All requests include auth token automatically
const response = await apiClient.get('/clients/')
```

### 5.3 Page Component

**Pattern**:
```typescript
// src/pages/MyPage.tsx
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'

export function MyPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['my-data'],
    queryFn: () => apiClient.get('/my-endpoint/'),
  })

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorBoundary error={error} />

  return <div>{/* render data */}</div>
}
```

### 5.4 API Module

**Pattern**:
```typescript
// src/api/myModule.ts
import apiClient from './client'

export const myApi = {
  list: () => apiClient.get('/my-endpoint/'),
  get: (id: string) => apiClient.get(`/my-endpoint/${id}/`),
  create: (data: MyType) => apiClient.post('/my-endpoint/', data),
  update: (id: string, data: MyType) => 
    apiClient.put(`/my-endpoint/${id}/`, data),
  delete: (id: string) => apiClient.delete(`/my-endpoint/${id}/`),
}
```

### 5.5 Background Jobs & Tasks

**Pattern** (limited usage in codebase):

Background jobs are used sparingly. When needed:

```python
# Example from ad_sync/tasks.py
from modules.jobs.models import Job

def sync_ad_users(firm_id: int):
    """
    Background task for syncing AD users.
    
    Always scope operations to firm_id parameter.
    """
    firm = Firm.objects.get(id=firm_id)
    # Perform sync operations
    ...
    return {"synced": count}
```

**When to Use Background Jobs**:
- Long-running operations (>5 seconds)
- Scheduled tasks (cron-like)
- Operations that can be retried on failure
- Non-user-facing operations

**When NOT to Use**:
- User-facing operations requiring immediate feedback
- Operations requiring transactional consistency
- Simple operations (<1 second)

---

## 6. Testing Patterns

### 6.1 Test Structure

```
tests/
├── {module_name}/
│   ├── test_models.py           # Model tests
│   ├── test_serializers.py      # Serializer tests
│   ├── test_views.py            # View/API tests
│   └── __init__.py
└── e2e/
    ├── test_hero_flows.py       # Critical user journeys
    └── test_tenant_isolation.py # Multi-tenancy tests
```

### 6.2 Model Tests

**Pattern**:
```python
import pytest
from modules.firm.models import Firm
from modules.mymodule.models import MyModel

@pytest.fixture
def firm(db):
    return Firm.objects.create(
        name="Test Firm",
        slug="test-firm",
        status="active",
    )

@pytest.mark.django_db
class TestMyModel:
    def test_creation(self, firm):
        obj = MyModel.objects.create(
            firm=firm,
            name="Test Object",
        )
        assert obj.name == "Test Object"
        assert obj.firm == firm
    
    def test_firm_scoping(self, firm):
        firm2 = Firm.objects.create(
            name="Other Firm",
            slug="other-firm",
            status="active",
        )
        
        obj1 = MyModel.objects.create(firm=firm, name="Obj1")
        obj2 = MyModel.objects.create(firm=firm2, name="Obj2")
        
        # Test firm isolation
        assert list(MyModel.objects.for_firm(firm)) == [obj1]
        assert list(MyModel.objects.for_firm(firm2)) == [obj2]
```

### 6.3 E2E Tests

**Pattern**:
```python
import pytest
from rest_framework.test import APIClient

@pytest.mark.e2e
@pytest.mark.django_db
class TestUserFlow:
    def test_complete_workflow(self, firm, user):
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Test complete user journey
        # 1. Create entity
        response = client.post('/api/v1/mymodels/', {
            'name': 'Test',
        })
        assert response.status_code == 201
        
        # 2. Retrieve entity
        obj_id = response.data['id']
        response = client.get(f'/api/v1/mymodels/{obj_id}/')
        assert response.status_code == 200
```

### 6.4 Running Tests

```bash
# All tests
make test

# Single module
pytest tests/mymodule/

# E2E only
pytest tests/e2e/ -m e2e

# Performance tests
make test-performance
```

---

## 7. Security Best Practices

### 7.1 Secrets Management

**RULE**: Never commit secrets to git.

```python
# CORRECT - Use environment variables
import os
SECRET_KEY = os.environ.get('SECRET_KEY')

# WRONG
SECRET_KEY = 'hardcoded-secret-123'  # FORBIDDEN
```

### 7.2 Authentication

**JWT Tokens** (Primary):
- Access tokens expire in 15 minutes
- Refresh tokens are single-use
- All API requests include: `Authorization: Bearer <token>`

**MFA** (Optional):
- Required for sensitive operations
- TOTP via django-otp

### 7.3 Authorization

**Roles**:
- `master_admin` — Full platform access
- `firm_admin` — Firm-level admin
- `staff` — Standard firm user
- `portal_user` — Client portal access only

**Permission Classes**:
```python
from rest_framework.permissions import IsAuthenticated
from modules.auth.permissions import IsFirmStaff

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsFirmStaff]
```

### 7.4 Input Validation

**ALWAYS validate and sanitize user input**:
```python
def validate_email(self, value):
    if not value or '@' not in value:
        raise serializers.ValidationError("Invalid email")
    return value.lower().strip()
```

---

## 8. Code Quality Standards

### 8.1 Linting & Formatting

**Python**:
- **Ruff**: Modern linter (replaces flake8, isort, pyupgrade)
- **Black**: Code formatter (120 char line length)
- **mypy**: Type checking (strict mode with exceptions)

```bash
# Run linting
make lint

# Format code
black src/
ruff check --fix src/
```

**TypeScript**:
- **ESLint**: Linting
- **Prettier**: Formatting (coming soon)

```bash
cd src/frontend
npm run lint
```

### 8.2 Type Hints

**Use type hints for all public functions**:
```python
from typing import List, Optional

def get_active_clients(firm: Firm) -> List[Client]:
    """Get all active clients for a firm."""
    return Client.objects.for_firm(firm).filter(status="active")
```

### 8.3 Documentation

**Module Docstrings**:
```python
"""
Module Name.

Brief description of what this module does.

TIER 0: All entities belong to exactly one Firm (tenant boundary).
"""
```

**Function Docstrings**:
```python
def calculate_invoice_total(items: List[LineItem]) -> Decimal:
    """
    Calculate total invoice amount including tax.
    
    Args:
        items: List of line items to sum
    
    Returns:
        Total amount as Decimal
    
    Raises:
        ValueError: If items list is empty
    """
```

---

## 9. Performance Best Practices

### 9.1 Database Queries

**Use select_related and prefetch_related**:
```python
# CORRECT - Single query with joins
clients = Client.objects.select_related(
    'firm', 'account_manager'
).prefetch_related('projects')

# WRONG - N+1 queries
clients = Client.objects.all()
for client in clients:
    print(client.firm.name)  # Extra query per client!
```

### 9.2 Indexing

**Add indexes for frequently queried fields**:
```python
class Meta:
    indexes = [
        models.Index(fields=["firm", "status"]),
        models.Index(fields=["created_at"]),
    ]
```

### 9.3 Query Budgets

**Track query counts in tests**:
```python
from tests.utils.query_budget import assert_query_budget

@assert_query_budget(max_queries=5)
def test_dashboard_view(client, firm):
    # Test ensures view uses ≤5 queries
    response = client.get('/api/dashboard/')
```

---

## 10. Common Workflows

### 10.1 Adding a New Feature

1. **Create task in `P0TODO.md`, `P1TODO.md`, `P2TODO.md`, or `P3TODO.md`**
2. **Read relevant `AGENTS.md` files**
3. **Check existing patterns** (grep for similar code)
4. **Implement with firm scoping**
5. **Add tests** (unit + integration)
6. **Run linter**: `make lint`
7. **Run tests**: `make test`
8. **Update docs** if needed
9. **Commit with descriptive message**

### 10.2 Fixing a Bug

1. **Write failing test** that reproduces bug
2. **Fix the bug**
3. **Verify test passes**
4. **Run full test suite**: `make test`
5. **Commit with `fix:` prefix**

### 10.3 Refactoring

1. **Create task in `P0TODO.md`, `P1TODO.md`, `P2TODO.md`, or `P3TODO.md`** with rationale
2. **Ensure tests exist** (add if missing)
3. **Refactor incrementally**
4. **Run tests after each step**
5. **Update documentation**
6. **Get code review**

---

## 11. Git & Version Control

### 11.1 Commit Messages

**Format**:
```
<type>: <short description>

<optional body>
```

**Types**:
- `feat:` — New feature
- `fix:` — Bug fix
- `refactor:` — Code refactoring
- `test:` — Add/update tests
- `docs:` — Documentation changes
- `chore:` — Build/tooling changes

### 11.2 Branch Strategy

- `main` — Production-ready code
- `copilot/*` — Feature branches created by agents

### 11.3 PR Guidelines

- Keep PRs small and focused
- Include tests
- Update relevant documentation
- Request review from relevant module owner

---

## 12. Module-Specific References

For module-specific patterns and conventions, see:
- `src/AGENTS.md` — Backend overview
- `src/modules/{module}/AGENTS.md` — Module-specific guide
- `src/frontend/AGENTS.md` — Frontend overview
- `src/api/AGENTS.md` — API layer patterns

---

## 13. Quick Reference Card

### Critical Patterns to Remember

**Firm Scoping**:
```python
# Models
firm = models.ForeignKey("firm.Firm", on_delete=models.CASCADE)
objects = models.Manager()
firm_scoped = FirmScopedManager()

# ViewSets (mixin order matters!)
class MyViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    model = MyModel
    permission_classes = [IsAuthenticated, IsStaffUser]

# Queries
MyModel.objects.for_firm(request.firm)

# ALWAYS call super() in get_queryset()
def get_queryset(self):
    queryset = super().get_queryset()  # Maintains firm scoping
    return queryset.filter(status='active')
```

**Custom Actions**:
```python
@action(detail=True, methods=["post"], url_path="custom-action")
def custom_action(self, request, pk=None):
    obj = self.get_object()
    return Response({"status": "success"})
```

**Validation**:
```python
def validate(self, data):
    if condition:
        raise serializers.ValidationError({
            "field": "Error message"
        })
    return data
```

**Testing**:
```python
@pytest.mark.django_db
def test_my_feature(firm):
    # Test implementation
    pass
```

**Linting**:
```bash
make lint       # Backend + frontend + docs
make test       # Run test suite
```

**Documentation**:
- Read: `CODEBASECONSTITUTION.md` → `READMEAI.md` → `AGENTS.md` → `BESTPR.md`
- Module: `src/modules/{module}/AGENTS.md`

---

## 15. Amendment Protocol

Changes to this document require:
1. A task in `P0TODO.md`, `P1TODO.md`, `P2TODO.md`, or `P3TODO.md`
2. Rationale in the change description
3. Update `Last Updated` date and version
4. Notify all agents via `AGENTS.md` updates

---

## Quick Links

- **Governance**: `CODEBASECONSTITUTION.md`
- **Operating Model**: `READMEAI.md`
- **Agent Rules**: `AGENTS.md`
- **Task Truth**: `P0TODO.md`, `P1TODO.md`, `P2TODO.md`, `P3TODO.md`
- **Project Status**: `PROJECT_STATUS.md`
- **Verification**: `repo.manifest.yaml`

---

**Remember**: When in doubt, check existing code for patterns. Grep is your friend.

```bash
# Find examples
grep -r "FirmScopedMixin" src/modules/
grep -r "class.*ViewSet" src/modules/

# Find tests
find tests/ -name "test_*.py"
```
