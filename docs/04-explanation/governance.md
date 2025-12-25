# Governance & GitHub Settings

This document captures the GitHub settings that must be enforced for documentation and API “truth” to remain intact.

## Required branch protection settings

Configure these on the default branch (main):

- Require Code Owners review.
- Require status checks to pass before merging:
  - `docs-validate`
  - `openapi-no-drift`
  - `policy-validate`
  - `lint` / `test` (backend + frontend)

## Why these are required

- **Docs validation** prevents broken links and missing structure from reaching main.
- **OpenAPI no-drift** guarantees API changes are reflected in the committed schema.
- **Policy validation** ensures repository health files remain complete.
- **Lint/test** keeps functional regressions out of production.
