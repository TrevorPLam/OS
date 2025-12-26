# Environment Variables Reference

Complete reference for all environment variables used in ConsultantPro.

---

## Table of Contents

1. [Django Core Settings](#django-core-settings)
2. [Database Configuration](#database-configuration)
3. [Security & Authentication](#security--authentication)
4. [CORS Settings](#cors-settings)
5. [AWS S3 Configuration](#aws-s3-configuration)
6. [Stripe Payment Processing](#stripe-payment-processing)
7. [Error Tracking (Sentry)](#error-tracking-sentry)
8. [Encryption & KMS](#encryption--kms)
9. [Optional/Advanced Settings](#optionaladvanced-settings)

---

## Django Core Settings

### `DJANGO_SECRET_KEY`
**Required:** Yes (for production)  
**Default:** `django-insecure-CHANGE-THIS-IN-PRODUCTION-xk7m9n8b5v4c3x2z1`  
**Purpose:** Secret key for cryptographic signing  

**Development:**
```bash
DJANGO_SECRET_KEY="dev-secret-key-for-local-testing"
```

**Production:**
```bash
# Generate a secure random key (50+ characters)
DJANGO_SECRET_KEY="your-production-secret-key-keep-this-secure"
```

**⚠️ Security:** NEVER commit production keys to version control.

---

### `DJANGO_DEBUG`
**Required:** No  
**Default:** `True`  
**Values:** `True` | `False`  
**Purpose:** Enable/disable Django debug mode  

**Development:**
```bash
DJANGO_DEBUG=True
```

**Production:**
```bash
DJANGO_DEBUG=False
```

**⚠️ Security:** MUST be `False` in production. Debug mode exposes sensitive information.

---

### `DJANGO_ALLOWED_HOSTS`
**Required:** Yes (for production)  
**Default:** `localhost,127.0.0.1`  
**Purpose:** Allowed hosts for HTTP Host header validation  

**Development:**
```bash
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

**Production:**
```bash
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
```

**Notes:** 
- Comma-separated list of hostnames/IPs
- No spaces between entries
- Include all domains and subdomains

---

## Database Configuration

### `POSTGRES_DB`
**Required:** Yes  
**Default:** `consultantpro`  
**Purpose:** PostgreSQL database name  

```bash
POSTGRES_DB=consultantpro
```

---

### `POSTGRES_USER`
**Required:** Yes  
**Default:** `postgres`  
**Purpose:** PostgreSQL username  

```bash
POSTGRES_USER=postgres
```

**Production:** Create a dedicated user with limited privileges.

---

### `POSTGRES_PASSWORD`
**Required:** Yes  
**Default:** `postgres`  
**Purpose:** PostgreSQL password  

```bash
POSTGRES_PASSWORD=your-secure-password
```

**⚠️ Security:** Use strong passwords in production. Rotate regularly.

---

### `POSTGRES_HOST`
**Required:** Yes  
**Default:** `db` (for Docker) or `localhost`  
**Purpose:** PostgreSQL host address  

**Docker:**
```bash
POSTGRES_HOST=db
```

**Local Development:**
```bash
POSTGRES_HOST=localhost
```

**Production:**
```bash
POSTGRES_HOST=your-db-hostname.rds.amazonaws.com
```

---

### `POSTGRES_PORT`
**Required:** No  
**Default:** `5432`  
**Purpose:** PostgreSQL port number  

```bash
POSTGRES_PORT=5432
```

---

### `USE_SQLITE_FOR_TESTS`
**Required:** No  
**Default:** Not set  
**Purpose:** Use SQLite for testing (faster test runs)  

```bash
USE_SQLITE_FOR_TESTS=True
```

**Notes:** Only for testing. NOT for production.

---

## Security & Authentication

### JWT Token Settings

JWT tokens are configured in `settings.py` with the following defaults:

- **Access Token Lifetime:** 1 hour
- **Refresh Token Lifetime:** 7 days
- **Algorithm:** HS256
- **Header Type:** Bearer

These are not configurable via environment variables but can be modified in `config/settings.py` if needed.

---

## CORS Settings

### `CORS_ALLOWED_ORIGINS`
**Required:** Yes (if using frontend)  
**Default:** `http://localhost:3000,http://127.0.0.1:3000`  
**Purpose:** Allowed origins for CORS requests  

**Development:**
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Production:**
```bash
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**Notes:**
- Comma-separated list of full URLs (include protocol)
- No spaces between entries
- Include all frontend origins

---

## AWS S3 Configuration

Used for document storage. Optional for development, required for production.

### `AWS_ACCESS_KEY_ID`
**Required:** No (optional for dev)  
**Default:** Empty string  
**Purpose:** AWS access key for S3 access  

```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
```

---

### `AWS_SECRET_ACCESS_KEY`
**Required:** No (optional for dev)  
**Default:** Empty string  
**Purpose:** AWS secret key for S3 access  

```bash
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**⚠️ Security:** Never commit AWS credentials. Use IAM roles in production.

---

### `AWS_STORAGE_BUCKET_NAME`
**Required:** No (optional for dev)  
**Default:** Empty string  
**Purpose:** S3 bucket name for document storage  

```bash
AWS_STORAGE_BUCKET_NAME=consultantpro-documents-prod
```

---

### `AWS_S3_REGION_NAME`
**Required:** No  
**Default:** `us-east-1`  
**Purpose:** AWS region for S3 bucket  

```bash
AWS_S3_REGION_NAME=us-west-2
```

---

## Stripe Payment Processing

Used for billing and payments. Optional for development, required for production billing features.

### `STRIPE_SECRET_KEY`
**Required:** No (optional for dev)  
**Default:** Empty string  
**Purpose:** Stripe secret API key  

**Development (Test Mode):**
```bash
STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Production (Live Mode):**
```bash
STRIPE_SECRET_KEY=[REDACTED]
```

**⚠️ Security:** Never commit live keys. Rotate if exposed.

---

### `STRIPE_PUBLISHABLE_KEY`
**Required:** No (optional for dev)  
**Default:** Empty string  
**Purpose:** Stripe publishable API key (frontend)  

**Development:**
```bash
STRIPE_PUBLISHABLE_KEY="pk_test_YOUR_TEST_KEY_HERE"
```

**Production:**
```bash
STRIPE_PUBLISHABLE_KEY="pk_live_YOUR_LIVE_KEY_HERE"
```

---

### `STRIPE_WEBHOOK_SECRET`
**Required:** No (for webhooks)  
**Default:** Empty string  
**Purpose:** Stripe webhook signing secret  

```bash
STRIPE_WEBHOOK_SECRET="whsec_YOUR_WEBHOOK_SECRET_HERE"
```

**Setup:** Get this from Stripe Dashboard → Webhooks → Add endpoint

**Webhook URL:** `https://yourdomain.com/api/webhooks/stripe/`

**Required Events:**
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `charge.refunded`
- `charge.dispute.created`
- `charge.dispute.closed`

---

## Error Tracking (Sentry)

Optional but highly recommended for production.

### `SENTRY_DSN`
**Required:** No (optional)  
**Default:** Not set  
**Purpose:** Sentry Data Source Name for error tracking  

```bash
SENTRY_DSN=https://abc123@o123456.ingest.sentry.io/7890123
```

**Get DSN:** Create project at https://sentry.io/

---

### `SENTRY_ENVIRONMENT`
**Required:** No  
**Default:** `production`  
**Purpose:** Environment identifier in Sentry  

```bash
SENTRY_ENVIRONMENT=production
```

**Values:** `development`, `staging`, `production`

---

### `SENTRY_TRACES_SAMPLE_RATE`
**Required:** No  
**Default:** `0.1` (10%)  
**Purpose:** Percentage of transactions to trace  

```bash
SENTRY_TRACES_SAMPLE_RATE=0.1
```

**Notes:** 
- `0.0` = disabled
- `1.0` = 100% (expensive, use sparingly)
- `0.1` = 10% (recommended for production)

---

### `SENTRY_PROFILES_SAMPLE_RATE`
**Required:** No  
**Default:** `0.1` (10%)  
**Purpose:** Percentage of transactions to profile  

```bash
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

---

### `SENTRY_DEBUG`
**Required:** No  
**Default:** Not set  
**Purpose:** Enable Sentry debug logging  

```bash
SENTRY_DEBUG=False
```

---

### `GIT_COMMIT_SHA`
**Required:** No  
**Default:** Not set  
**Purpose:** Git commit SHA for release tracking  

```bash
GIT_COMMIT_SHA=$(git rev-parse HEAD)
```

**Notes:** Automatically set in CI/CD pipeline.

---

## Encryption & KMS

### `DEFAULT_FIRM_KMS_KEY_ID`
**Required:** No  
**Default:** `local-default-key`  
**Purpose:** Default KMS key ID for encryption  

```bash
DEFAULT_FIRM_KMS_KEY_ID=local-default-key
```

**Production:** Set to actual KMS key ID when using AWS KMS.

---

### `KMS_BACKEND`
**Required:** No  
**Default:** `local`  
**Purpose:** KMS backend implementation  

```bash
KMS_BACKEND=local
```

**Values:**
- `local` - Local encryption (development only)
- `aws` - AWS KMS (production)

**Notes:** E2EE requires AWS KMS infrastructure setup. See [E2EE Implementation Plan](../../docs/tier0/E2EE_IMPLEMENTATION_PLAN.md).

---

## Optional/Advanced Settings

### Rate Limiting

Configured in `settings.py`:

- **Burst:** 100 requests/minute
- **Sustained:** 1000 requests/hour
- **Anonymous:** 20 requests/hour
- **Payment:** 10 requests/minute
- **Upload:** 30 requests/hour

Not configurable via environment variables.

---

### API Guardrails

Configured in `settings.py`:

- **Max Page Size:** 200 items
- **Search Max Length:** 100 characters
- **Query Timeout:** 3000ms (3 seconds)

Not configurable via environment variables.

---

## Environment Setup Examples

### Development (Local)

```bash
# Django
DJANGO_SECRET_KEY="dev-secret-key"
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=consultantpro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

### Docker Development

```bash
# Django
DJANGO_SECRET_KEY="dev-secret-key"
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (using Docker service name)
POSTGRES_DB=consultantpro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

### Staging

```bash
# Django
DJANGO_SECRET_KEY="staging-secret-key-keep-secure"
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=staging.yourdomain.com

# Database
POSTGRES_DB=consultantpro_staging
POSTGRES_USER=consultantpro_staging
POSTGRES_PASSWORD=secure-staging-password
POSTGRES_HOST=staging-db.yourdomain.com
POSTGRES_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=https://staging.yourdomain.com

# Sentry
SENTRY_DSN=https://abc123@o123456.ingest.sentry.io/7890123
SENTRY_ENVIRONMENT=staging
```

---

### Production

```bash
# Django
DJANGO_SECRET_KEY="production-secret-key-minimum-50-characters-keep-very-secure"
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# Database
POSTGRES_DB=consultantpro
POSTGRES_USER=consultantpro_prod
POSTGRES_PASSWORD=very-secure-production-password
POSTGRES_HOST=prod-db.abc123.us-east-1.rds.amazonaws.com
POSTGRES_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# AWS S3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_STORAGE_BUCKET_NAME=consultantpro-documents-prod
AWS_S3_REGION_NAME=us-east-1

# Stripe
STRIPE_SECRET_KEY=[REDACTED]
STRIPE_PUBLISHABLE_KEY=pk_live_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXXXXXXX

# Sentry
SENTRY_DSN=https://abc123@o123456.ingest.sentry.io/7890123
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
GIT_COMMIT_SHA=$(git rev-parse HEAD)
```

---

## Security Best Practices

1. **Never commit secrets to version control**
   - Use `.env` files locally
   - Use secrets managers in production (AWS Secrets Manager, HashiCorp Vault, etc.)

2. **Rotate secrets regularly**
   - Database passwords: Every 90 days
   - API keys: When team members leave
   - Django secret key: Annually

3. **Use strong passwords**
   - Minimum 20 characters
   - Mix of letters, numbers, symbols
   - Generate with password manager

4. **Limit access**
   - Principle of least privilege
   - Use IAM roles instead of access keys when possible
   - Different credentials for different environments

5. **Monitor and audit**
   - Enable Sentry error tracking
   - Review audit logs regularly
   - Set up alerts for security events

---

## Troubleshooting

### "Django settings module not found"
**Solution:** Ensure you're in the `src/` directory or set `DJANGO_SETTINGS_MODULE`:
```bash
export DJANGO_SETTINGS_MODULE=config.settings
```

### "Database connection refused"
**Checklist:**
1. PostgreSQL is running
2. `POSTGRES_HOST` is correct
3. `POSTGRES_PORT` is correct
4. Database exists: `psql -l | grep consultantpro`
5. User has access: Test connection with `psql -U $POSTGRES_USER -h $POSTGRES_HOST -d $POSTGRES_DB`

### "CORS errors in browser"
**Checklist:**
1. `CORS_ALLOWED_ORIGINS` includes frontend URL
2. Include protocol (http/https)
3. No trailing slashes
4. No spaces between entries

### "Stripe webhook signature invalid"
**Checklist:**
1. `STRIPE_WEBHOOK_SECRET` matches Stripe Dashboard
2. Webhook endpoint URL is correct
3. Using correct environment (test/live)

---

## Related Documentation

- [Getting Started Tutorial](../../docs/01-tutorials/getting-started.md) - Setup guide
- [Production Deployment](production-deployment.md) - Production configuration
- [Sentry Setup](sentry-setup.md) - Error tracking setup
- [API Usage Guide](../03-reference/api-usage.md) - API documentation

---

**Last Updated:** December 26, 2025
