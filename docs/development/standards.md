# Code Standards

Coding standards and conventions for UBOS.

## General Principles

1. **Consistency** - Follow existing patterns
2. **Clarity** - Code should be self-documenting
3. **Type Safety** - Use type hints (Python) and TypeScript
4. **Testing** - Write tests for new code
5. **Documentation** - Document complex logic

## Backend Standards (Python/Django)

### Code Style
- Follow PEP 8
- Use `black` for formatting
- Use `ruff` for linting
- Type hints preferred

### Django Patterns
- Use Django REST Framework viewsets
- Firm-scoped models (use `FirmScopedMixin`)
- Follow Django conventions
- Use migrations for schema changes

### Example
```python
from modules.core.models import FirmScopedMixin
from rest_framework import viewsets

class ClientViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """Client management viewset."""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
```

## Frontend Standards (TypeScript/React)

### Code Style
- Use TypeScript strict mode
- Follow React best practices
- Use functional components
- Prefer hooks over classes

### Patterns
- Use TanStack React Query for data fetching
- Use React Hook Form for forms
- Keep components small and focused
- Use TypeScript types

### Example
```typescript
import { useQuery } from '@tanstack/react-query';

export const ClientList: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: fetchClients,
  });

  // Component implementation
};
```

## File Organization

### Backend
- Models in `models.py`
- Views in `views.py`
- Serializers in `serializers.py`
- URLs in `urls.py`

### Frontend
- Components in `src/components/`
- Pages in `src/pages/`
- Hooks in `src/hooks/`
- API clients in `src/api/`

## Naming Conventions

- **Files:** `snake_case.py` (backend), `PascalCase.tsx` (frontend)
- **Classes:** `PascalCase`
- **Functions:** `snake_case` (Python), `camelCase` (TypeScript)
- **Constants:** `UPPER_SNAKE_CASE`

## Related Documentation

- [Development Guide](README.md)
- [Testing](testing.md)
- [Contributing](contributing.md)
- [`.repo/policy/BESTPR.md`](../../.repo/policy/BESTPR.md) - Repository-specific best practices
