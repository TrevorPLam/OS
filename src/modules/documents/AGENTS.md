# AGENTS.md — Documents Module (Document Management)

Last Updated: 2026-01-06
Applies To: `src/modules/documents/`

## Purpose

S3-backed document storage with versioning, encryption, client portal sharing, and malware scanning.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | Folder, Document, DocumentVersion, DocumentShare, FileRequest (~2387 LOC) |
| `services.py` | Document upload/download, S3 operations |
| `malware_scan.py` | Virus scanning integration |
| `reconciliation.py` | S3 ↔ DB consistency checks |
| `permissions.py` | Document access controls |

## Domain Model

```
Folder (hierarchical)
    └── Document
            └── DocumentVersion (immutable versions)
            └── DocumentShare (portal sharing)
            └── FileRequest (request uploads from clients)
```

## Key Models

### Folder

Hierarchical folder structure:

```python
class Folder(models.Model):
    firm: FK[Firm]
    client: FK[Client]
    project: FK[Project]              # Optional
    parent: FK[Folder]                # Self-referential
    
    name: str
    visibility: str                   # internal, client
```

### Document

Core document entity:

```python
class Document(models.Model):
    firm: FK[Firm]
    folder: FK[Folder]
    
    name: str
    description: str
    mime_type: str
    
    # S3 storage
    s3_bucket: str
    s3_key: str
    
    # Security
    is_encrypted: bool
    encryption_key_id: str            # KMS key reference
    
    # Scanning
    scan_status: str                  # pending, clean, infected, error
    scanned_at: DateTime
```

### DocumentVersion

Immutable version history:

```python
class DocumentVersion(models.Model):
    document: FK[Document]
    version_number: int
    
    s3_key: str                       # Version-specific S3 key
    file_size: int
    checksum: str                     # SHA-256
    
    uploaded_by: FK[User]
    uploaded_at: DateTime
    
    # Immutable after creation
```

### DocumentShare

Portal sharing:

```python
class DocumentShare(models.Model):
    document: FK[Document]
    
    share_type: str                   # link, email
    access_code: str                  # Hashed access code
    expires_at: DateTime
    
    # Tracking
    access_count: int
    last_accessed_at: DateTime
```

### FileRequest

Request files from clients:

```python
class FileRequest(models.Model):
    firm: FK[Firm]
    client: FK[Client]
    
    title: str
    description: str
    due_date: Date
    
    status: str                       # pending, partial, complete
    requested_files: JSONField        # List of requested file types
```

## Security Features

### 1. Encryption at Rest

All documents encrypted with firm-specific KMS keys:

```python
from modules.core.encryption import field_encryption_service

# Upload flow
encrypted_content = field_encryption_service.encrypt(content, firm.kms_key_id)
s3_client.upload(encrypted_content)

# Download flow
encrypted_content = s3_client.download(s3_key)
content = field_encryption_service.decrypt(encrypted_content, firm.kms_key_id)
```

### 2. Malware Scanning

All uploads scanned before storage:

```python
from modules.documents.malware_scan import scan_document

result = scan_document(file_content)
if result.is_infected:
    raise MalwareDetectedError(result.threat_name)
```

### 3. Access Control

```python
# Staff: Full access to firm documents
# Portal users: Only documents with visibility='client' in their folders
# Share links: Time-limited, access-code protected
```

## S3 Structure

```
s3://bucket-name/
└── firms/
    └── {firm_id}/
        └── documents/
            └── {document_id}/
                └── v{version}/
                    └── {filename}
```

## Dependencies

- **Depends on**: `firm/`, `clients/`, `projects/`, `core/`
- **Used by**: Client portal, project views
- **External**: boto3 (S3), ClamAV (scanning)

## URLs

Staff endpoints (`/api/v1/documents/`):
```
GET/POST   /folders/
GET/PUT    /folders/{id}/

GET/POST   /documents/
GET/PUT    /documents/{id}/
GET        /documents/{id}/download/
POST       /documents/{id}/share/
GET        /documents/{id}/versions/

GET/POST   /file-requests/
GET        /file-requests/{id}/
```

Portal endpoints (`/api/v1/portal/`):
```
GET        /documents/                    # Client's visible documents
GET        /documents/{id}/download/
POST       /file-requests/{id}/upload/    # Upload requested files
```

Public endpoints (`/api/v1/public/`):
```
GET        /shares/{token}/               # Access shared document
POST       /file-requests/{token}/upload/ # Upload via public link
```
