# Testing Guide

Testing strategies and practices for UBOS.

## Testing Philosophy

- **Test Everything** - New features require tests
- **Evidence Over Vibes** - Show proof, not assumptions
- **Deterministic** - Tests must be repeatable
- **Fast** - Unit tests should be quick

## Test Structure

### Backend Tests
- Location: `backend/modules/*/tests/` and `tests/`
- Framework: pytest
- Run: `make test` or `pytest`

### Frontend Tests
- Unit tests: `frontend/tests/` (Vitest)
- E2E tests: `frontend/e2e/` (Playwright)
- Run: `make -C frontend test` or `make -C frontend e2e`

### Integration Tests
- Location: `tests/`
- Cross-module integration tests
- Shared test utilities

## Test Types

### Unit Tests
- Test individual functions/classes
- Fast, isolated
- Mock external dependencies

### Integration Tests
- Test module interactions
- Use test database
- Test API endpoints

### E2E Tests
- Test full user workflows
- Use Playwright
- Test critical paths

## Running Tests

```bash
# All tests
make test

# Backend only
pytest

# Frontend unit tests
make -C frontend test

# Frontend E2E tests
make -C frontend e2e
```

## Test Coverage

- Aim for high coverage on critical paths
- Security and money flows require comprehensive tests
- Use coverage reports to identify gaps

## Best Practices

1. **Write Tests First** - TDD when possible
2. **Test Edge Cases** - Don't just test happy paths
3. **Keep Tests Fast** - Unit tests should be quick
4. **Use Fixtures** - Reuse test data
5. **Mock External Services** - Don't depend on external APIs

## Related Documentation

- [Development Guide](README.md)
- [Code Standards](standards.md)
- [Local Setup](local-setup.md)
