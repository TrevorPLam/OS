# TESTS.md (Folder-Level Guide)

## Purpose of this folder

This folder (`tests/`) contains cross-cutting and integration tests shared across modules. Module-specific tests may also exist within module directories.

## What agents may do here

- Add new test files for integration scenarios
- Create test utilities and fixtures
- Add cross-module integration tests
- Update existing tests when code changes
- Add performance tests (marked with `@pytest.mark.performance`)

## What agents may NOT do

- Add production code (tests only)
- Break existing test patterns without justification
- Skip tests for new features
- Remove tests without replacement
- Create tests that depend on external services without mocking

## Required links

- Refer to higher-level policy: `.repo/policy/PRINCIPLES.md` (Principle 6: Evidence Over Vibes)
- See `.repo/policy/QUALITY_GATES.md` for test requirements
- See `.repo/policy/BESTPR.md` for testing practices
- See `pytest.ini` for test configuration

## Testing Standards

- All new features require tests
- Tests must be deterministic and fast
- Integration tests should use test database
- Performance tests should be marked appropriately
- Test coverage should not regress (see quality gates)
