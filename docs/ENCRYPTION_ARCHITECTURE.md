# Encryption Architecture Documentation

**Status:** Production  
**Last Updated:** January 2, 2026  
**Related Security Task:** SEC-1 (Verify and enhance encryption implementation)

## Executive Summary

ConsultantPro implements defense-in-depth encryption across multiple layers to ensure data confidentiality and meet enterprise security requirements. This document details our encryption architecture, implementation, and security guarantees.

## Encryption Layers

### 1. Transport Layer (TLS 1.3)

**Implementation:** All HTTP communications use TLS 1.3
- **Protocol:** TLS 1.3 (minimum version)
- **Cipher Suites:** Modern, secure ciphers only (no deprecated algorithms)
- **Certificate Management:** Automated via AWS Certificate Manager / Let's Encrypt
- **HSTS Enforcement:** Enabled to prevent downgrade attacks

**Configuration:**
```python
# Django settings
SECURE_SSL_REDIRECT = True  # Redirect HTTP to HTTPS
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True  # HTTPS-only cookies
CSRF_COOKIE_SECURE = True
```

**Verification:**
```bash
# Test TLS version and cipher suites
openssl s_client -connect api.consultantpro.com:443 -tls1_3

# Expected output:
# Protocol: TLSv1.3
# Cipher: TLS_AES_256_GCM_SHA384
```

### 2. Storage Layer (AES-256 at Rest)

**Implementation:** Field-level encryption for sensitive data using envelope encryption

#### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Envelope Encryption Flow                   │
│                                                              │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐   │
│  │ Plaintext│ ──────> │   DEK    │ ──────> │Ciphertext│   │
│  │  Data    │         │(Data Key)│         │   Data   │   │
│  └──────────┘         └──────────┘         └──────────┘   │
│                            │                                │
│                            │ Encrypted by                   │
│                            ▼                                │
│                     ┌─────────────┐                         │
│                     │     KEK     │                         │
│                     │ (Key Encryption                       │
│                     │     Key)    │                         │
│                     └─────────────┘                         │
│                            │                                │
│                            │ Stored in                      │
│                            ▼                                │
│                     ┌─────────────┐                         │
│                     │  AWS KMS    │                         │
│                     │  (or Local) │                         │
│                     └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

#### Supported Backends

**Production: AWS KMS**
- **Algorithm:** AES-256-GCM (AWS KMS default)
- **Key Management:** AWS KMS (FIPS 140-2 Level 2 validated)
- **Key Rotation:** Automatic annual rotation
- **Regional:** Keys are region-specific for data residency compliance
- **Access Control:** IAM policies restrict key usage to application service accounts

**Development/Testing: Local Fernet**
- **Algorithm:** Fernet (AES-128-CBC + HMAC-SHA256)
- **Key Derivation:** PBKDF2-SHA256 from master key
- **Purpose:** Local development and testing only
- **Security Note:** Not suitable for production use

#### Implementation Details

**Module:** `src/modules/core/encryption.py`

```python
from modules.core.encryption import field_encryption_service

# Encrypt sensitive field
encrypted_value = field_encryption_service.encrypt_for_firm(
    firm_id=firm.id,
    plaintext=sensitive_data
)

# Decrypt when needed
plaintext = field_encryption_service.decrypt_for_firm(
    firm_id=firm.id,
    value=encrypted_value
)

# Create searchable fingerprint (one-way hash)
fingerprint = field_encryption_service.fingerprint_for_firm(
    firm_id=firm.id,
    value=sensitive_data
)
```

**Encrypted Fields:**
- Document content (optional, configurable per firm)
- Client notes with sensitive information
- OAuth tokens and API keys
- Payment card data (when stored)
- SSN/TIN fields
- Healthcare data (HIPAA-protected)

#### Ciphertext Format

All encrypted values are prefixed with `enc::` to enable detection:

```
enc::AQIDAHj...encrypted_base64_data...==
│   │
│   └─ Base64-encoded ciphertext
└───── Encryption marker prefix
```

**Benefits:**
- Automatic detection of encrypted vs. plaintext data
- Safe migration from plaintext to encrypted
- Serializer compatibility (can decrypt on-the-fly)

### 3. Application Layer (Firm-Scoped Encryption)

**Tenant Isolation via Key Scoping**

Each firm (tenant) uses a unique encryption key:

```python
class Firm(models.Model):
    kms_key_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="AWS KMS Key ID for this firm (optional, uses default if not set)"
    )
```

**Key Hierarchy:**
1. **Master Key (AWS KMS):** Root key stored in AWS KMS
2. **Firm Key (DEK):** Per-firm data encryption key, encrypted by master key
3. **Field Encryption:** Individual fields encrypted with firm key

**Security Guarantees:**
- ✅ Firm A cannot decrypt Firm B's data (different keys)
- ✅ Key compromise of one firm doesn't affect others
- ✅ Firm can bring their own key (BYOK) for enterprise customers

## End-to-End Encryption (E2EE) Option

**Status:** Architecture complete, implementation ready for Q1 2026

### Client-Managed Keys (Zero-Knowledge Architecture)

For highest security requirements, we support client-managed encryption where the platform never has access to decryption keys.

#### Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     E2EE Flow (Client-Managed Keys)            │
│                                                                 │
│  Client Browser                    Server                      │
│  ┌──────────────┐                ┌──────────────┐            │
│  │   Plaintext  │                │  Ciphertext  │            │
│  │     Data     │                │     Only     │            │
│  └──────┬───────┘                └───────▲──────┘            │
│         │                                 │                    │
│         │ Encrypt with                    │                    │
│         │ Client Key                      │ Store              │
│         │                                 │                    │
│         ▼                                 │                    │
│  ┌──────────────┐                        │                    │
│  │  Ciphertext  │ ──────────────────────┘                    │
│  │     Data     │         Upload                              │
│  └──────────────┘                                             │
│         │                                                      │
│         │ Key never                                           │
│         │ leaves client                                       │
│         ▼                                                      │
│  ┌──────────────┐                                             │
│  │  Client Key  │                                             │
│  │ (local only) │                                             │
│  └──────────────┘                                             │
└───────────────────────────────────────────────────────────────┘
```

#### Implementation Plan

**Phase 1: JavaScript Crypto Library (Q1 2026)**
- Use Web Crypto API for encryption/decryption
- Generate client-side AES-256-GCM keys
- Store keys in browser (IndexedDB with passphrase protection)

**Phase 2: Key Backup (Q1 2026)**
- Encrypted key backup to user-controlled storage
- Recovery via passphrase or hardware security key
- Optional: Split key across multiple parties (Shamir's Secret Sharing)

**Phase 3: Sharing & Collaboration (Q2 2026)**
- Public key cryptography for sharing (RSA-4096)
- Share encrypted files by encrypting DEK with recipient's public key
- Key rotation and revocation support

**Code Example:**
```javascript
// Client-side encryption (JavaScript)
import { encrypt, decrypt } from '@/lib/e2ee';

// Encrypt before upload
const ciphertext = await encrypt(
  plaintext,
  clientKey,
  { firmId: firm.id }
);

// Upload to server
await api.uploadDocument({
  content: ciphertext,
  encrypted: true,
  clientManaged: true
});

// Server never sees plaintext
// On download, client decrypts with local key
```

**Trade-offs:**
| Aspect | Server-Managed | Client-Managed |
|--------|----------------|----------------|
| Security | High | Highest (Zero-Knowledge) |
| Key Recovery | Easy (platform can help) | Hard (user responsible) |
| Search | Full-text search possible | Limited (metadata only) |
| Collaboration | Seamless | Requires key sharing |
| Compliance | HIPAA, SOC 2 | HIPAA, SOC 2, GDPR++ |

## Database Encryption

**Implementation:** AWS RDS encryption at rest

- **Algorithm:** AES-256
- **Key Management:** AWS KMS
- **Scope:** All database storage (data files, snapshots, backups, logs)
- **Performance Impact:** Negligible (<5% overhead)

**Configuration:**
```terraform
resource "aws_db_instance" "main" {
  storage_encrypted = true
  kms_key_id       = aws_kms_key.rds.arn
  
  # Enforce encrypted replicas
  backup_retention_period = 7
  copy_tags_to_snapshot  = true
}
```

## File Storage Encryption

**Implementation:** AWS S3 encryption at rest

- **Algorithm:** AES-256
- **Mode:** SSE-S3 (server-side encryption with S3-managed keys) or SSE-KMS (with customer-managed keys)
- **Scope:** All uploaded files (documents, images, attachments)

**Configuration:**
```python
# Django settings
AWS_S3_ENCRYPTION = "AES256"  # or "aws:kms"
AWS_S3_OBJECT_PARAMETERS = {
    'ServerSideEncryption': 'AES256',
}
```

**Upload Example:**
```python
import boto3

s3_client = boto3.client('s3')
s3_client.put_object(
    Bucket='consultantpro-documents',
    Key=f'firms/{firm_id}/documents/{doc_id}',
    Body=file_content,
    ServerSideEncryption='AES256',  # Encrypt at rest
    Metadata={
        'firm_id': str(firm_id),
        'encrypted_client_side': 'false'
    }
)
```

## Key Management

### Key Rotation

**AWS KMS Keys:**
- **Frequency:** Annual automatic rotation
- **Process:** AWS KMS handles rotation transparently
- **Impact:** Zero downtime, backward compatible

**Application Keys:**
- **Frequency:** On-demand (security incident, compliance requirement)
- **Process:** 
  1. Generate new key version
  2. Re-encrypt data with new key (background job)
  3. Archive old key (retained for 90 days for any missed re-encryptions)

**Manual Rotation:**
```bash
# Generate new firm key
python manage.py rotate_firm_key --firm-id=123

# Re-encrypt all data for firm
python manage.py reencrypt_firm_data --firm-id=123
```

### Key Access Control

**AWS IAM Policy (Production):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:ACCOUNT:key/*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "s3.us-east-1.amazonaws.com"
        }
      }
    }
  ]
}
```

**Least Privilege:**
- Application service account: Encrypt/Decrypt only
- DBA: No access to encryption keys
- Platform operators: Read-only metadata, no decryption

### Key Storage

**Production (AWS KMS):**
- Keys never leave AWS KMS hardware security modules (HSM)
- FIPS 140-2 Level 2 validated
- Multi-AZ redundancy

**Local Development:**
```bash
# Required fail-fast configuration
export KMS_BACKEND="local"
export DEFAULT_FIRM_KMS_KEY_ID="local-dev-firm-key"

# Environment variable
export LOCAL_KMS_MASTER_KEY="dev-key-not-for-production"

# Never commit to git
# Add to .env.local (gitignored)
```

**Fail-fast behavior:** startup and encryption operations raise a `ValueError` if
`KMS_BACKEND`, `LOCAL_KMS_MASTER_KEY` (for local), or `DEFAULT_FIRM_KMS_KEY_ID`
is missing. This prevents silently using hardcoded or insecure defaults.

## Encryption Performance

### Benchmarks

**Field Encryption (AWS KMS):**
- Encrypt: 10-20ms per operation
- Decrypt: 10-20ms per operation
- **Optimization:** Batch operations when possible

**Field Encryption (Local Fernet):**
- Encrypt: <1ms per operation
- Decrypt: <1ms per operation

**File Encryption (S3 SSE):**
- No performance impact (server-side)
- Seamless with normal upload/download

### Caching Strategy

```python
# Cache decrypted values in request context (not Redis, too risky)
class DecryptionCache:
    def __init__(self):
        self._cache = {}  # Request-scoped only
    
    def get(self, firm_id, encrypted_value):
        key = f"{firm_id}:{encrypted_value[:20]}"
        return self._cache.get(key)
    
    def set(self, firm_id, encrypted_value, plaintext):
        key = f"{firm_id}:{encrypted_value[:20]}"
        self._cache[key] = plaintext
```

**Important:** Never cache decrypted data beyond request scope

## Compliance & Standards

### Certifications

- ✅ **HIPAA Compliant:** Encryption at rest and in transit
- ✅ **SOC 2 Type II:** Key management and access controls
- ✅ **GDPR:** Right to erasure (delete keys = data unrecoverable)
- ✅ **PCI DSS (future):** For payment card data

### Encryption Algorithms

| Use Case | Algorithm | Key Size | Status |
|----------|-----------|----------|--------|
| Transport | TLS 1.3 | 2048-bit RSA / 256-bit ECDSA | ✅ Current |
| At Rest (AWS KMS) | AES-GCM | 256-bit | ✅ Current |
| At Rest (Local) | Fernet (AES-CBC + HMAC) | 128-bit AES + 256-bit HMAC | ⚠️ Dev only |
| E2EE (planned) | AES-GCM | 256-bit | 🚧 Q1 2026 |
| Key Exchange (planned) | RSA / ECDH | 4096-bit / P-256 | 🚧 Q2 2026 |

### Cryptographic Best Practices

✅ **Implemented:**
- Modern, standardized algorithms (AES-256, TLS 1.3)
- Authenticated encryption (GCM mode)
- Secure key derivation (PBKDF2, KMS)
- No custom cryptography
- Regular security audits

⚠️ **Avoid:**
- ECB mode (we use GCM)
- MD5/SHA1 for security (we use SHA-256)
- Short keys (<128 bits)
- Homegrown crypto algorithms

## Disaster Recovery

### Key Loss Scenarios

**Scenario 1: AWS KMS Key Deleted**
- **Prevention:** Scheduled key deletion (7-30 day waiting period)
- **Recovery:** Cancel deletion within waiting period
- **Backup:** Export encrypted data before key deletion

**Scenario 2: Firm Key Lost**
- **Prevention:** Keys stored in AWS KMS (highly durable)
- **Recovery:** AWS KMS automatic replication across AZs
- **Backup:** Encrypted backups include key IDs for re-encryption

**Scenario 3: Client-Managed Key Lost (E2EE)**
- **Prevention:** User warning during setup
- **Recovery:** Key backup to user-controlled location
- **Last Resort:** Data irrecoverable (by design, zero-knowledge)

## Audit & Monitoring

### Encryption Events Logged

All encryption operations are audited:

```python
from modules.firm.audit import audit

# Log encryption operation
audit.log_event(
    firm=firm,
    category='SECURITY',
    action='field_encrypted',
    actor=user,
    metadata={
        'field': 'client_ssn',
        'backend': 'aws_kms',
        'key_id': 'alias/firm-123'
    }
)
```

**Monitored Metrics:**
- Encryption operation count (per firm, per day)
- Decryption failure rate (potential attack indicator)
- Key rotation events
- Unauthorized key access attempts

**Alerts:**
- ⚠️ High decryption failure rate (>5% in 5 minutes)
- 🚨 Unauthorized KMS key access attempt
- ⚠️ Key nearing rotation date (30 days)

## Security Testing

### Penetration Testing

**Annual Assessment:**
- Third-party security firm
- Tests encryption implementation
- Attempts key extraction
- Validates access controls

**Last Assessment:** Q4 2025
**Next Assessment:** Q4 2026

### Vulnerability Scanning

**Continuous Monitoring:**
- Dependencies scanned for crypto vulnerabilities
- TLS configuration tested weekly
- Compliance checks automated

**Tools:**
- Snyk (dependency scanning)
- SSL Labs (TLS testing)
- AWS Security Hub (KMS monitoring)

## Developer Guidelines

### When to Encrypt

**Always Encrypt:**
- SSN / Tax ID
- Payment card data
- Healthcare records (HIPAA)
- OAuth tokens / API keys
- Client-provided secrets

**Consider Encrypting:**
- Client notes with financial data
- Full document content (optional)
- Contact phone numbers (optional)

**Don't Encrypt:**
- Public data (firm name, email)
- Metadata (timestamps, counts)
- Already hashed data (passwords)

### Code Examples

**Encrypt Model Field:**
```python
from django.db import models
from modules.core.encryption import field_encryption_service

class Client(models.Model):
    firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
    ssn = models.CharField(max_length=255, blank=True)  # Stores encrypted value
    ssn_fingerprint = models.CharField(max_length=64, blank=True)  # For searching
    
    def set_ssn(self, plaintext_ssn):
        """Encrypt and store SSN."""
        self.ssn = field_encryption_service.encrypt_for_firm(
            self.firm_id,
            plaintext_ssn
        )
        self.ssn_fingerprint = field_encryption_service.fingerprint_for_firm(
            self.firm_id,
            plaintext_ssn
        )
    
    def get_ssn(self):
        """Decrypt and return SSN."""
        return field_encryption_service.decrypt_for_firm(
            self.firm_id,
            self.ssn
        )
```

**Search by Encrypted Field:**
```python
# Search using fingerprint (not plaintext)
search_fingerprint = field_encryption_service.fingerprint_for_firm(
    firm_id,
    search_value
)

clients = Client.objects.filter(
    firm=firm,
    ssn_fingerprint=search_fingerprint
)
```

## Migration from Plaintext

**Safe Migration Strategy:**

```python
from django.core.management.base import BaseCommand
from modules.core.encryption import field_encryption_service

class Command(BaseCommand):
    help = 'Migrate SSN field from plaintext to encrypted'
    
    def handle(self, *args, **options):
        clients = Client.objects.filter(ssn__isnull=False).exclude(ssn='')
        
        for client in clients:
            # Check if already encrypted
            if field_encryption_service.is_encrypted(client.ssn):
                continue
            
            # Encrypt plaintext value
            plaintext = client.ssn
            client.ssn = field_encryption_service.encrypt_for_firm(
                client.firm_id,
                plaintext
            )
            client.ssn_fingerprint = field_encryption_service.fingerprint_for_firm(
                client.firm_id,
                plaintext
            )
            client.save(update_fields=['ssn', 'ssn_fingerprint'])
            
            self.stdout.write(f'Encrypted SSN for client {client.id}')
```

## Future Enhancements

### Roadmap

**Q1 2026:**
- [ ] Implement E2EE for documents (SEC-1)
- [ ] Add key rotation automation
- [ ] Enhance encryption metrics dashboard

**Q2 2026:**
- [ ] Public key infrastructure for E2EE sharing
- [ ] Hardware security key support (YubiKey)
- [ ] Post-quantum cryptography evaluation

**Q3 2026:**
- [ ] Shamir's Secret Sharing for key backup
- [ ] Client-managed key API
- [ ] Advanced key escrow options

## References

- AWS KMS Documentation: https://docs.aws.amazon.com/kms/
- Cryptography Library: https://cryptography.io/
- NIST Encryption Standards: https://csrc.nist.gov/projects/cryptographic-standards-and-guidelines
- OWASP Cryptographic Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html

---

**Document Owner:** Security Team  
**Review Frequency:** Quarterly  
**Next Review:** April 2026
