# ConsultantPro - Production Deployment Guide

This guide covers deploying ConsultantPro to production environments with security best practices, performance optimization, and monitoring setup.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Migration](#database-migration)
4. [Static Files & Media](#static-files--media)
5. [Security Configuration](#security-configuration)
6. [Performance Optimization](#performance-optimization)
7. [Monitoring & Logging](#monitoring--logging)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (`pytest`)
- [ ] No security vulnerabilities (`bandit`, `safety`)
- [ ] Code linted (`black`, `flake8`, `eslint`)
- [ ] Dependencies up to date
- [ ] Environment variables documented

### Security
- [ ] SECRET_KEY is strong and unique
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS configured
- [ ] CORS origins restricted
- [ ] HTTPS enforced
- [ ] Database credentials secure
- [ ] AWS/Stripe keys are production keys

### Infrastructure
- [ ] Database backed up
- [ ] Log aggregation configured
- [ ] Error tracking setup (Sentry)
- [ ] Uptime monitoring configured
- [ ] SSL certificates valid

---

## Environment Setup

### 1. Create Production .env File

```bash
# Copy template
cp .env.example .env

# Edit with production values
nano .env
```

**Critical Settings:**

```bash
# Security
DJANGO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=consultantpro.com,www.consultantpro.com

# Database (Use managed PostgreSQL service)
POSTGRES_DB=consultantpro_prod
POSTGRES_USER=consultantpro_user
POSTGRES_PASSWORD=<strong-password>
POSTGRES_HOST=<rds-endpoint>.amazonaws.com
POSTGRES_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=https://consultantpro.com,https://www.consultantpro.com

# AWS S3 (Production bucket)
AWS_ACCESS_KEY_ID=<production-key>
AWS_SECRET_ACCESS_KEY=<production-secret>
AWS_STORAGE_BUCKET_NAME=consultantpro-prod-documents
AWS_S3_REGION_NAME=us-east-1

# Stripe (Production keys)
STRIPE_SECRET_KEY=sk_live_<your-key>
STRIPE_PUBLISHABLE_KEY=pk_live_<your-key>
STRIPE_WEBHOOK_SECRET=whsec_<your-webhook-secret>
```

### 2. Database Setup

```bash
# Create production database
createdb consultantpro_prod

# Run migrations
python src/manage.py migrate

# Create superuser
python src/manage.py createsuperuser

# Collect static files
python src/manage.py collectstatic --noinput
```

---

## Database Migration

### Safe Migration Process

```bash
# 1. Backup database
pg_dump consultantpro_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Test migrations on staging
python src/manage.py migrate --plan
python src/manage.py migrate --check

# 3. Apply migrations
python src/manage.py migrate

# 4. Verify
python src/manage.py showmigrations
```

### Rollback Plan

```bash
# Restore from backup if needed
psql consultantpro_prod < backup_<timestamp>.sql
```

---

## Static Files & Media

### Option 1: Serve from S3/CloudFront

```python
# settings.py
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
```

### Option 2: Serve from Nginx

```nginx
location /static/ {
    alias /var/www/consultantpro/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location /media/ {
    alias /var/www/consultantpro/media/;
    expires 7d;
}
```

---

## Security Configuration

### 1. Django Security Settings

**Already configured in `settings.py` when DEBUG=False:**

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 2. Rate Limiting

**Already configured** via Django REST Framework throttling:
- 100 requests/minute (burst)
- 1000 requests/hour (sustained)
- 10 requests/minute (payments)

### 3. Firewall Rules

```bash
# Allow only HTTPS traffic
ufw allow 443/tcp
ufw allow 80/tcp  # For redirect to HTTPS
ufw allow 22/tcp  # SSH (restrict to IP whitelist)

# Database (internal only)
ufw deny 5432/tcp from any
ufw allow from <app-server-ip> to any port 5432
```

### 4. SSL/TLS Setup

```bash
# Using Let's Encrypt with Certbot
sudo certbot --nginx -d consultantpro.com -d www.consultantpro.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Performance Optimization

### 1. Gunicorn Configuration

```bash
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4  # (2 x CPU cores) + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 5
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
```

**Run:**

```bash
gunicorn config.wsgi:application -c gunicorn.conf.py
```

### 2. Nginx Configuration

```nginx
upstream consultantpro {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name consultantpro.com www.consultantpro.com;

    ssl_certificate /etc/letsencrypt/live/consultantpro.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/consultantpro.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 100M;

    location / {
        proxy_pass http://consultantpro;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_redirect off;
    }

    location /static/ {
        alias /var/www/consultantpro/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/consultantpro/media/;
        expires 7d;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name consultantpro.com www.consultantpro.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. Database Connection Pooling

```python
# settings.py (already configured)
DATABASES = {
    'default': {
        # ...
        'CONN_MAX_AGE': 600,  # 10 minutes
    }
}
```

### 4. Redis Caching (Optional)

```bash
pip install redis django-redis
```

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session storage
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

---

## Monitoring & Logging

### 1. Error Tracking with Sentry

```bash
pip install sentry-sdk
```

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    environment='production',
    traces_sample_rate=0.1,
)
```

### 2. Application Monitoring

**Recommended tools:**
- **New Relic** - APM and performance monitoring
- **DataDog** - Infrastructure and application monitoring
- **Prometheus + Grafana** - Custom metrics

### 3. Log Aggregation

**Using CloudWatch Logs:**

```python
# Install
pip install watchtower

# settings.py
import watchtower

LOGGING['handlers']['cloudwatch'] = {
    'class': 'watchtower.CloudWatchLogHandler',
    'log_group': 'consultantpro-prod',
    'stream_name': 'django-app',
}
```

### 4. Uptime Monitoring

**Set up alerts:**
- Pingdom / UptimeRobot
- StatusPage.io
- CloudWatch Alarms

---

## CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /var/www/consultantpro
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python src/manage.py migrate
            python src/manage.py collectstatic --noinput
            sudo systemctl restart gunicorn
            sudo systemctl restart nginx
```

---

## Rollback Procedures

### Quick Rollback

```bash
# 1. Revert code
git revert HEAD
git push origin main

# 2. Restore database (if needed)
psql consultantpro_prod < backup_<timestamp>.sql

# 3. Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# 4. Verify
curl -I https://consultantpro.com
```

### Blue-Green Deployment

```bash
# Deploy to green environment
# Test thoroughly
# Switch traffic (load balancer / DNS)
# Keep blue environment for 24h as fallback
```

---

## Health Checks

### Application Health Endpoint

Create `/health/` endpoint:

```python
# config/urls.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        # Check database
        connection.ensure_connection()

        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
        }, status=500)

urlpatterns += [
    path('health/', health_check),
]
```

### Monitor Endpoint

```bash
# Set up monitoring
curl https://consultantpro.com/health/

# Expected: {"status":"healthy","database":"connected"}
```

---

## Maintenance Mode

```nginx
# nginx - maintenance page
if (-f /var/www/consultantpro/maintenance.html) {
    return 503;
}

error_page 503 @maintenance;
location @maintenance {
    root /var/www/consultantpro;
    rewrite ^(.*)$ /maintenance.html break;
}
```

Enable maintenance:

```bash
touch /var/www/consultantpro/maintenance.html
```

---

## Performance Benchmarks

### Expected Performance (Production)

- API response time: < 200ms (p95)
- Database queries: < 50ms (p95)
- Static file delivery: < 100ms
- Uptime: > 99.9%

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 100 https://consultantpro.com/api/crm/clients/

# Using Locust
locust -f loadtest.py --host=https://consultantpro.com
```

---

## Support & Maintenance

### Regular Tasks

**Daily:**
- Monitor error logs
- Check uptime metrics
- Review Sentry errors

**Weekly:**
- Review performance metrics
- Update dependencies (security patches)
- Backup verification

**Monthly:**
- Database optimization (VACUUM, ANALYZE)
- SSL certificate renewal check
- Security audit
- Dependency updates

---

## Emergency Contacts

```
On-Call Engineer: <phone>
DevOps Lead: <phone>
Database Admin: <phone>
Security Team: <email>
```

---

## Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [Security Best Practices](https://docs.djangoproject.com/en/4.2/topics/security/)
- [Performance Optimization](https://docs.djangoproject.com/en/4.2/topics/performance/)

---

**Last Updated:** 2025-12-20
