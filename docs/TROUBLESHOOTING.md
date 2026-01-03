# Troubleshooting Guide

**Purpose:** Common failure modes and "if X then Y" recovery playbooks for ConsultantPro.

**Audience:** Non-coder founder, operators, on-call engineers.

---

## Quick Navigation

- [Application Won't Start](#application-wont-start)
- [Tests Failing](#tests-failing)
- [Database Issues](#database-issues)
- [Lint/CI Failures](#lintci-failures)
- [Docker Issues](#docker-issues)
- [Frontend Issues](#frontend-issues)
- [See Also: Runbooks](#see-also-runbooks)

---

## Application Won't Start

### Error: `ValueError: DJANGO_SECRET_KEY environment variable is required`

**Symptom:** Application crashes immediately on startup.

**Evidence:** `src/config/settings.py:19-24`

**Cause:** Missing `DJANGO_SECRET_KEY` environment variable.

**Fix:**
```bash
# Generate a secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set it
export DJANGO_SECRET_KEY="<generated-key-here>"
```

---

### Error: Database connection refused

**Symptom:** `django.db.utils.OperationalError: could not connect to server`

**Evidence:** `README.md:76-81` - PostgreSQL connection required

**Cause:** PostgreSQL not running OR wrong connection parameters.

**Fix:**
1. **Check if PostgreSQL is running:**
   ```bash
   # macOS/Linux
   ps aux | grep postgres

   # Or check service status
   systemctl status postgresql  # Linux
   brew services list           # macOS
   ```

2. **Verify connection parameters:**
   ```bash
   echo $POSTGRES_HOST
   echo $POSTGRES_PORT
   echo $POSTGRES_DB
   echo $POSTGRES_USER
   ```

3. **Test connection manually:**
   ```bash
   psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB
   ```

4. **Common fixes:**
   - Start PostgreSQL: `brew services start postgresql` (macOS) or `systemctl start postgresql` (Linux)
   - Create database: `createdb consultantpro`
   - Check password is correct

---

### Error: `django.core.exceptions.ImproperlyConfigured`

**Symptom:** Various configuration errors on startup.

**Cause:** Missing or incorrect environment variables.

**Fix:**
1. Review required environment variables in `docs/OPERATIONS.md` Section 3.1
2. Verify all required vars are set: `env | grep DJANGO` and `env | grep POSTGRES`
3. Check for typos in variable names

---

## Tests Failing

### Error: `pytest: command not found`

**Cause:** Dependencies not installed.

**Fix:**
```bash
pip install -r requirements.txt
```

---

### Error: Tests fail with `sqlite3` vs `postgres` differences

**Symptom:** Tests pass locally but fail in CI, or vice versa.

**Evidence:** TODO.md:129 - "ASSESS-C3.10 Eliminate test non-determinism - Standardize tests to use Postgres (not SQLite)"

**Cause:** SQLite and PostgreSQL have different behaviors (e.g., foreign key constraints).

**Fix:**
1. **Use PostgreSQL for local tests:**
   ```bash
   # Ensure POSTGRES_* env vars are set
   pytest
   ```

2. **Check if USE_SQLITE_FOR_TESTS is set:**
   ```bash
   unset USE_SQLITE_FOR_TESTS
   ```

**Evidence:** `.github/workflows/docs.yml:85` uses `USE_SQLITE_FOR_TESTS=True` for OpenAPI generation only.

---

### Error: Migration not applied

**Symptom:** `django.db.utils.ProgrammingError: relation "..." does not exist`

**Cause:** Database migrations not run.

**Fix:**
```bash
cd src
python manage.py migrate
```

---

## Database Issues

### Error: Unapplied migrations

**Symptom:** `You have 5 unapplied migration(s). Your project may not work properly until you apply the migrations`

**Fix:**
```bash
cd src
python manage.py migrate
```

---

### Error: Migration conflicts

**Symptom:** `Conflicting migrations detected`

**Fix:**
1. **Check for multiple migration files with same number:**
   ```bash
   find src/modules -name "0001_*.py" | sort
   ```

2. **Resolve conflicts** - See Django migration documentation or:
   ```bash
   python manage.py makemigrations --merge
   ```

**Evidence:** Constitution Section 8.2 - "Migration Safety Policy"

---

## Lint/CI Failures

### Error: `make lint` fails

**Symptom:** Linting errors reported.

**Evidence:** `Makefile:34-54`, `.github/workflows/ci.yml:14-52`

**Fix by lint type:**

**1. Ruff (Python linter):**
```bash
cd src
ruff check .
# Auto-fix where possible
ruff check --fix .
```

**2. Black (Python formatter):**
```bash
cd src
black .
```

**3. Isort (Import sorting):**
```bash
cd src
isort .
```

**4. Frontend lint (ESLint/TypeScript):**
```bash
cd src/frontend
npm run lint
```

**5. Docs validation:**
```bash
make -C docs validate
```

---

### Error: OpenAPI schema drift detected

**Symptom:** CI fails with "OpenAPI drift detected"

**Evidence:** `.github/workflows/docs.yml:89-93`, `Makefile:145-146`

**Cause:** OpenAPI schema in docs is out of sync with code.

**Fix:**
```bash
make openapi
git add docs/03-reference/api/openapi.yaml
git commit -m "Update OpenAPI schema"
```

**Evidence:** `Makefile:98-106` defines `openapi` target.

---

### Error: Markdown link check failures

**Symptom:** CI fails with "Markdown link check failed"

**Evidence:** `.github/workflows/docs.yml:31-39` - lychee link checker

**Cause:** Broken internal or external links in markdown files.

**Fix:**
1. **Run link checker locally:**
   ```bash
   python scripts/check_markdown_links.py
   ```

2. **Common issues:**
   - File moved/renamed: Update link
   - Anchor doesn't exist: Fix heading or anchor reference
   - External URL down: Update or remove link

---

## Docker Issues

### Error: Docker build fails

**Symptom:** `docker compose up --build` fails.

**Evidence:** `.github/workflows/ci.yml:213-231` - CI tests docker build

**Common causes:**
1. **Missing Dockerfile:** Verify `Dockerfile` exists at repo root
2. **Invalid Dockerfile syntax:** Check for syntax errors
3. **Dependencies fail to install:** Check network connectivity

**Fix:**
1. **Check Docker is running:**
   ```bash
   docker ps
   ```

2. **Review build logs:**
   ```bash
   docker compose build
   ```

3. **Clear cache and rebuild:**
   ```bash
   docker compose build --no-cache
   ```

---

## Frontend Issues

### Error: `npm ci` fails

**Cause:** Outdated or corrupted `package-lock.json`.

**Fix:**
```bash
cd src/frontend
rm -rf node_modules package-lock.json
npm install
```

---

### Error: Frontend build fails

**Symptom:** `npm run build` fails.

**Evidence:** `.github/workflows/ci.yml:158-161`

**Common causes:**
1. **TypeScript errors:** Run `npm run typecheck`
2. **Lint errors:** Run `npm run lint`
3. **Missing env vars:** Check `VITE_*` variables

**Fix:**
```bash
cd src/frontend
npm run typecheck  # Check TypeScript errors
npm run lint       # Check linting errors
npm run build      # Rebuild
```

---

## See Also: Runbooks

For operational procedures, see:

- **Rollback Procedures:** `docs/RUNBOOKS/ROLLBACK.md` ✅ EXISTS (evidence: docs/runbooks/ROLLBACK.md)
- **Incident Response:** `docs/RUNBOOKS/RUNBOOK_incident-response.md` - Tracked in TODO: T-012
- **Deployment:** `docs/RUNBOOKS/RUNBOOK_release.md` - UNKNOWN (to be created)
- **Backup/Restore:** `docs/RUNBOOKS/RUNBOOK_backup-restore.md` - Tracked in TODO: T-012

**Runbook Index:** `docs/RUNBOOKS/README.md`

---

## Escalation

If you can't resolve an issue:

1. **Check existing issues:** Search GitHub issues for similar problems
2. **Open a new issue:** Include:
   - Error message (full stack trace)
   - Steps to reproduce
   - Environment details (OS, Python version, PostgreSQL version)
   - Relevant logs
3. **Security issues:** Follow `SECURITY.md` for responsible disclosure

---

**Last Updated:** 2025-12-30
**Evidence Status:** STATIC-ONLY verification (based on code analysis, not execution)
