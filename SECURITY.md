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

### Content Security Policy (CSP)

The application uses Content Security Policy headers in production to prevent cross-site scripting (XSS) and other code injection attacks.

**CSP Configuration:**

CSP is configured in `src/config/settings.py` and only active when `DEBUG=False` (production mode).

**Default CSP Directives:**

- `default-src 'self'` - Only allow resources from same origin
- `script-src 'self' https://browser.sentry-cdn.com` - Scripts from same origin + Sentry
- `style-src 'self' 'unsafe-inline'` - Styles from same origin + inline (required for React)
- `img-src 'self' data: https:` - Images from same origin, data URIs, and HTTPS
- `font-src 'self' data:` - Fonts from same origin and data URIs
- `connect-src 'self' https://*.sentry.io` - XHR/WebSocket to same origin + Sentry
- `frame-ancestors 'none'` - Prevent clickjacking (no iframes)
- `base-uri 'self'` - Restrict base tag to same origin
- `form-action 'self'` - Forms can only submit to same origin
- `object-src 'none'` - Disable plugins (Flash, Java, etc.)

**Testing CSP:**

1. Build the frontend in production mode:
   ```bash
   cd src/frontend
   npm run build
   ```

2. Start the backend with DEBUG=False:
   ```bash
   export DJANGO_DEBUG=False
   cd src
   python manage.py runserver
   ```

3. Check the response headers:
   ```bash
   curl -I http://localhost:8000/api/health/
   ```

4. Look for the `Content-Security-Policy` header in the response.

**CSP Violation Reporting:**

Set the `CSP_REPORT_URI` environment variable to enable CSP violation reporting:

```bash
export CSP_REPORT_URI=https://your-csp-reporting-endpoint.com/report
```

**Customizing CSP:**

Edit the CSP directives in `src/config/settings.py` under the "Security Settings (Production)" section.

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
