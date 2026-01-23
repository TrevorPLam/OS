# Contributing

## Workflow

- Create a branch for your change.
- Keep changes focused and minimal.
- Run the verification suite before opening a PR.

## Golden commands

From repo root:
- `make setup`
- `make lint`
- `make test`
- `make verify`
- `make ci` (alias of `make verify`)

## Backend tooling

- Lint: ruff (`make -C backend lint`)
- Format check: black (`make -C backend lint`)
- Typecheck: mypy (`make -C backend typecheck`)
- Tests: pytest (`make -C backend test`)

## Frontend tooling

- Lint: `npm run lint` via `make -C frontend lint`
- Typecheck: `npm run typecheck`
- Tests: `npm run test` via `make -C frontend test`
- E2E: `npm run e2e` via `make -C frontend e2e`
