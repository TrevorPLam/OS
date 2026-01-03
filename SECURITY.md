# Security Policy

Security and privacy are foundational to ConsultantPro. Please handle potential vulnerabilities responsibly.

## Reporting a Vulnerability

- **Preferred:** Use your hosting platform's private security reporting workflow (e.g., GitHub Security Advisories).
- **If private reporting is unavailable:** Contact the project maintainers directly at security@consultantpro.com and avoid public disclosure until a fix is available.

## What to Include

- A clear description of the issue and potential impact
- Steps to reproduce (proof-of-concept if possible)
- Affected versions or commits
- Any suggested fixes or mitigations

## Response Expectations

The team will triage reports as quickly as possible, prioritize based on severity, and coordinate a responsible disclosure timeline.

## Dependency Management

### Frontend Dependency Updates

All frontend dependencies use exact versions (no `^` or `~` prefixes) to ensure reproducible builds.

**To update a dependency:**

1. Check for outdated packages:
   ```bash
   cd src/frontend
   npm outdated
   ```

2. Update specific package:
   ```bash
   npm install package-name@latest --save-exact
   ```

3. For security updates:
   ```bash
   npm audit
   npm audit fix
   ```

4. Verify the build:
   ```bash
   npm run build
   npm run typecheck
   npm run lint
   ```

5. Test the application thoroughly before committing.

6. Commit both `package.json` and `package-lock.json`.

### Backend Dependency Updates

Backend dependencies should be updated with caution, following these steps:

1. Check for security vulnerabilities:
   ```bash
   safety check --file requirements.txt
   ```

2. Update dependencies in `requirements.txt` or `requirements-dev.txt`

3. Verify tests pass:
   ```bash
   make test
   ```

4. Run security checks:
   ```bash
   safety check --file requirements.txt
   bandit -r src/
   ```
