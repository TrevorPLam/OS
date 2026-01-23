# AI Contribution Guide

## Golden commands

Run these from repo root:
- `make setup`
- `make lint`
- `make test`
- `make verify`
- `make ci` (alias of `make verify`)

## Boundaries

- Do not refactor unrelated code.
- Do not change public APIs without updating docs and tests.
- Keep changes minimal and focused.

## Tests

- Add or update tests for behavioral changes.
- Ensure `make ci` passes before submitting.
