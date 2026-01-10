# Playwright E2E Tests

Run the E2E suite against a running frontend (and backend, if needed).

```bash
npm run e2e:install
E2E_BASE_URL=http://localhost:5173 npm run e2e
```

If you are using Docker Compose, ensure the services are already running before
invoking the Playwright command.

## Environment variables

- `E2E_API_URL` (default: `http://localhost:8000/api/v1`)
- `E2E_SEED_HEADER` (default: `X-E2E-Seed`)
- `E2E_SEED_VALUE` (default: `local-e2e-token`)

The core workflow tests call `/api/v1/auth/provision-firm/`, which is only
available when `DEBUG=True`, `E2E_PROVISION_TOKEN` is set on the backend, and
the seed header/value match that token.
