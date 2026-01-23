# Platform Shared Utilities

This directory contains shared utilities, types, and configurations used across all domains and features in the application.

## Purpose

The platform layer provides generic, reusable functionality that has no business logic and is used by multiple features.

## Structure

```
platform/
├── api/           # HTTP clients and API utilities
├── utils/         # Generic utility functions
├── types/         # Shared type definitions
├── config/        # Configuration management
└── errors/        # Error handling utilities
```

## What Belongs Here

✅ **Appropriate**:
- Generic utility functions (formatting, parsing, validation)
- Shared types and interfaces
- API clients and HTTP wrappers
- Logging and monitoring utilities
- Configuration management
- Error handling utilities
- Common constants
- Framework extensions

❌ **Not Appropriate**:
- Business logic (belongs in domain layer)
- UI components (belongs in ui layer)
- Feature-specific code
- Domain models (unless truly shared)

## Rule of Three

Before adding to platform, ask:
1. Is this used by 3+ features? (Rule of three)
2. Is this generic enough to be reusable?
3. Does this have no business logic?
4. Will this be stable over time?

If all yes, add to platform. Otherwise, keep in feature.

## Import Rules

The platform layer:
- **Cannot import** from any domain or feature
- **Can only import** from external dependencies (npm packages)
- **Must be** dependency-free within the codebase

Other layers can import from platform:
- UI layer → platform ✓
- Domain layer → platform ✓
- Data layer → platform ✓

## Adding New Utilities

When adding to platform:
1. Ensure it follows the "Rule of Three"
2. Write clear documentation
3. Include unit tests
4. Keep it generic and reusable
5. Avoid business logic

## Related Documents

- **Boundaries**: `/.repo/policy/BOUNDARIES.md`
- **Architecture**: `/.repo/docs/architecture/`
