# Runbook

## Local verification

Run the same checks as CI:
- `make ci`

## Common issues

- If `make setup` fails, ensure Python 3.11 and Node 20 are available.
- If backend tests fail locally, confirm database settings in `.env`.
- If frontend tests fail, ensure dependencies are installed (`make -C frontend setup`).
