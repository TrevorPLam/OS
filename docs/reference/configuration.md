# Configuration Reference

Configuration options and environment variables for UBOS.

## Configuration Overview

UBOS configuration is managed through:
- Environment variables (`.env` file)
- Django settings
- Frontend configuration

## Environment Variables

### Database
- `DATABASE_URL` - Database connection string
- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password

### Security
- `SECRET_KEY` - Django secret key
- `KMS_BACKEND` - Key management backend
- `LOCAL_KMS_MASTER_KEY` - Local KMS key (dev only)

### Application
- `DEBUG` - Debug mode (dev only)
- `ALLOWED_HOSTS` - Allowed hostnames
- `CORS_ORIGINS` - CORS allowed origins

### Services
- `REDIS_URL` - Redis connection
- `CELERY_BROKER_URL` - Celery broker
- `EMAIL_BACKEND` - Email backend
- `SMS_BACKEND` - SMS backend

## Configuration Files

### Backend
- `backend/config/settings.py` - Django settings
- `.env` - Environment variables

### Frontend
- `frontend/.env` - Frontend environment variables
- `frontend/vite.config.ts` - Vite configuration

## Configuration Management

- Use `.env.example` as template
- Never commit `.env` files
- Use environment-specific configs
- Document all configuration options

## Related Documentation

- [Local Setup](../development/local-setup.md) - Local configuration
- [Operations](../operations/README.md) - Production configuration
- [Security](../security/README.md) - Security configuration
