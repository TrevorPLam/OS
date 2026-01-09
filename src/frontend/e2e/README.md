# Playwright E2E Tests

Run the E2E suite against a running frontend (and backend, if needed).

```bash
npm run e2e:install
E2E_BASE_URL=http://localhost:5173 npm run e2e
```

If you are using Docker Compose, ensure the services are already running before
invoking the Playwright command.
