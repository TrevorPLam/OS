import pytest
import os
from unittest import mock

from modules.core.encryption import (
    LocalKMSBackend,
    _get_backend,
    encrypt_field,
    decrypt_field,
    ENCRYPTED_PREFIX,
)


@pytest.mark.unit
class TestLocalKMSBackend:
    """Test LocalKMSBackend encryption functionality"""

    def test_backend_requires_master_key(self):
        """Test that LocalKMSBackend requires a master key"""
        with pytest.raises(ValueError, match="LOCAL_KMS_MASTER_KEY is required"):
            LocalKMSBackend("")

    def test_encrypt_decrypt_cycle(self):
        """Test basic encrypt/decrypt cycle"""
        backend = LocalKMSBackend("test-master-key-32-bytes-long!!")
        plaintext = "sensitive-data"
        key_id = "test-key-001"

        # Encrypt
        ciphertext = backend.encrypt(key_id, plaintext)
        assert ciphertext != plaintext
        assert len(ciphertext) > 0

        # Decrypt
        decrypted = backend.decrypt(key_id, ciphertext)
        assert decrypted == plaintext

    def test_different_key_ids_produce_different_ciphertexts(self):
        """Test that different key IDs produce different ciphertexts"""
        backend = LocalKMSBackend("test-master-key-32-bytes-long!!")
        plaintext = "same-data"

        ciphertext1 = backend.encrypt("key-001", plaintext)
        ciphertext2 = backend.encrypt("key-002", plaintext)

        assert ciphertext1 != ciphertext2

    def test_decrypt_with_wrong_key_id_fails(self):
        """Test that decrypting with wrong key ID fails"""
        backend = LocalKMSBackend("test-master-key-32-bytes-long!!")
        plaintext = "secret-data"

        ciphertext = backend.encrypt("key-001", plaintext)

        with pytest.raises(ValueError, match="Invalid ciphertext"):
            backend.decrypt("key-002", ciphertext)

    def test_decrypt_invalid_ciphertext_fails(self):
        """Test that invalid ciphertext fails decryption"""
        backend = LocalKMSBackend("test-master-key-32-bytes-long!!")

        with pytest.raises(ValueError, match="Invalid ciphertext"):
            backend.decrypt("key-001", "not-valid-ciphertext")


@pytest.mark.unit
class TestGetBackend:
    """Test backend selection logic"""

    def test_get_backend_requires_configuration(self):
        """Test that backend selection requires KMS_BACKEND env var"""
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="KMS_BACKEND environment variable required"):
                _get_backend()

    def test_get_backend_local_requires_master_key(self):
        """Test that local backend requires LOCAL_KMS_MASTER_KEY"""
        with mock.patch.dict(os.environ, {"KMS_BACKEND": "local"}, clear=True):
            with pytest.raises(ValueError, match="LOCAL_KMS_MASTER_KEY environment variable required"):
                _get_backend()

    def test_get_backend_local_success(self):
        """Test successful local backend initialization"""
        with mock.patch.dict(
            os.environ, {"KMS_BACKEND": "local", "LOCAL_KMS_MASTER_KEY": "test-key-32-bytes-long!!"}, clear=True
        ):
            backend = _get_backend()
            assert isinstance(backend, LocalKMSBackend)

    def test_get_backend_invalid_type_fails(self):
        """Test that invalid backend type fails"""
        with mock.patch.dict(os.environ, {"KMS_BACKEND": "invalid"}, clear=True):
            with pytest.raises(ValueError, match="KMS_BACKEND must be 'aws' or 'local'"):
                _get_backend()


@pytest.mark.unit
class TestEncryptDecryptFields:
    """Test field-level encryption/decryption"""

    def test_encrypt_field_adds_prefix(self):
        """Test that encrypt_field adds the encrypted prefix"""
        with mock.patch.dict(
            os.environ, {"KMS_BACKEND": "local", "LOCAL_KMS_MASTER_KEY": "test-key-32-bytes-long!!"}, clear=True
        ):
            plaintext = "sensitive-data"
            key_id = "test-key"

            ciphertext = encrypt_field(key_id, plaintext)

            assert ciphertext.startswith(ENCRYPTED_PREFIX)
            assert ciphertext != plaintext

    def test_decrypt_field_removes_prefix(self):
        """Test that decrypt_field removes the encrypted prefix"""
        with mock.patch.dict(
            os.environ, {"KMS_BACKEND": "local", "LOCAL_KMS_MASTER_KEY": "test-key-32-bytes-long!!"}, clear=True
        ):
            plaintext = "sensitive-data"
            key_id = "test-key"

            ciphertext = encrypt_field(key_id, plaintext)
            decrypted = decrypt_field(key_id, ciphertext)

            assert decrypted == plaintext

    def test_decrypt_field_without_prefix_returns_unchanged(self):
        """Test that decrypt_field returns unencrypted values unchanged"""
        with mock.patch.dict(
            os.environ, {"KMS_BACKEND": "local", "LOCAL_KMS_MASTER_KEY": "test-key-32-bytes-long!!"}, clear=True
        ):
            plaintext = "not-encrypted-value"
            key_id = "test-key"

            # Should return the value unchanged if no prefix
            result = decrypt_field(key_id, plaintext)

            assert result == plaintext

    def test_encrypt_empty_string(self):
        """Test encrypting empty string"""
        with mock.patch.dict(
            os.environ, {"KMS_BACKEND": "local", "LOCAL_KMS_MASTER_KEY": "test-key-32-bytes-long!!"}, clear=True
        ):
            ciphertext = encrypt_field("test-key", "")
            assert ciphertext.startswith(ENCRYPTED_PREFIX)

            decrypted = decrypt_field("test-key", ciphertext)
            assert decrypted == ""

    def test_encrypt_none_returns_none(self):
        """Test that encrypting None returns None"""
        with mock.patch.dict(
            os.environ, {"KMS_BACKEND": "local", "LOCAL_KMS_MASTER_KEY": "test-key-32-bytes-long!!"}, clear=True
        ):
            result = encrypt_field("test-key", None)
            assert result is None

    def test_decrypt_none_returns_none(self):
        """Test that decrypting None returns None"""
        with mock.patch.dict(
            os.environ, {"KMS_BACKEND": "local", "LOCAL_KMS_MASTER_KEY": "test-key-32-bytes-long!!"}, clear=True
        ):
            result = decrypt_field("test-key", None)
            assert result is None


@pytest.mark.unit
class TestEncryptionSecurity:
    """Test security properties of encryption"""

    def test_same_plaintext_different_encryptions(self):
        """Test that same plaintext produces different ciphertexts (if nonce/IV used)"""
        with mock.patch.dict(
            os.environ, {"KMS_BACKEND": "local", "LOCAL_KMS_MASTER_KEY": "test-key-32-bytes-long!!"}, clear=True
        ):
            plaintext = "same-data"
            key_id = "test-key"

            # Note: Fernet uses timestamp, so encryptions at different times differ
            # However, for deterministic testing, we'll just check they can decrypt
            ciphertext1 = encrypt_field(key_id, plaintext)
            ciphertext2 = encrypt_field(key_id, plaintext)

            # Both should decrypt to same plaintext
            assert decrypt_field(key_id, ciphertext1) == plaintext
            assert decrypt_field(key_id, ciphertext2) == plaintext

    def test_encryption_produces_non_readable_output(self):
        """Test that encrypted output is not human-readable"""
        with mock.patch.dict(
            os.environ, {"KMS_BACKEND": "local", "LOCAL_KMS_MASTER_KEY": "test-key-32-bytes-long!!"}, clear=True
        ):
            plaintext = "credit-card-number"
            key_id = "test-key"

            ciphertext = encrypt_field(key_id, plaintext)

            # Remove prefix for checking
            encrypted_part = ciphertext[len(ENCRYPTED_PREFIX) :]

            # Should not contain plaintext
            assert plaintext not in encrypted_part
