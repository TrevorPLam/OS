import pytest
from django.test import override_settings

from job_guards import require_client_for_job, require_firm_for_job
from modules.clients.models import Client
from modules.firm.models import Firm
from modules.firm.utils import FirmScopingError


SQLITE_DB_SETTINGS = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


@pytest.mark.django_db
@override_settings(DATABASES=SQLITE_DB_SETTINGS)
def test_require_firm_for_job_missing():
    with pytest.raises(FirmScopingError):
        require_firm_for_job(None)


@pytest.mark.django_db
@override_settings(DATABASES=SQLITE_DB_SETTINGS)
def test_require_client_for_job_missing_ids():
    firm = Firm.objects.create(name="Demo Firm", subdomain="demo")

    with pytest.raises(FirmScopingError):
        require_client_for_job(firm.id, None)


@pytest.mark.django_db
@override_settings(DATABASES=SQLITE_DB_SETTINGS)
def test_require_client_for_job_enforces_membership():
    firm_a = Firm.objects.create(name="Firm A", subdomain="firma")
    firm_b = Firm.objects.create(name="Firm B", subdomain="firmb")
    client = Client.objects.create(firm=firm_b, company_name="Client B")

    with pytest.raises(FirmScopingError):
        require_client_for_job(firm_a.id, client.id)
