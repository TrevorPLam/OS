"""Encryption utilities for field-level E2EE.

Implements a lightweight envelope encryption service that can run against
AWS KMS or a local, Fernet-backed test key. The service is intentionally
stateless: ciphertexts are prefixed so that downstream serializers and
services can detect whether a value needs decryption.
"""

import base64
import hashlib
import os
from dataclasses import dataclass
from typing import Protocol

import boto3
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


ENCRYPTED_PREFIX = "enc::"


class EncryptionBackend(Protocol):
    """Protocol for encrypt/decrypt operations."""

    def encrypt(self, key_id: str, plaintext: str) -> str:  # pragma: no cover - interface
        ...

    def decrypt(self, key_id: str, ciphertext: str) -> str:  # pragma: no cover - interface
        ...


class LocalKMSBackend:
    """Deterministic Fernet-based backend for tests and local runs."""

    def __init__(self, master_key: str):
        if not master_key:
            raise ValueError("LOCAL_KMS_MASTER_KEY is required for LocalKMSBackend")
        self.master_key = master_key.encode()

    def _derive_key(self, key_id: str) -> Fernet:
        digest = hashlib.sha256(self.master_key + key_id.encode()).digest()
        return Fernet(base64.urlsafe_b64encode(digest))

    def encrypt(self, key_id: str, plaintext: str) -> str:
        fernet = self._derive_key(key_id)
        return fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, key_id: str, ciphertext: str) -> str:
        fernet = self._derive_key(key_id)
        try:
            return fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as exc:  # pragma: no cover - defensive
            raise ValueError("Invalid ciphertext for provided key") from exc


class AWSKMSBackend:
    """AWS KMS-backed envelope encryption for production."""

    def __init__(self):
        self.client = boto3.client(
            "kms",
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def encrypt(self, key_id: str, plaintext: str) -> str:
        response = self.client.encrypt(KeyId=key_id, Plaintext=plaintext.encode())
        return base64.b64encode(response["CiphertextBlob"]).decode()

    def decrypt(self, key_id: str, ciphertext: str) -> str:
        response = self.client.decrypt(
            KeyId=key_id, CiphertextBlob=base64.b64decode(ciphertext.encode())
        )
        return response["Plaintext"].decode()


def _get_backend() -> EncryptionBackend:
    backend = os.environ.get("KMS_BACKEND", "local").lower()
    if backend == "aws":
        return AWSKMSBackend()
    return LocalKMSBackend(os.environ.get("LOCAL_KMS_MASTER_KEY", "local-dev-master-key"))


def _firm_key_id(firm_id: int) -> str:
    from modules.firm.models import Firm

    firm = Firm.objects.only("id", "kms_key_id").get(id=firm_id)
    if firm.kms_key_id:
        return firm.kms_key_id
    return settings.DEFAULT_FIRM_KMS_KEY_ID


@dataclass
class FieldEncryptionService:
    """Encrypt/decrypt content fields with firm-scoped keys."""

    backend: EncryptionBackend

    def encrypt_for_firm(self, firm_id: int, plaintext: str | None) -> str | None:
        if plaintext in (None, ""):
            return plaintext
        if self.is_encrypted(plaintext):
            return plaintext
        key_id = _firm_key_id(firm_id)
        ciphertext = self.backend.encrypt(key_id, plaintext)
        return f"{ENCRYPTED_PREFIX}{ciphertext}"

    def decrypt_for_firm(self, firm_id: int, value: str | None) -> str | None:
        if value in (None, ""):
            return value
        if not self.is_encrypted(value):
            return value
        key_id = _firm_key_id(firm_id)
        ciphertext = value[len(ENCRYPTED_PREFIX) :]
        return self.backend.decrypt(key_id, ciphertext)

    def fingerprint_for_firm(self, firm_id: int, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        key_material = f"{_firm_key_id(firm_id)}:{value}".encode()
        return hashlib.sha256(key_material).hexdigest()

    @staticmethod
    def is_encrypted(value: str | None) -> bool:
        return bool(value) and value.startswith(ENCRYPTED_PREFIX)


field_encryption_service = FieldEncryptionService(_get_backend())
