# GitHub Copilot Instructions for UBOS

This file provides context and guidance for GitHub Copilot and other AI coding assistants working on the UBOS (Unified Business Operating System) codebase.

---

## 🎯 Product Context

**UBOS** is an enterprise-grade unified platform for service firms. It consolidates CRM, client management, project delivery, billing, and operations into a single integrated system.

**Target Users**: Professional service firms (consulting, agencies, law, accounting) with 10-500 employees.

**Key Value Propositions**:
- Unified platform replacing 5-10 separate tools
- Built specifically for service firm workflows
- AI-native with governance framework
- Enterprise-grade security and multi-tenancy

For detailed product vision, see [PRODUCT.md](../PRODUCT.md).

---

## 🏗️ Architecture Principles

### System Design
- **Multi-Tenant**: Firm-scoped isolation at database level
- **Domain-Driven**: Modules organized by business domain
- **API-First**: RESTful API design with OpenAPI spec
- **Security-First**: Authentication, authorization, and data protection built-in
- **Microservices-Ready**: Modular Django apps for future scaling

### Technology Stack
- **Backend**: Django 4.2 + DRF, Python 3.11, PostgreSQL 15
- **Frontend**: React 18 + TypeScript 5.9, Vite 5.4, TanStack React Query
- **Testing**: pytest (backend), Vitest (frontend), Playwright (e2e)
- **Infrastructure**: Docker, GitHub Actions CI/CD

For detailed architecture, see [docs/architecture/README.md](../docs/architecture/README.md).

---

## 📋 Code Style & Conventions

### General Principles
1. **Consistency over novelty** - Follow existing patterns
2. **Explicit over implicit** - Clear, readable code
3. **Type safety** - Use TypeScript strictly, Python type hints
4. **Security-first** - Validate inputs, prevent injection, audit sensitive operations
5. **Performance-aware** - Consider N+1 queries, bundle size, caching

### Python/Django Backend

**Style**: Follow PEP 8, use Black formatter, use type hints.

```python
# Good - Type hints, clear naming, docstring
def calculate_deal_value(deal: Deal, probability_override: Optional[float] = None) -> Decimal:
    """
    Calculate weighted value of a deal based on probability.
    
    Args:
        deal: The deal instance
        probability_override: Optional probability override (0-1)
        
    Returns:
        Weighted deal value as Decimal
    """
    probability = probability_override or (deal.probability / 100.0)
    return deal.value * Decimal(str(probability))

# Avoid - No types, unclear naming, no docs
def calc(d, p=None):
    prob = p or (d.probability / 100.0)
    return d.value * Decimal(str(prob))
```

**Key Patterns**:
- Use Django ORM efficiently (select_related, prefetch_related)
- Firm-scoped queries: Always filter by `firm=request.user.firm`
- Use serializers for validation and transformation
- Permissions: Use Django's permission system + custom firm checks
- Use transactions for multi-step operations

**What to Avoid**:
- Don't use `objects.all()` without firm filtering (security risk!)
- Don't put business logic in views (use services/managers)
- Don't bypass serializer validation
- Don't commit secrets or credentials

### TypeScript/React Frontend

**Style**: Follow ESLint rules, use Prettier, strict TypeScript.

```typescript
// Good - Type safety, React Query, proper error handling
interface DealFormProps {
  dealId?: number;
  onSuccess: () => void;
}

export function DealForm({ dealId, onSuccess }: DealFormProps) {
  const createDeal = useCreateDeal();
  const updateDeal = useUpdateDeal();
  
  const { register, handleSubmit, formState: { errors } } = useForm<DealFormData>({
    resolver: zodResolver(dealSchema),
  });

  const onSubmit = handleSubmit((data) => {
    const mutation = dealId ? updateDeal : createDeal;
    mutation.mutate(
      { ...data, id: dealId },
      { onSuccess }
    );
  });

  return (
    <form onSubmit={onSubmit}>
      {/* Form fields */}
    </form>
  );
}

// Avoid - Manual state, direct API calls, no validation
export function DealForm() {
  const [deal, setDeal] = useState(null);
  
  const handleSubmit = async () => {
    const response = await fetch('/api/deals/', {
      method: 'POST',
      body: JSON.stringify(deal),
    });
    // No error handling, no types, manual state management
  };
}
```

**Key Patterns**:
- **Always use React Query** for data fetching (useQuery, useMutation)
- **Always use React Hook Form** for forms with validation
- Use TypeScript interfaces for props and data structures
- Organize by feature/module, not by type (no separate folders for "components", "hooks")
- Use semantic HTML and ARIA attributes for accessibility

**What to Avoid**:
- Don't use `useState` + `useEffect` for data fetching (use React Query!)
- Don't bypass form validation
- Don't use `any` type (use `unknown` if truly unknown)
- Don't create component files in wrong locations
- Don't use `window.confirm` (use custom ConfirmDialog component)

### File Organization

```
backend/
  modules/           # Django apps by domain
    core/           # Infrastructure (auth, firms, users)
    crm/            # CRM features
    clients/        # Client management
    projects/       # Project delivery
    finance/        # Billing and invoicing
    [module]/
      models.py     # Data models
      serializers.py # DRF serializers
      views.py      # API views
      services.py   # Business logic
      tests/        # Module tests

frontend/src/
  api/              # API client functions and hooks
  pages/            # Page components (route-level)
  components/       # Shared UI components
  hooks/            # Custom React hooks
  types/            # TypeScript type definitions
  utils/            # Utility functions
```

---

## 🔒 Security Guidelines

### Critical Rules
1. **Never commit secrets** - Use environment variables
2. **Always validate inputs** - Backend serializers, frontend forms
3. **Firm isolation** - Filter all queries by firm
4. **SQL injection** - Use ORM, never raw SQL with user input
5. **XSS prevention** - React escapes by default, use `dangerouslySetInnerHTML` cautiously
6. **Authentication** - JWT tokens, refresh token rotation
7. **Authorization** - Check permissions on every endpoint

### Security Checklist for New Features
- [ ] All API endpoints check user authentication
- [ ] All queries scoped to user's firm
- [ ] Input validation on backend (serializers)
- [ ] Input validation on frontend (forms)
- [ ] No secrets in code or version control
- [ ] Sensitive operations logged/audited
- [ ] CSRF protection enabled for mutations
- [ ] XSS prevention (proper escaping)

---

## 🧪 Testing Guidelines

### What to Test
- **Backend**: Models, serializers, views, business logic, permissions
- **Frontend**: API hooks, complex components, forms, utility functions
- **E2E**: Critical user flows (login, create deal, generate invoice)

### Testing Standards
- **Backend**: pytest, aim for 80%+ coverage on business logic
- **Frontend**: Vitest, aim for 60%+ coverage on critical paths
- **E2E**: Playwright, test happy paths and critical errors

```python
# Backend test example
def test_create_deal_scoped_to_firm(authenticated_client, firm, other_firm):
    """Verify deals are firm-scoped."""
    data = {"name": "Test Deal", "value": "10000"}
    response = authenticated_client.post("/api/crm/deals/", data)
    
    assert response.status_code == 201
    deal = Deal.objects.get(id=response.data["id"])
    assert deal.firm == firm  # Not other_firm!
```

```typescript
// Frontend test example
describe('useDealMutation', () => {
  it('creates deal and invalidates cache', async () => {
    const { result } = renderHook(() => useCreateDeal(), {
      wrapper: createQueryWrapper(),
    });
    
    await act(async () => {
      await result.current.mutate({
        name: 'Test Deal',
        value: '10000',
      });
    });
    
    expect(result.current.isSuccess).toBe(true);
    // Verify cache invalidation
  });
});
```

---

## 🤖 AI Governance Framework

UBOS has an **AI-native governance framework** that guides AI agent behavior. When working on this codebase, be aware of:

### Key Governance Files (in `.repo/`)
- `tasks/TODO.md` - Current active task (ONE task only)
- `tasks/BACKLOG.md` - Prioritized task queue
- `repo.manifest.yaml` - Canonical commands (don't guess!)
- `agents/QUICK_REFERENCE.md` - Essential rules for agents
- `policy/CONSTITUTION.md` - 8 articles governing AI agents
- `policy/PRINCIPLES.md` - 25 principles for code changes

### Important Rules for AI Assistants
1. **Read TODO.md first** - Understand the current task
2. **Use manifest commands** - Don't guess commands, use manifest
3. **Mark UNKNOWN** - If something is unclear, mark it and ask
4. **Include filepaths** - Always specify full paths in changes
5. **Link to tasks** - Connect changes to task in TODO.md
6. **Show verification** - Provide evidence (test output, screenshots)
7. **Think security** - Security/auth/money changes need HITL (Human-in-the-Loop)
8. **Respect boundaries** - Don't cross module boundaries without ADR

### Three-Pass Workflow
1. **Plan**: Determine change type, check boundaries, identify risks
2. **Change**: Apply edits following patterns
3. **Verify**: Run tests, show evidence, update logs

---

## 🚀 Development Workflow

### Setup
```bash
make setup      # Install all dependencies
make lint       # Run linters
make test       # Run tests
make verify     # Full CI checks
```

### Commands (from repo.manifest.yaml)
```bash
# Quick checks (before committing)
make lint && make frontend-build

# Full CI suite (before PR)
make verify SKIP_HEAVY=0

# Backend-specific
make -C backend migrate
make -C backend openapi

# Frontend-specific
make -C frontend test
make -C frontend e2e
```

### Before Committing
1. Run `make lint` - Fix any linting errors
2. Run relevant tests - Ensure tests pass
3. Update docs if behavior changed
4. Check for secrets in code
5. Verify files committed are expected (no artifacts)

---

## 🎓 Common Tasks & Patterns

### Adding a New API Endpoint (Backend)

1. **Model** (if needed): `backend/modules/[module]/models.py`
2. **Serializer**: `backend/modules/[module]/serializers.py`
3. **View**: `backend/modules/[module]/views.py`
4. **URL**: `backend/modules/[module]/urls.py`
5. **Permissions**: Check firm scope + custom permissions
6. **Test**: `backend/modules/[module]/tests/test_views.py`

### Adding a New Page (Frontend)

1. **Page Component**: `frontend/src/pages/[Page].tsx`
2. **API Hook** (if needed): `frontend/src/api/[module].ts`
3. **Route**: Add to `frontend/src/App.tsx`
4. **Navigation**: Update sidebar in `frontend/src/components/Sidebar.tsx`
5. **Test**: `frontend/src/pages/__tests__/[Page].test.tsx`

### Refactoring to React Query

**Before** (anti-pattern):
```typescript
const [data, setData] = useState(null);
const [loading, setLoading] = useState(false);

useEffect(() => {
  const fetchData = async () => {
    setLoading(true);
    const result = await api.getData();
    setData(result);
    setLoading(false);
  };
  fetchData();
}, []);
```

**After** (correct pattern):
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['data'],
  queryFn: api.getData,
});
```

---

## 📚 Key Documentation

- [PRODUCT.md](../PRODUCT.md) - Product vision and business context
- [README.md](../README.md) - Project overview and setup
- [ARCHITECTURE.md](../docs/architecture/README.md) - System architecture
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](../SECURITY.md) - Security policies
- [.repo/agents/QUICK_REFERENCE.md](../.repo/agents/QUICK_REFERENCE.md) - Agent rules

---

## ❓ When You're Unsure

1. **Check existing patterns** - Look for similar code in the codebase
2. **Read the docs** - Check architecture and module docs
3. **Ask for clarification** - Create HITL if something is UNKNOWN
4. **Follow conventions** - Consistency over novelty
5. **Test your changes** - Verify behavior before committing

---

## 🔗 Helpful Links

- **Repository**: https://github.com/TrevorPLam/OS
- **Tech Stack Docs**:
  - Django: https://docs.djangoproject.com/
  - Django REST Framework: https://www.django-rest-framework.org/
  - React: https://react.dev/
  - TanStack React Query: https://tanstack.com/query/latest
  - TypeScript: https://www.typescriptlang.org/docs/
  - Vite: https://vitejs.dev/

---

**Last Updated**: 2026-01-24  
**Copilot Version**: Optimized for GitHub Copilot, Cursor, and other AI coding assistants
