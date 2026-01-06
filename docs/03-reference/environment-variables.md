# Environment Variables Reference

Document Type: Reference
Last Updated: 2026-01-06

This document lists all environment variables used by ConsultantPro, their purpose, and configuration requirements.

## Core Django Settings

### DJANGO_SECRET_KEY
- **Required**: Yes (production)
- **Type**: String
- **Purpose**: Cryptographic signing key for Django sessions, CSRF tokens, and password reset tokens
- **Production Requirements**: 
  - Must be at least 50 characters
  - Must be randomly generated and kept secret
  - Never commit to version control
- **Example**: `DJANGO_SECRET_KEY=your-very-long-random-secret-key-here`

### DJANGO_DEBUG
- **Required**: No
- **Type**: Boolean (`True`/`False`)
- **Default**: `False`
- **Purpose**: Enables Django debug mode with detailed error pages
- **Production Requirements**: Must be `False` in production
- **Example**: `DJANGO_DEBUG=False`

### DJANGO_ALLOWED_HOSTS
- **Required**: Yes (production)
- **Type**: Comma-separated list of hostnames
- **Purpose**: Hostnames that Django will serve
- **Production Requirements**: Must include all production domain names
- **Example**: `DJANGO_ALLOWED_HOSTS=consultantpro.com,www.consultantpro.com`

## Database Configuration

### POSTGRES_DB
- **Required**: Yes
- **Type**: String
- **Purpose**: PostgreSQL database name
- **Example**: `POSTGRES_DB=consultantpro`

### POSTGRES_USER
- **Required**: Yes
- **Type**: String
- **Purpose**: PostgreSQL database username
- **Example**: `POSTGRES_USER=postgres`

### POSTGRES_PASSWORD
- **Required**: Yes
- **Type**: String
- **Purpose**: PostgreSQL database password
- **Production Requirements**: Strong password, never commit to version control
- **Example**: `POSTGRES_PASSWORD=secure-random-password`

### POSTGRES_HOST
- **Required**: Yes
- **Type**: String (hostname or IP)
- **Purpose**: PostgreSQL server hostname
- **Example**: `POSTGRES_HOST=db` (Docker Compose) or `POSTGRES_HOST=localhost` (local dev)

### POSTGRES_PORT
- **Required**: No
- **Type**: Integer
- **Default**: `5432`
- **Purpose**: PostgreSQL server port
- **Example**: `POSTGRES_PORT=5432`

## CORS Configuration

### CORS_ALLOWED_ORIGINS
- **Required**: Yes (if frontend is separate domain)
- **Type**: Comma-separated list of URLs
- **Purpose**: Origins allowed to make cross-origin requests to the API
- **Production Requirements**: Only include trusted frontend domains
- **Example**: `CORS_ALLOWED_ORIGINS=https://app.consultantpro.com,https://portal.consultantpro.com`

## AWS S3 Storage

### AWS_ACCESS_KEY_ID
- **Required**: Yes (if using S3 for document storage)
- **Type**: String
- **Purpose**: AWS IAM access key for S3 operations
- **Production Requirements**: Use IAM role if running in AWS, otherwise use restricted IAM user
- **Example**: `AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE`

### AWS_SECRET_ACCESS_KEY
- **Required**: Yes (if using S3)
- **Type**: String
- **Purpose**: AWS IAM secret key for S3 operations
- **Production Requirements**: Never commit to version control
- **Example**: `AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

### AWS_STORAGE_BUCKET_NAME
- **Required**: Yes (if using S3)
- **Type**: String
- **Purpose**: S3 bucket name for document storage
- **Example**: `AWS_STORAGE_BUCKET_NAME=consultantpro-documents-prod`

### AWS_S3_REGION_NAME
- **Required**: Yes (if using S3)
- **Type**: String (AWS region code)
- **Purpose**: AWS region where S3 bucket is located
- **Example**: `AWS_S3_REGION_NAME=us-east-1`

## Payment Processing (Stripe)

### STRIPE_SECRET_KEY
- **Required**: Yes (if using Stripe)
- **Type**: String
- **Purpose**: Stripe API secret key for payment processing
- **Production Requirements**: Use live key in production, never commit to version control
- **Example**: `STRIPE_SECRET_KEY=sk_live_...` or `sk_test_...`

### STRIPE_PUBLISHABLE_KEY
- **Required**: Yes (if using Stripe)
- **Type**: String
- **Purpose**: Stripe publishable key for frontend payment forms
- **Example**: `STRIPE_PUBLISHABLE_KEY=pk_live_...` or `pk_test_...`

### STRIPE_WEBHOOK_SECRET
- **Required**: Yes (if using Stripe webhooks)
- **Type**: String
- **Purpose**: Secret for verifying Stripe webhook signatures
- **Production Requirements**: Required for webhook signature verification (SEC-6)
- **Example**: `STRIPE_WEBHOOK_SECRET=whsec_...`

## DocuSign E-Signature Integration

### DOCUSIGN_CLIENT_ID
- **Required**: Yes (if using DocuSign)
- **Type**: String
- **Purpose**: DocuSign OAuth client ID
- **Example**: `DOCUSIGN_CLIENT_ID=abc123-def456-...`

### DOCUSIGN_CLIENT_SECRET
- **Required**: Yes (if using DocuSign)
- **Type**: String
- **Purpose**: DocuSign OAuth client secret
- **Production Requirements**: Never commit to version control
- **Example**: `DOCUSIGN_CLIENT_SECRET=your-client-secret`

### DOCUSIGN_REDIRECT_URI
- **Required**: Yes (if using DocuSign)
- **Type**: String (URL)
- **Purpose**: OAuth callback URL after DocuSign authorization
- **Example**: `DOCUSIGN_REDIRECT_URI=https://api.consultantpro.com/api/v1/esignature/docusign/callback/`

### DOCUSIGN_WEBHOOK_SECRET
- **Required**: Yes (production, if using DocuSign webhooks)
- **Type**: String
- **Purpose**: Secret for verifying DocuSign webhook signatures
- **Production Requirements**: Required for webhook signature verification (SEC-6)
- **Example**: `DOCUSIGN_WEBHOOK_SECRET=your-webhook-secret`

### DOCUSIGN_ENVIRONMENT
- **Required**: Yes (if using DocuSign)
- **Type**: String (`sandbox` or `production`)
- **Purpose**: DocuSign API environment
- **Example**: `DOCUSIGN_ENVIRONMENT=production`

## Twilio SMS Integration

### TWILIO_ACCOUNT_SID
- **Required**: Yes (if using Twilio)
- **Type**: String
- **Purpose**: Twilio account identifier
- **Example**: `TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### TWILIO_AUTH_TOKEN
- **Required**: Yes (if using Twilio)
- **Type**: String
- **Purpose**: Twilio authentication token
- **Production Requirements**: Required for webhook signature verification (SEC-6), never commit to version control
- **Example**: `TWILIO_AUTH_TOKEN=your-auth-token`

## Sentry Error Tracking

### SENTRY_DSN
- **Required**: No (recommended for production)
- **Type**: String (URL)
- **Purpose**: Sentry Data Source Name for error reporting
- **Example**: `SENTRY_DSN=https://public@sentry.io/project-id`

### SENTRY_ENVIRONMENT
- **Required**: No
- **Type**: String
- **Default**: `production`
- **Purpose**: Environment name for Sentry error grouping
- **Example**: `SENTRY_ENVIRONMENT=production`

### SENTRY_TRACES_SAMPLE_RATE
- **Required**: No
- **Type**: Float (0.0 to 1.0)
- **Default**: `0.1`
- **Purpose**: Percentage of transactions to send to Sentry for performance monitoring
- **Example**: `SENTRY_TRACES_SAMPLE_RATE=0.1`

### SENTRY_PROFILES_SAMPLE_RATE
- **Required**: No
- **Type**: Float (0.0 to 1.0)
- **Default**: `0.1`
- **Purpose**: Percentage of transactions to profile for performance insights
- **Example**: `SENTRY_PROFILES_SAMPLE_RATE=0.1`

### SENTRY_DEBUG
- **Required**: No
- **Type**: Boolean
- **Default**: `False`
- **Purpose**: Enable Sentry SDK debug logging
- **Example**: `SENTRY_DEBUG=False`

### GIT_COMMIT_SHA
- **Required**: No (recommended for production)
- **Type**: String
- **Purpose**: Git commit SHA for release tracking in Sentry
- **Example**: `GIT_COMMIT_SHA=abc123def456`

## Security Configuration

### WEBHOOK_RATE_LIMIT
- **Required**: No
- **Type**: String (rate limit expression)
- **Default**: `100/m` (100 requests per minute)
- **Purpose**: Rate limit for webhook endpoints to prevent abuse (SEC-2)
- **Example**: `WEBHOOK_RATE_LIMIT=100/m`

### WEBHOOK_RETENTION_DAYS
- **Required**: No
- **Type**: Integer
- **Default**: `180`
- **Purpose**: Number of days to retain webhook event records (SEC-3)
- **Example**: `WEBHOOK_RETENTION_DAYS=180`

### LOG_RETENTION_DAYS
- **Required**: No
- **Type**: Integer
- **Default**: `90`
- **Purpose**: Number of days to retain application logs (SEC-3)
- **Example**: `LOG_RETENTION_DAYS=90`

### AUDIT_LOG_ARCHIVE_DAYS
- **Required**: No
- **Type**: Integer
- **Default**: `365`
- **Purpose**: Number of days before audit logs are moved to cold storage (SEC-3)
- **Example**: `AUDIT_LOG_ARCHIVE_DAYS=365`

### ENABLE_AUTOMATED_CLEANUP
- **Required**: No
- **Type**: Boolean
- **Default**: `true` (in production)
- **Purpose**: Enable automated cleanup jobs for data retention (SEC-3)
- **Example**: `ENABLE_AUTOMATED_CLEANUP=true`

### CSP_REPORT_URI
- **Required**: No
- **Type**: String (URL)
- **Purpose**: Endpoint for Content Security Policy violation reports (SEC-4)
- **Example**: `CSP_REPORT_URI=https://your-csp-reporting-endpoint.com/report`

## Environment Variable Validation

The application validates required environment variables at startup. See [src/config/env_validator.py](../../src/config/env_validator.py) for validation logic.

## See Also
- [.env.example](../../.env.example) - Example environment file
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Production deployment guide
- [SECURITY.md](../../SECURITY.md) - Security configuration details
