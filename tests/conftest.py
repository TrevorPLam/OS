import os
import sys
from pathlib import Path

import django
import pytest
from django.test.runner import DiscoverRunner

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("KMS_BACKEND", "local")
os.environ.setdefault("LOCAL_KMS_MASTER_KEY", "test-master-key-32-bytes-long!!")
os.environ.setdefault("DEFAULT_FIRM_KMS_KEY_ID", "test-default-firm-key")

django.setup()


@pytest.fixture(scope="session", autouse=True)
def django_test_environment(django_db_setup, django_db_blocker):
    test_runner = DiscoverRunner()
    test_runner.setup_test_environment()
    with django_db_blocker.unblock():
        old_config = test_runner.setup_databases()

    yield

    with django_db_blocker.unblock():
        test_runner.teardown_databases(old_config)
    test_runner.teardown_test_environment()
