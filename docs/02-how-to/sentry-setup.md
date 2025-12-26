# Sentry Error Tracking Setup Guide

This guide explains how to set up Sentry error tracking for ConsultantPro.

## Overview

Sentry provides:
- **Error Tracking**: Automatic capture of exceptions with stack traces
- **Performance Monitoring**: Transaction and query performance tracking
- **User Context**: Associate errors with specific users and firms (multi-tenant)
- **Alerting**: Real-time notifications when errors occur
- **Release Tracking**: Track errors by deployment version

---

## Quick Start

### 1. Create a Sentry Account

1. Go to [https://sentry.io/](https://sentry.io/)
2. Create an account or sign in
3. Create a new project for Django
4. Copy your **DSN** (Data Source Name)

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Sentry Error Tracking (required for production)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

### 3. Deploy and Verify

Deploy your application and trigger a test error:

```python
# In Django shell or view
raise Exception("Test Sentry integration")
```

Check your Sentry dashboard to verify the error was captured.

---

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SENTRY_DSN` | Sentry Data Source Name | None | Yes (for Sentry to work) |
| `SENTRY_ENVIRONMENT` | Environment name | `production` | No |
| `SENTRY_TRACES_SAMPLE_RATE` | Performance monitoring sample rate (0.0-1.0) | `0.1` (10%) | No |
| `SENTRY_PROFILES_SAMPLE_RATE` | Profiling sample rate (0.0-1.0) | `0.1` (10%) | No |
| `SENTRY_DEBUG` | Enable Sentry debug logging | `False` | No |
| `GIT_COMMIT_SHA` | Git commit SHA for release tracking | None | No |

### Sample Rates

**Traces Sample Rate** (`SENTRY_TRACES_SAMPLE_RATE`):
- Controls what percentage of transactions are sent to Sentry
- `0.1` = 10% (recommended for production)
- `1.0` = 100% (only for low-traffic staging environments)
- Higher rates = more data but higher costs

**Profiles Sample Rate** (`SENTRY_PROFILES_SAMPLE_RATE`):
- Controls what percentage of *sampled transactions* get profiling data
- This is applied *after* traces sampling
- `0.1` = 10% of sampled transactions (recommended)

**Example**: With `TRACES_SAMPLE_RATE=0.1` and `PROFILES_SAMPLE_RATE=0.1`:
- 10% of transactions are sampled for performance monitoring
- 10% of those (1% total) get detailed profiling data

---

## Multi-Tenant Context

ConsultantPro automatically adds firm and user context to all Sentry errors via `SentryContextMiddleware`.

### Automatic Context

Every error in Sentry includes:
- **User Context**: User ID, email, username
- **Firm Context**: Firm ID and name (critical for multi-tenant debugging)
- **Request Metadata**: Path, method, headers (filtered for security)

### Viewing Context in Sentry

1. Open an error in Sentry
2. Navigate to the **Context** tab
3. Look for:
   - `user.id`, `user.email`
   - `firm.id`, `firm.name` (in tags)
   - Custom context fields

### Filtering by Firm

In Sentry dashboard:
- Filter by firm: `firm_id:123` or `firm_name:"Acme Consulting"`
- Filter by user: `user.id:456` or `user.email:"user@example.com"`

---

## Usage in Code

### Automatic Error Capture

Exceptions are automatically captured:

```python
# Django view
def my_view(request):
    # This exception will be automatically captured by Sentry
    raise ValueError("Something went wrong!")
```

### Manual Error Capture

For more control, use the Sentry utilities:

```python
from config.sentry import capture_exception_with_context, capture_message_with_context

try:
    risky_operation()
except Exception as e:
    # Capture exception with additional context
    capture_exception_with_context(
        e,
        context={
            "operation": "risky_operation",
            "params": {"client_id": 123, "amount": 1000},
        },
        level="error",
        module="finance",
        action="invoice_creation",
    )
    raise  # Re-raise to let Django handle it

# Capture non-exception events
capture_message_with_context(
    "Payment failed after 3 retries",
    level="warning",
    context={"client_id": 123, "invoice_id": 456},
    payment_method="stripe",
)
```

### Set Context Manually

```python
from config.sentry import set_user_context, set_firm_context

# Set user context (usually done by middleware)
set_user_context(
    user_id=user.id,
    email=user.email,
    username=user.username,
)

# Set firm context (usually done by middleware)
set_firm_context(
    firm_id=firm.id,
    firm_name=firm.name,
)
```

---

## Performance Monitoring

Sentry automatically tracks:
- HTTP request/response times
- Database query performance
- External API calls (Stripe, AWS S3)
- Django middleware execution time

### View Performance Data

1. Go to Sentry dashboard
2. Navigate to **Performance** section
3. View:
   - Slowest transactions
   - Database query performance
   - External service latency

### Troubleshooting Slow Endpoints

1. Filter by transaction: `/api/invoices/` or `/api/clients/`
2. Click on slow transaction
3. View span breakdown to see what's slow:
   - Database queries
   - External API calls
   - Middleware overhead

---

## Production Best Practices

### 1. Set Environment Correctly

```bash
# Production
SENTRY_ENVIRONMENT=production

# Staging
SENTRY_ENVIRONMENT=staging

# Development
SENTRY_ENVIRONMENT=development
```

This allows filtering errors by environment in Sentry.

### 2. Track Releases

Set `GIT_COMMIT_SHA` to track which version introduced an error:

```bash
# In deployment script
export GIT_COMMIT_SHA=$(git rev-parse HEAD)
```

In Sentry, you'll see which release introduced each error.

### 3. Set Up Alerts

In Sentry dashboard:
1. Go to **Alerts** > **Create Alert**
2. Create alert for:
   - New issues (first occurrence)
   - Regression issues (previously resolved)
   - High error rate (>10 errors in 5 minutes)

### 4. Filter Sensitive Data

The Sentry integration automatically filters:
- Authorization headers
- Cookie headers
- Other sensitive request data

See `src/config/sentry.py` → `before_send_filter()` for customization.

### 5. Ignore Expected Errors

To ignore specific errors (e.g., portal users accessing admin endpoints):

Edit `src/config/sentry.py` → `before_send_filter()`:

```python
def before_send_filter(event, hint):
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        # Don't send expected permission errors
        if isinstance(exc_value, PermissionError):
            return None  # Drop event
    return event
```

---

## Disabling Sentry

### In Development

Simply don't set `SENTRY_DSN`:

```bash
# .env (development)
# SENTRY_DSN=  # Leave empty or comment out
```

Sentry initialization will be skipped automatically.

### In Production

To temporarily disable Sentry in production:

```bash
# Remove or comment out SENTRY_DSN
# SENTRY_DSN=https://...
```

**Warning**: Only disable in emergency. Sentry is critical for production monitoring.

---

## Troubleshooting

### Sentry Not Capturing Errors

1. **Check DSN**: Ensure `SENTRY_DSN` is set correctly
2. **Check Logs**: Look for "Sentry initialized" message on startup
3. **Test Manually**:
   ```python
   from django.core.management import execute_from_command_line
   execute_from_command_line(['manage.py', 'shell'])
   >>> raise Exception("Test Sentry")
   ```
4. **Check Sentry Dashboard**: Verify project settings

### High Sentry Costs

1. **Reduce Sample Rates**:
   ```bash
   SENTRY_TRACES_SAMPLE_RATE=0.05  # 5% instead of 10%
   SENTRY_PROFILES_SAMPLE_RATE=0.05
   ```

2. **Filter Out Noise**:
   - Add more filters in `before_send_filter()`
   - Ignore health check endpoints
   - Ignore specific error types

3. **Review Quotas**: Check Sentry billing dashboard

### Performance Impact

Sentry has minimal performance impact:
- Error capture: ~1-2ms overhead
- Performance monitoring: ~1-5ms overhead (sampled)

If needed, reduce sample rates further.

---

## Security Considerations

### Data Sent to Sentry

Sentry captures:
- ✅ Stack traces (safe)
- ✅ Request path and method (safe)
- ✅ User ID and firm ID (safe, needed for debugging)
- ❌ Authorization tokens (filtered automatically)
- ❌ Passwords (filtered automatically)
- ❌ Customer content (not sent)

### PII Handling

Set `send_default_pii=False` (already configured) to ensure:
- No request bodies captured by default
- No query parameters captured by default
- No personally identifiable information sent

### Firm Data Isolation

- Sentry sees firm **IDs** but not firm **data**
- Errors are tagged with `firm_id` for filtering
- No customer documents or content sent to Sentry

---

## Additional Resources

- [Sentry Django Documentation](https://docs.sentry.io/platforms/python/guides/django/)
- [Performance Monitoring Guide](https://docs.sentry.io/product/performance/)
- [Alert Configuration](https://docs.sentry.io/product/alerts/)
- [Release Tracking](https://docs.sentry.io/product/releases/)

---

## Support

For issues with Sentry integration:
1. Check this guide
2. Review `src/config/sentry.py` comments
3. Consult [Sentry documentation](https://docs.sentry.io/)
4. Contact platform team

---

**Last Updated**: 2025-12-26
