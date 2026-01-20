import pytest
from django.test import TestCase, override_settings

from modules.core.encryption import FieldEncryptionService, LocalKMSBackend
from modules.firm.models import Firm


pytestmark = [pytest.mark.e2e]


class TestEncryptionConfiguration(TestCase):
    """End-to-end validation of encryption configuration guardrails."""

    @override_settings(DEFAULT_FIRM_KMS_KEY_ID=None)
    def test_encrypt_requires_default_firm_key_when_firm_key_missing(self):
        """
        Ensure encryption fails fast when neither firm.kms_key_id nor
        DEFAULT_FIRM_KMS_KEY_ID is configured.
        """
        firm = Firm.objects.create(name="E2E Encryption Firm", slug="e2e-encryption-firm")
        service = FieldEncryptionService(LocalKMSBackend("test-master-key-32-bytes-long!!"))

        with pytest.raises(ValueError, match="DEFAULT_FIRM_KMS_KEY_ID"):
            service.encrypt_for_firm(firm.id, "sensitive-value")
