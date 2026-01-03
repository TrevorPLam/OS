# External Document Sharing (Task 3.10)

**Status:** COMPLETE ✅  
**Last Updated:** January 1, 2026

---

## Overview

The External Document Sharing system (Task 3.10) enables secure, token-based sharing of documents with external parties without requiring authentication. The system provides comprehensive access control, tracking, and security features including password protection, expiration dates, download limits, and detailed audit logs.

---

## Architecture

### Models

#### 1. ExternalShare

The primary model for managing external document shares.

**Key Features:**
- UUID-based share tokens for secure access
- Password protection with bcrypt hashing
- Expiration dates
- Download limits with tracking
- Revocation with audit trail
- Access type control (view, download, comment)

**Fields:**
- `firm` (ForeignKey): TIER 0 tenant boundary
- `document` (ForeignKey): The document being shared
- `share_token` (UUIDField): Unique secure token (auto-generated)
- `access_type` (CharField): Type of access granted
- `require_password` (BooleanField): Whether password is required
- `password_hash` (CharField): Bcrypt hash of password
- `expires_at` (DateTimeField): Optional expiration date
- `max_downloads` (IntegerField): Optional download limit
- `download_count` (IntegerField): Current download count
- `revoked` (BooleanField): Revocation status
- `revoked_at`, `revoked_by`, `revoke_reason`: Audit trail
- `created_by`, `created_at`, `updated_at`: Standard audit fields

**Methods:**
- `is_active`: Property checking if share is currently valid
- `is_expired`: Check if share has expired
- `is_download_limit_reached`: Check if download limit reached
- `verify_password(password)`: Verify provided password
- `set_password(password)`: Set/update password with bcrypt
- `revoke(user, reason)`: Revoke the share
- `increment_download_count()`: Increment download counter

#### 2. SharePermission

Detailed permission configuration for external shares.

**Key Features:**
- Print and copy control
- Watermark configuration
- IP restrictions
- Email notifications

**Fields:**
- `firm` (ForeignKey): TIER 0 tenant boundary
- `external_share` (OneToOneField): Associated share
- `allow_print` (BooleanField): Allow printing
- `allow_copy` (BooleanField): Allow text copying
- `apply_watermark` (BooleanField): Apply watermark
- `watermark_text` (CharField): Watermark text
- `watermark_settings` (JSONField): Additional watermark config
- `allowed_ip_addresses` (JSONField): IP whitelist
- `notify_on_access` (BooleanField): Send notifications
- `notification_emails` (JSONField): Email addresses to notify

**Methods:**
- `is_ip_allowed(ip_address)`: Check if IP is allowed

#### 3. ShareAccess

Audit logging for all share access attempts.

**Key Features:**
- Tracks successful and failed access attempts
- Records IP address, user agent, and referer
- Supports different action types
- Immutable audit records

**Fields:**
- `firm` (ForeignKey): TIER 0 tenant boundary
- `external_share` (ForeignKey): Associated share
- `action` (CharField): Type of access action
- `success` (BooleanField): Whether access was successful
- `accessed_at` (DateTimeField): When access occurred
- `ip_address` (GenericIPAddressField): Request IP
- `user_agent` (TextField): Browser/client info
- `referer` (TextField): HTTP referer
- `metadata` (JSONField): Additional access data

**Action Types:**
- `view`: Document view
- `download`: Document download
- `failed_password`: Incorrect password
- `failed_expired`: Share expired
- `failed_revoked`: Share revoked
- `failed_limit`: Download limit reached
- `failed_ip`: IP restricted

**Class Method:**
- `log_access(...)`: Convenience method for logging access

---

## API Endpoints

### ExternalShare Endpoints

#### List/Create Shares
```
GET  /api/documents/external-shares/
POST /api/documents/external-shares/
```

**Create Request Body:**
```json
{
  "document": 123,
  "access_type": "download",
  "require_password": true,
  "password": "secret123",
  "expires_at": "2026-12-31T23:59:59Z",
  "max_downloads": 10
}
```

**Response:**
```json
{
  "id": 1,
  "document": 123,
  "document_name": "Contract.pdf",
  "share_token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "share_url": "https://example.com/api/public/shares/a1b2c3d4-e5f6-7890-abcd-ef1234567890/",
  "access_type": "download",
  "require_password": true,
  "expires_at": "2026-12-31T23:59:59Z",
  "max_downloads": 10,
  "download_count": 0,
  "revoked": false,
  "is_active": true,
  "is_expired": false,
  "is_download_limit_reached": false,
  "created_by": 5,
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z"
}
```

#### Get/Update/Delete Share
```
GET    /api/documents/external-shares/{id}/
PUT    /api/documents/external-shares/{id}/
PATCH  /api/documents/external-shares/{id}/
DELETE /api/documents/external-shares/{id}/
```

#### Revoke Share
```
POST /api/documents/external-shares/{id}/revoke/
```

**Request Body:**
```json
{
  "reason": "Security concern"
}
```

#### Get Share Statistics
```
GET /api/documents/external-shares/{id}/statistics/
```

**Response:**
```json
{
  "share_id": 1,
  "share_token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "document_name": "Contract.pdf",
  "statistics": {
    "total_accesses": 25,
    "successful_accesses": 20,
    "failed_accesses": 5,
    "download_count": 8,
    "max_downloads": 10,
    "action_counts": {
      "view": 12,
      "download": 8,
      "failed_password": 5
    }
  },
  "status": {
    "is_active": true,
    "is_expired": false,
    "is_revoked": false,
    "is_download_limit_reached": false
  },
  "recent_activity": [
    {
      "id": 45,
      "action": "download",
      "success": true,
      "accessed_at": "2026-01-01T15:30:00Z",
      "ip_address": "192.168.1.100"
    }
  ]
}
```

### SharePermission Endpoints

```
GET  /api/documents/share-permissions/
POST /api/documents/share-permissions/
GET  /api/documents/share-permissions/{id}/
PUT  /api/documents/share-permissions/{id}/
PATCH /api/documents/share-permissions/{id}/
DELETE /api/documents/share-permissions/{id}/
```

**Create Request Body:**
```json
{
  "external_share": 1,
  "allow_print": true,
  "allow_copy": false,
  "apply_watermark": true,
  "watermark_text": "CONFIDENTIAL",
  "watermark_settings": {
    "opacity": 0.3,
    "position": "center"
  },
  "allowed_ip_addresses": ["192.168.1.0/24"],
  "notify_on_access": true,
  "notification_emails": ["admin@example.com"]
}
```

### ShareAccess Endpoints (Read-Only)

```
GET /api/documents/share-accesses/
GET /api/documents/share-accesses/{id}/
```

---

## Admin Interface

### ExternalShare Admin

**List Display:**
- Document name
- Share token (truncated)
- Access type
- Created by
- Status (Active/Revoked/Expired/Limit Reached)
- Download count
- Created date

**Filters:**
- Access type
- Require password
- Revoked status
- Created date

**Search:**
- Document name
- Share token
- Created by username

**Readonly Fields:**
- Share token
- Download count
- Timestamps
- Revocation fields
- Share URL (clickable link)

**Admin Actions:**
- Revoke selected shares

**Fieldsets:**
1. Document & Token
2. Access Configuration
3. Revocation (collapsible)
4. Audit (collapsible)

### SharePermission Admin

**List Display:**
- External share
- Allow print
- Allow copy
- Apply watermark
- Notify on access

**Filters:**
- Permission flags

**Fieldsets:**
1. External Share
2. Permission Flags
3. Watermark Settings (collapsible)
4. IP Restrictions (collapsible)
5. Notifications (collapsible)
6. Audit (collapsible)

### ShareAccess Admin (Read-Only)

**List Display:**
- External share
- Action
- Success/Failed (color-coded)
- IP address
- Accessed date

**Filters:**
- Action type
- Success status
- Access date

**Features:**
- No add permission (logs are auto-generated)
- No change permission (immutable audit records)
- Search by share token, document name, IP

---

## Security Features

### 1. Token-Based Access

- **UUID4 tokens**: Cryptographically secure random tokens
- **Unique constraint**: Database-enforced uniqueness
- **Auto-generation**: Tokens generated automatically on creation
- **No enumeration**: Tokens are not sequential or guessable

### 2. Password Protection

- **Bcrypt hashing**: Industry-standard password hashing
- **Salt generation**: Automatic salt generation per password
- **Secure verification**: Constant-time password comparison
- **No plain text**: Passwords never stored in plain text

### 3. Access Control

- **Expiration dates**: Time-limited access
- **Download limits**: Prevent excessive downloads
- **Revocation**: Immediate access revocation
- **IP restrictions**: Optional IP whitelist (framework)

### 4. Audit Trail

- **Complete logging**: All access attempts logged
- **Success/failure tracking**: Distinguish between successful and failed attempts
- **IP tracking**: Record IP addresses for security analysis
- **User agent logging**: Track client information
- **Immutable records**: Audit logs cannot be modified or deleted

### 5. Tenant Isolation (TIER 0)

- **Firm scoping**: All models include firm foreign key
- **FirmScopedManager**: Automatic query scoping
- **API scoping**: All endpoints respect firm boundaries
- **Access verification**: get_object() enforces firm access

---

## Usage Examples

### Creating a Simple Share

```python
from modules.documents.models import Document, ExternalShare

# Get document
document = Document.objects.get(pk=123, firm=request.firm)

# Create share
share = ExternalShare.objects.create(
    firm=request.firm,
    document=document,
    access_type="view",
    created_by=request.user
)

# Share URL is: /api/public/shares/{share.share_token}/
```

### Creating a Password-Protected Share with Expiration

```python
from datetime import timedelta
from django.utils import timezone
from modules.documents.models import ExternalShare

share = ExternalShare.objects.create(
    firm=request.firm,
    document=document,
    access_type="download",
    require_password=True,
    expires_at=timezone.now() + timedelta(days=7),
    max_downloads=5,
    created_by=request.user
)

# Set password
share.set_password("secret123")
share.save()
```

### Adding Permissions

```python
from modules.documents.models import SharePermission

permissions = SharePermission.objects.create(
    firm=request.firm,
    external_share=share,
    allow_print=False,
    allow_copy=False,
    apply_watermark=True,
    watermark_text="CONFIDENTIAL",
    notify_on_access=True,
    notification_emails=["admin@example.com"]
)
```

### Logging Access

```python
from modules.documents.models import ShareAccess

# Log successful download
ShareAccess.log_access(
    firm_id=share.firm_id,
    external_share=share,
    action="download",
    success=True,
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT'),
)

# Increment download count
share.increment_download_count()
```

### Checking Share Validity

```python
def can_access_share(share, password=None):
    """Check if share can be accessed."""
    
    # Check if active
    if not share.is_active:
        if share.revoked:
            return False, "Share has been revoked"
        if share.is_expired:
            return False, "Share has expired"
        if share.is_download_limit_reached:
            return False, "Download limit reached"
    
    # Verify password if required
    if share.require_password:
        if not password or not share.verify_password(password):
            return False, "Invalid password"
    
    return True, "Access granted"
```

### Revoking a Share

```python
# Revoke with reason
share.revoke(user=request.user, reason="Security concern")

# Share is now inaccessible
assert not share.is_active
assert share.revoked == True
```

---

## Public Access Endpoint (Tracked in TODO: T-015)

The public access endpoint implementation is tracked in TODO: T-015. The endpoint should be implemented in a separate view that doesn't require authentication:

```python
# In src/api/public/views.py or similar

class PublicShareView(APIView):
    """
    Public endpoint for accessing shared documents.
    
    No authentication required.
    """
    permission_classes = []  # No auth required
    authentication_classes = []
    
    def get(self, request, share_token):
        """
        GET /api/public/shares/{share_token}/
        
        Query params:
        - password: Optional password if share is protected
        """
        try:
            share = ExternalShare.objects.get(share_token=share_token)
        except ExternalShare.DoesNotExist:
            ShareAccess.log_access(
                firm_id=None,  # Unknown firm
                external_share=None,
                action="failed_not_found",
                success=False,
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            return Response({"error": "Share not found"}, status=404)
        
        # Check if share is valid
        if not share.is_active:
            action = "failed_expired" if share.is_expired else \
                     "failed_revoked" if share.revoked else \
                     "failed_limit"
            ShareAccess.log_access(
                firm_id=share.firm_id,
                external_share=share,
                action=action,
                success=False,
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            return Response({"error": "Share is no longer active"}, status=403)
        
        # Check password
        password = request.query_params.get('password')
        if share.require_password:
            if not password or not share.verify_password(password):
                ShareAccess.log_access(
                    firm_id=share.firm_id,
                    external_share=share,
                    action="failed_password",
                    success=False,
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
                return Response({"error": "Invalid password"}, status=401)
        
        # Check permissions (IP restriction)
        if hasattr(share, 'permissions'):
            perms = share.permissions
            ip_address = request.META.get('REMOTE_ADDR')
            if not perms.is_ip_allowed(ip_address):
                ShareAccess.log_access(
                    firm_id=share.firm_id,
                    external_share=share,
                    action="failed_ip",
                    success=False,
                    ip_address=ip_address,
                )
                return Response({"error": "Access denied from this IP"}, status=403)
        
        # Generate download URL
        from modules.documents.services import S3Service
        s3_service = S3Service()
        download_url = s3_service.generate_presigned_url(
            share.document.decrypted_s3_key(),
            bucket=share.document.decrypted_s3_bucket(),
            expiration=3600,
        )
        
        # Log successful access
        ShareAccess.log_access(
            firm_id=share.firm_id,
            external_share=share,
            action="view" if share.access_type == "view" else "download",
            success=True,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
        )
        
        # Increment download count if downloading
        if share.access_type == "download":
            share.increment_download_count()
        
        return Response({
            "document_name": share.document.name,
            "access_type": share.access_type,
            "download_url": download_url,
            "expires_in": 3600,
            "permissions": {
                "allow_print": share.permissions.allow_print if hasattr(share, 'permissions') else True,
                "allow_copy": share.permissions.allow_copy if hasattr(share, 'permissions') else True,
            }
        })
```

---

## Testing

### Unit Tests

```python
import pytest
from django.utils import timezone
from datetime import timedelta
from modules.documents.models import ExternalShare, Document

@pytest.mark.django_db
class TestExternalShare:
    
    def test_create_share(self, firm, document, user):
        """Test creating a basic share."""
        share = ExternalShare.objects.create(
            firm=firm,
            document=document,
            access_type="view",
            created_by=user
        )
        
        assert share.share_token is not None
        assert share.is_active
        assert not share.is_expired
        assert not share.revoked
    
    def test_password_protection(self, share):
        """Test password setting and verification."""
        password = "test123"
        share.set_password(password)
        share.save()
        
        assert share.require_password
        assert share.verify_password(password)
        assert not share.verify_password("wrong")
    
    def test_expiration(self, firm, document, user):
        """Test share expiration."""
        share = ExternalShare.objects.create(
            firm=firm,
            document=document,
            access_type="view",
            expires_at=timezone.now() - timedelta(hours=1),
            created_by=user
        )
        
        assert share.is_expired
        assert not share.is_active
    
    def test_download_limit(self, share):
        """Test download limit tracking."""
        share.max_downloads = 3
        share.save()
        
        # Simulate downloads
        for i in range(3):
            share.increment_download_count()
        
        assert share.download_count == 3
        assert share.is_download_limit_reached
        assert not share.is_active
    
    def test_revocation(self, share, user):
        """Test share revocation."""
        share.revoke(user=user, reason="Test revocation")
        
        assert share.revoked
        assert share.revoked_by == user
        assert share.revoke_reason == "Test revocation"
        assert not share.is_active
```

### Integration Tests

```python
import pytest
from rest_framework.test import APIClient
from rest_framework import status

@pytest.mark.django_db
class TestExternalShareAPI:
    
    def test_create_share(self, api_client, firm, document, user):
        """Test creating share via API."""
        api_client.force_authenticate(user=user)
        
        response = api_client.post('/api/documents/external-shares/', {
            'document': document.id,
            'access_type': 'download',
            'max_downloads': 5
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'share_token' in response.data
        assert 'share_url' in response.data
    
    def test_revoke_share(self, api_client, share, user):
        """Test revoking share via API."""
        api_client.force_authenticate(user=user)
        
        response = api_client.post(
            f'/api/documents/external-shares/{share.id}/revoke/',
            {'reason': 'Security test'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        share.refresh_from_db()
        assert share.revoked
    
    def test_statistics(self, api_client, share, user):
        """Test getting share statistics."""
        api_client.force_authenticate(user=user)
        
        response = api_client.get(
            f'/api/documents/external-shares/{share.id}/statistics/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert 'statistics' in response.data
        assert 'recent_activity' in response.data
```

---

## Related Documentation

- [Documents Module](./documents-module.md)
- [System Invariants](../../spec/SYSTEM_INVARIANTS.md)
- [Data Governance](../../spec/DATA_GOVERNANCE.md)
- [API Usage Guide](./api-usage.md)
- [Security Guidelines](./security-guidelines.md)

---

## Future Enhancements

1. **CIDR Range Support**: Full CIDR notation for IP restrictions
2. **PDF Watermarking**: Server-side PDF watermarking
3. **Email Notifications**: Automatic notification system
4. **Share Templates**: Pre-configured sharing templates
5. **Batch Sharing**: Share multiple documents at once
6. **Share Groups**: Group multiple shares under one token
7. **Analytics Dashboard**: Visual analytics for share usage
8. **Custom Branding**: White-label share pages
9. **2FA Support**: Two-factor authentication for sensitive shares
10. **Rate Limiting**: Per-IP rate limiting for access attempts

---

**End of Documentation**
