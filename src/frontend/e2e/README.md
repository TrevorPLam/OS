# Playwright E2E Tests

Run the E2E suite against a running frontend (and backend, if needed).

```bash
E2E_BASE_URL=http://localhost:5173 npm run e2e:install
E2E_BASE_URL=http://localhost:5173 npm run e2e
```

If you are using Docker Compose, ensure the services are already running before
invoking the Playwright command.

## CI expectations

- Set `E2E_BASE_URL` explicitly in CI to avoid running against the wrong target.
- Use `E2E_CI=1` to force CI-mode behavior when needed.
- To skip browser downloads (for cached environments), set `E2E_SKIP_BROWSER_INSTALL=1`.
