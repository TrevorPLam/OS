# DEPLOYMENT.md

Last Updated: 2026-01-06

This repo is a template. Fill this in for real projects.

## Prerequisites

### System Dependencies

The application requires the following system dependencies to be installed:

- **PostgreSQL client libraries** (`libpq-dev` on Debian/Ubuntu, `postgresql-devel` on RHEL/CentOS)
  - Required for compiling `psycopg2` from source (production database adapter)
  - Already included in the Docker image
  - For local development without Docker: `apt-get install libpq-dev` (Debian/Ubuntu) or `yum install postgresql-devel` (RHEL/CentOS)

- **Build tools** (`build-essential` on Debian/Ubuntu)
  - Required for compiling Python packages with C extensions

## Target environments
- Local development:
- Staging:
- Production:

## Deployment method
- CI/CD:
- Infrastructure:
- Secrets management:

## Rollback plan
- How to rollback:
- Data migration rollback (if applicable):
