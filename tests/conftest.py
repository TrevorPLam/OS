import os
import sys
from pathlib import Path

import django
import pytest
from django.test.runner import DiscoverRunner

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_auth_test")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("USE_SQLITE_FOR_TESTS", "True")

django.setup()


@pytest.fixture(scope="session", autouse=True)
def django_test_environment():
    test_runner = DiscoverRunner()
    test_runner.setup_test_environment()
    old_config = test_runner.setup_databases()

    yield

    test_runner.teardown_databases(old_config)
    test_runner.teardown_test_environment()
