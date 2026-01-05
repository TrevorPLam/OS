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

### Webhook Rate Limiting (SEC-2)

All webhook endpoints are rate limited to prevent webhook flooding attacks.

**Default Rate Limit:**

- **100 requests per minute per IP address** for all webhook endpoints
- Applies to: Stripe, Square, DocuSign, and Twilio (SMS) webhooks
- Returns HTTP 429 (Too Many Requests) when limit exceeded

**Webhook Endpoints Protected:**

- `/api/v1/finance/stripe/webhook/` - Stripe payment webhooks
- `/api/v1/finance/square/webhook/` - Square payment webhooks  
- `/api/v1/esignature/docusign/webhook/` - DocuSign e-signature webhooks
- `/api/v1/sms/webhook/status/` - Twilio SMS status webhooks
- `/api/v1/sms/webhook/inbound/` - Twilio inbound SMS webhooks

**Configuring Rate Limits:**

Rate limits can be adjusted via the `WEBHOOK_RATE_LIMIT` environment variable:

```bash
# Default: 100 requests per minute
export WEBHOOK_RATE_LIMIT="100/m"

# Examples of other rate limits:
export WEBHOOK_RATE_LIMIT="200/m"  # 200 per minute
export WEBHOOK_RATE_LIMIT="10/s"   # 10 per second
export WEBHOOK_RATE_LIMIT="1000/h" # 1000 per hour
```

**Per-endpoint Overrides (optional):**

```bash
export STRIPE_WEBHOOK_RATE_LIMIT="150/m"
export SQUARE_WEBHOOK_RATE_LIMIT="150/m"
export DOCUSIGN_WEBHOOK_RATE_LIMIT="150/m"
export TWILIO_STATUS_WEBHOOK_RATE_LIMIT="150/m"
export TWILIO_INBOUND_WEBHOOK_RATE_LIMIT="150/m"
```

**Monitoring Rate Limit Violations:**

Rate limit violations are logged and can be monitored through application logs:

```
WARNING: Rate limit exceeded for webhook endpoint from IP 192.168.1.1
```

**Legitimate Traffic Considerations:**

The default rate limit of 100 requests/minute per IP should accommodate legitimate webhook traffic from providers. If you experience legitimate traffic being blocked:

1. Check your webhook provider's retry behavior
2. Verify no retry storms are occurring
3. Adjust `WEBHOOK_RATE_LIMIT` if needed for your volume

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

By default, CSP reports are accepted at:

```
/api/security/csp-report/
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
