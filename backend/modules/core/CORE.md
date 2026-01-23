# CORE.md (Folder-Level Guide)

## Purpose of this folder

This folder (`backend/modules/core/`) contains shared platform/core utilities. This is the platform layer that provides common functionality for all other modules.

## What agents may do here

- Add shared utilities and base classes
- Create common functionality used across modules
- Provide platform-level abstractions
- Update core infrastructure (with care for breaking changes)

## What agents may NOT do

- Add business logic or domain-specific code
- Depend on other modules (core is the foundation)
- Create module-specific functionality
- Break existing core APIs without migration plan
- Add dependencies that other modules must inherit

## Required links

- Refer to higher-level policy: `.repo/policy/BOUNDARIES.md` for platform layer rules
- See `.repo/policy/BESTPR.md` for shared utility patterns
- See `backend/BACKEND.md` for backend-wide rules

## Platform Layer Rules

- Core is the foundation - it depends on nothing
- Other modules may depend on core
- Core should provide stable, well-tested abstractions
- Changes to core may affect all modules - test thoroughly
- Core should not know about business domains
