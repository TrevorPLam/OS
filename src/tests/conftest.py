"""
Pytest configuration for ConsultantPro tests.

Implements ASSESS-C3.10: Standardize tests to use Postgres (not SQLite).
"""

import os
import pytest
from django.conf import settings
from django.db import connections
from django.test.utils import get_runner

# SECURITY: Force Postgres for all tests (ASSESS-C3.10)
# This ensures test/prod environment alignment and eliminates SQLite vs Postgres drift
if 'test' in os.sys.argv or 'pytest' in os.sys.argv[0]:
    # Override database settings to use Postgres for tests
    # This ensures tests run against the same database engine as production
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'consultantpro_test'),
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            'TEST': {
                'NAME': 'consultantpro_test',
            },
        }
    }
    
    # Update settings if not already set
    if not hasattr(settings, 'DATABASES') or settings.DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
        settings.DATABASES = DATABASES


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Ensure all tests use Postgres database.
    
    This fixture runs before any database-dependent tests and verifies
    that the test database is using Postgres, not SQLite.
    """
    with django_db_blocker.unblock():
        db_engine = connections['default'].settings_dict['ENGINE']
        if 'sqlite' in db_engine.lower():
            pytest.fail(
                "Tests must use Postgres, not SQLite. "
                "Set POSTGRES_* environment variables or use docker-compose for test database."
            )


@pytest.fixture(autouse=True)
def enable_db_foreign_keys(db):
    """
    Enable foreign key constraints for SQLite (if used) or verify Postgres constraints.
    
    ASSESS-C3.10: Enable SQLite foreign keys if SQLite is used.
    For Postgres, foreign keys are always enabled.
    """
    from django.db import connection
    
    if 'sqlite' in connection.vendor:
        # Enable foreign key constraints for SQLite
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = ON;")
    # Postgres always has foreign keys enabled, no action needed