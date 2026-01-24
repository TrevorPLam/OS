# Patterns Mappable to OS

**Analysis of which patterns from new apps can be directly applied to OS**

---

## Current OS State

### ✅ What OS Has
- **Django 4.2.17** with REST Framework
- **PostgreSQL** database
- **React 18.3.1** + **Vite 5.4.21** frontend
- **TypeScript 5.9.3** (frontend)
- **Python 3.11** (backend)
- **Multi-tenant architecture** (firm-scoped)
- **Django ORM** for data access
- **Ruff** for Python linting/formatting
- **ESLint** for TypeScript (frontend)
- **JWT Authentication** with refresh tokens
- **OAuth/SAML** support (django-allauth)
- **MFA** support (django-otp)
- **Rate limiting** (django-ratelimit)
- **Factory pattern** for accounting integrations (QuickBooks, Xero)
- **Service layer** pattern (sync services)
- **ViewSets** for API endpoints
- **Serializers** for data validation
- **Governance framework** (`.repo/` structure)
- **Extensive automation scripts** (intelligent, ultra, vibranium)

### ❌ What OS Lacks
- **No repository pattern** (uses Django ORM directly)
- **No factory pattern** for storage providers (S3 only)
- **No factory pattern** for email providers (hardcoded)
- **No factory pattern** for SMS providers (Twilio only)
- **No persistent configuration** (only environment variables)
- **No Biome** (uses ESLint for frontend, Ruff for backend)
- **No GraphQL** (REST API only)

---

## 🎯 High-Priority Mappings

### 1. **Repository Pattern for Django ORM** (from cal.com, adapted)

**Why it fits:**
- Currently uses **Django ORM directly** in ViewSets
- Repository pattern provides **abstraction layer** for data access
- Makes it easier to **test** (mock repository)
- Enables **select optimization** (only fetch needed fields)
- Better **separation of concerns** (business logic vs data access)

**Current State:**
```python
# backend/api/crm/views.py (current)
class LeadViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    model = Lead
    serializer_class = LeadSerializer
    # Django ORM queries happen automatically in ModelViewSet
```

**What to extract:**
```python
# backend/modules/crm/repositories/base.py
from typing import Generic, TypeVar, Optional, List, Dict, Any
from django.db import models

T = TypeVar('T', bound=models.Model)

class BaseRepository(Generic[T]):
    """
    Base repository for Django models.

    Provides type-safe data access with select optimization.
    """

    def __init__(self, model: type[T], firm_id: Optional[int] = None):
        self.model = model
        self.firm_id = firm_id

    def get_queryset(self):
        """Get base queryset, optionally filtered by firm."""
        qs = self.model.objects.all()
        if self.firm_id and hasattr(self.model, 'firm'):
            qs = qs.filter(firm_id=self.firm_id)
        return qs

    def find_by_id(self, id: int, select: Optional[List[str]] = None) -> Optional[T]:
        """Find by primary key with optional field selection."""
        qs = self.get_queryset()
        if select:
            qs = qs.only(*select)
        try:
            return qs.get(pk=id)
        except self.model.DoesNotExist:
            return None

    def find_many(
        self,
        filters: Optional[Dict[str, Any]] = None,
        select: Optional[List[str]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[T]:
        """Find multiple records with filtering and selection."""
        qs = self.get_queryset()

        if filters:
            qs = qs.filter(**filters)

        if select:
            qs = qs.only(*select)

        if order_by:
            qs = qs.order_by(*order_by)

        if limit:
            qs = qs[:limit]

        return list(qs)

    def create(self, data: Dict[str, Any]) -> T:
        """Create a new record."""
        return self.model.objects.create(**data)

    def update(self, id: int, data: Dict[str, Any]) -> T:
        """Update an existing record."""
        instance = self.find_by_id(id)
        if not instance:
            raise self.model.DoesNotExist(f"{self.model.__name__} with id={id} not found")

        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, id: int) -> bool:
        """Delete a record."""
        instance = self.find_by_id(id)
        if not instance:
            return False
        instance.delete()
        return True

# backend/modules/crm/repositories/lead_repository.py
from modules.crm.models import Lead
from modules.crm.repositories.base import BaseRepository

class LeadRepository(BaseRepository[Lead]):
    """Repository for Lead model with CRM-specific methods."""

    def __init__(self, firm_id: Optional[int] = None):
        super().__init__(Lead, firm_id)

    def find_by_status(self, status: str, select: Optional[List[str]] = None) -> List[Lead]:
        """Find leads by status."""
        return self.find_many(
            filters={'status': status},
            select=select or ['id', 'company_name', 'contact_name', 'status', 'created_at'],
        )

    def find_by_source(self, source: str, select: Optional[List[str]] = None) -> List[Lead]:
        """Find leads by source."""
        return self.find_many(
            filters={'source': source},
            select=select or ['id', 'company_name', 'contact_name', 'source', 'created_at'],
        )
```

**Implementation Steps:**
1. Create `backend/modules/*/repositories/` directories
2. Add base repository class
3. Create module-specific repositories (CRM, Finance, Projects, etc.)
4. Refactor ViewSets to use repositories
5. Add tests for repositories
6. Document pattern

**Files to create:**
- `backend/modules/crm/repositories/base.py`
- `backend/modules/crm/repositories/lead_repository.py`
- `backend/modules/crm/repositories/prospect_repository.py`
- `backend/modules/finance/repositories/invoice_repository.py`
- `backend/modules/projects/repositories/project_repository.py`
- `tests/modules/crm/repositories/test_lead_repository.py`
- `docs/patterns/repository-pattern.md`

**Files to modify:**
- `backend/api/crm/views.py` (use repositories)
- `backend/api/finance/views.py` (use repositories)
- `backend/api/projects/views.py` (use repositories)

**Benefits:**
- ✅ Type-safe data access
- ✅ Easier testing (mock repository)
- ✅ Select optimization (only fetch needed fields)
- ✅ Better separation of concerns
- ✅ Consistent patterns across modules

---

### 2. **Factory Pattern for Storage Providers** (from omni-storage)

**Why it fits:**
- Currently uses **S3 only** (via django-storages)
- Might want to switch to **GCS**, **Azure Blob**, or **local storage**
- Factory pattern enables **easy storage switching**
- Reduces vendor lock-in

**Current State:**
```python
# backend/config/settings.py (current)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
```

**What to extract:**
```python
# backend/modules/documents/storage/base.py
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional

class StorageProvider(ABC):
    """Abstract base class for storage providers."""

    @abstractmethod
    def upload(self, key: str, file: BinaryIO, content_type: Optional[str] = None) -> str:
        """Upload a file and return its URL."""
        pass

    @abstractmethod
    def download(self, key: str) -> BinaryIO:
        """Download a file by key."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a file by key."""
        pass

    @abstractmethod
    def get_url(self, key: str, expires_in: Optional[int] = None) -> str:
        """Get a signed URL for a file."""
        pass

# backend/modules/documents/storage/factory.py
from modules.documents.storage.base import StorageProvider
from modules.documents.storage.s3 import S3StorageProvider
from modules.documents.storage.gcs import GCSStorageProvider
from modules.documents.storage.local import LocalStorageProvider

class StorageProviderFactory:
    """Factory for creating storage providers."""

    @staticmethod
    def create(provider: str, config: dict) -> StorageProvider:
        """Create a storage provider instance."""
        if provider == 's3':
            return S3StorageProvider(config)
        elif provider == 'gcs':
            return GCSStorageProvider(config)
        elif provider == 'local':
            return LocalStorageProvider(config)
        else:
            raise ValueError(f"Unknown storage provider: {provider}")

    @staticmethod
    def create_from_settings() -> StorageProvider:
        """Create storage provider from Django settings."""
        provider = os.environ.get('STORAGE_PROVIDER', 's3')
        config = {
            'bucket_name': os.environ.get('AWS_STORAGE_BUCKET_NAME'),
            'access_key': os.environ.get('AWS_ACCESS_KEY_ID'),
            'secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
            'region': os.environ.get('AWS_REGION', 'us-east-1'),
        }
        return StorageProviderFactory.create(provider, config)

# backend/modules/documents/storage/s3.py
import boto3
from botocore.exceptions import ClientError
from modules.documents.storage.base import StorageProvider

class S3StorageProvider(StorageProvider):
    """S3 storage provider implementation."""

    def __init__(self, config: dict):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config['access_key'],
            aws_secret_access_key=config['secret_key'],
            region_name=config['region'],
        )
        self.bucket_name = config['bucket_name']

    def upload(self, key: str, file: BinaryIO, content_type: Optional[str] = None) -> str:
        """Upload to S3."""
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        self.s3_client.upload_fileobj(file, self.bucket_name, key, ExtraArgs=extra_args)
        return f"s3://{self.bucket_name}/{key}"

    # ... other methods
```

**Implementation Steps:**
1. Create `backend/modules/documents/storage/` directory
2. Define `StorageProvider` interface
3. Create factory class
4. Refactor S3 logic into `S3StorageProvider`
5. Update document views to use factory
6. Add environment variable for storage selection
7. Document pattern

**Files to create:**
- `backend/modules/documents/storage/base.py`
- `backend/modules/documents/storage/factory.py`
- `backend/modules/documents/storage/s3.py`
- `backend/modules/documents/storage/gcs.py` (example, optional)
- `backend/modules/documents/storage/local.py` (example, optional)
- `docs/patterns/storage-provider-factory.md`

**Files to modify:**
- `backend/modules/documents/views.py` (use factory)
- `backend/config/settings.py` (remove hardcoded S3 config)
- `env.example` (add STORAGE_PROVIDER)

**Benefits:**
- ✅ Easy to switch storage backends
- ✅ Reduces vendor lock-in
- ✅ Consistent interface across providers
- ✅ Easier to test (mock storage)
- ✅ Can support multiple providers simultaneously

---

### 3. **Factory Pattern for Email Providers** (from esperanto pattern)

**Why it fits:**
- Currently uses **hardcoded email backend** (Django's default)
- Might want to switch to **SendGrid**, **Resend**, **AWS SES**, or **Mailgun**
- Factory pattern enables **easy provider switching**
- Reduces vendor lock-in

**What to extract:**
```python
# backend/modules/communications/email/base.py
from abc import ABC, abstractmethod
from typing import List, Optional

class EmailProvider(ABC):
    """Abstract base class for email providers."""

    @abstractmethod
    def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        html: Optional[str] = None,
    ) -> bool:
        """Send an email."""
        pass

    @abstractmethod
    def send_template(
        self,
        to: List[str],
        template_id: str,
        template_data: dict,
        from_email: Optional[str] = None,
    ) -> bool:
        """Send an email using a template."""
        pass

# backend/modules/communications/email/factory.py
from modules.communications.email.base import EmailProvider
from modules.communications.email.sendgrid import SendGridProvider
from modules.communications.email.resend import ResendProvider
from modules.communications.email.ses import SESProvider

class EmailProviderFactory:
    """Factory for creating email providers."""

    @staticmethod
    def create(provider: str, config: dict) -> EmailProvider:
        """Create an email provider instance."""
        if provider == 'sendgrid':
            return SendGridProvider(config)
        elif provider == 'resend':
            return ResendProvider(config)
        elif provider == 'ses':
            return SESProvider(config)
        else:
            raise ValueError(f"Unknown email provider: {provider}")

    @staticmethod
    def create_from_settings() -> EmailProvider:
        """Create email provider from Django settings."""
        provider = os.environ.get('EMAIL_PROVIDER', 'sendgrid')
        config = {
            'api_key': os.environ.get('EMAIL_API_KEY'),
            'from_email': os.environ.get('EMAIL_FROM', 'noreply@example.com'),
        }
        return EmailProviderFactory.create(provider, config)
```

**Implementation Steps:**
1. Create `backend/modules/communications/email/` directory
2. Define `EmailProvider` interface
3. Create factory class
4. Implement providers (SendGrid, Resend, SES)
5. Update email sending code to use factory
6. Add environment variable for provider selection
7. Document pattern

**Files to create:**
- `backend/modules/communications/email/base.py`
- `backend/modules/communications/email/factory.py`
- `backend/modules/communications/email/sendgrid.py`
- `backend/modules/communications/email/resend.py`
- `backend/modules/communications/email/ses.py`
- `docs/patterns/email-provider-factory.md`

**Files to modify:**
- `backend/modules/communications/views.py` (use factory)
- `env.example` (add EMAIL_PROVIDER)

**Benefits:**
- ✅ Easy to switch email providers
- ✅ Reduces vendor lock-in
- ✅ Consistent interface across providers
- ✅ Easier to test (mock email provider)

---

### 4. **Factory Pattern for SMS Providers** (from esperanto pattern)

**Why it fits:**
- Currently uses **Twilio only** (in `modules/sms/`)
- Might want to switch to **AWS SNS**, **Vonage**, or **MessageBird**
- Factory pattern enables **easy provider switching**
- Reduces vendor lock-in

**What to extract:**
```python
# backend/modules/sms/providers/base.py
from abc import ABC, abstractmethod
from typing import List, Optional

class SMSProvider(ABC):
    """Abstract base class for SMS providers."""

    @abstractmethod
    def send(
        self,
        to: str,
        message: str,
        from_number: Optional[str] = None,
    ) -> bool:
        """Send an SMS."""
        pass

    @abstractmethod
    def send_bulk(
        self,
        to: List[str],
        message: str,
        from_number: Optional[str] = None,
    ) -> dict:
        """Send bulk SMS."""
        pass

# backend/modules/sms/providers/factory.py
from modules.sms.providers.base import SMSProvider
from modules.sms.providers.twilio import TwilioProvider
from modules.sms.providers.sns import SNSProvider
from modules.sms.providers.vonage import VonageProvider

class SMSProviderFactory:
    """Factory for creating SMS providers."""

    @staticmethod
    def create(provider: str, config: dict) -> SMSProvider:
        """Create an SMS provider instance."""
        if provider == 'twilio':
            return TwilioProvider(config)
        elif provider == 'sns':
            return SNSProvider(config)
        elif provider == 'vonage':
            return VonageProvider(config)
        else:
            raise ValueError(f"Unknown SMS provider: {provider}")

    @staticmethod
    def create_from_settings() -> SMSProvider:
        """Create SMS provider from Django settings."""
        provider = os.environ.get('SMS_PROVIDER', 'twilio')
        config = {
            'account_sid': os.environ.get('TWILIO_ACCOUNT_SID'),
            'auth_token': os.environ.get('TWILIO_AUTH_TOKEN'),
            'from_number': os.environ.get('TWILIO_FROM_NUMBER'),
        }
        return SMSProviderFactory.create(provider, config)
```

**Implementation Steps:**
1. Create `backend/modules/sms/providers/` directory
2. Define `SMSProvider` interface
3. Create factory class
4. Refactor Twilio logic into `TwilioProvider`
5. Update SMS views to use factory
6. Add environment variable for provider selection
7. Document pattern

**Files to create:**
- `backend/modules/sms/providers/base.py`
- `backend/modules/sms/providers/factory.py`
- `backend/modules/sms/providers/twilio.py`
- `backend/modules/sms/providers/sns.py` (example, optional)
- `docs/patterns/sms-provider-factory.md`

**Files to modify:**
- `backend/modules/sms/views.py` (use factory)
- `env.example` (add SMS_PROVIDER)

**Benefits:**
- ✅ Easy to switch SMS providers
- ✅ Reduces vendor lock-in
- ✅ Consistent interface across providers
- ✅ Easier to test (mock SMS provider)

---

### 5. **Persistent Configuration** (from open-webui)

**Why it fits:**
- Currently uses **environment variables only**
- Some config should be **user-editable** (firm settings, default values)
- Database-backed config allows **runtime changes** without redeployment
- Falls back to environment variables (backward compatible)

**What to extract:**
```python
# backend/modules/core/config/persistent_config.py
from typing import TypeVar, Optional, Type
from django.db import models
from django.core.cache import cache

T = TypeVar('T')

class PersistentConfig:
    """Persistent configuration with environment variable fallback."""

    def __init__(
        self,
        key: str,
        env_name: str,
        default_value: T,
        value_type: Type[T] = str,
    ):
        self.key = key
        self.env_name = env_name
        self.default_value = default_value
        self.value_type = value_type

    def get(self) -> T:
        """Get configuration value (database first, then env, then default)."""
        # Try database
        from modules.core.models import ConfigSetting
        try:
            setting = ConfigSetting.objects.get(key=self.key)
            return self._cast_value(setting.value)
        except ConfigSetting.DoesNotExist:
            pass

        # Try environment variable
        env_value = os.environ.get(self.env_name)
        if env_value:
            return self._cast_value(env_value)

        # Return default
        return self.default_value

    def set(self, value: T) -> None:
        """Set configuration value in database."""
        from modules.core.models import ConfigSetting
        ConfigSetting.objects.update_or_create(
            key=self.key,
            defaults={'value': str(value)},
        )
        cache.delete(f'config:{self.key}')

    def _cast_value(self, value: str) -> T:
        """Cast value to correct type."""
        if self.value_type == bool:
            return value.lower() in ('true', '1', 'yes')
        elif self.value_type == int:
            return int(value)
        elif self.value_type == float:
            return float(value)
        else:
            return value

# Usage
DEFAULT_CURRENCY = PersistentConfig(
    'firm.default_currency',
    'DEFAULT_CURRENCY',
    'USD',
)

MAX_PROJECTS_PER_CLIENT = PersistentConfig(
    'firm.max_projects_per_client',
    'MAX_PROJECTS_PER_CLIENT',
    10,
    int,
)
```

**Implementation Steps:**
1. Create `ConfigSetting` model in `modules/core/models.py`
2. Create `PersistentConfig` class
3. Migrate existing env vars to PersistentConfig where appropriate
4. Add config management API (optional)
5. Document usage

**Files to create:**
- `backend/modules/core/config/persistent_config.py`
- `backend/modules/core/models.py` (add ConfigSetting)
- `backend/api/config/views.py` (API for config management)
- `docs/patterns/persistent-config.md`

**Benefits:**
- ✅ Runtime configuration changes
- ✅ User-editable settings
- ✅ Environment variable fallback
- ✅ Type-safe configuration

---

### 6. **Biome Configuration for Frontend** (from cal.com)

**Why it fits:**
- Currently uses **ESLint** for TypeScript/React
- Biome is a **unified tool** that replaces ESLint + Prettier
- Better performance and simpler configuration
- Already TypeScript-focused

**What to extract:**
```json
// frontend/biome.json
{
  "formatter": {
    "lineWidth": 100,
    "indentStyle": "space",
    "indentWidth": 2
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "nursery": {
        "noUnresolvedImports": "warn"
      }
    }
  },
  "overrides": [
    {
      "includes": ["src/**/*.tsx", "src/**/*.ts"],
      "linter": {
        "rules": {
          "style": {
            "noDefaultExport": "off"
          }
        }
      }
    }
  ]
}
```

**Implementation Steps:**
1. Install Biome: `npm install --save-dev @biomejs/biome`
2. Replace ESLint config with `biome.json`
3. Update `package.json` scripts
4. Remove ESLint dependencies

**Files to modify:**
- `frontend/package.json` (scripts, dependencies)
- `frontend/.eslintrc.json` → `frontend/biome.json` (replace)
- `.lintstagedrc.json` (update to use Biome)

**Benefits:**
- ✅ Single tool instead of ESLint
- ✅ Faster linting/formatting
- ✅ Better TypeScript support
- ✅ Simpler configuration

---

## 🟡 Medium-Priority Mappings

### 7. **GraphQL Setup** (from hoppscotch)

**Why it fits:**
- OS might add **complex queries** (sessions, repositories, filtering)
- Better for **client portal** (flexible data fetching)
- Can expose **public API** for integrations

**When to implement:**
- When adding complex queries
- When exposing public API
- When client portal needs flexible data fetching

---

## 🔴 Low-Priority Mappings

### 8. **Plugin System** (from eliza)

**Why it's low priority:**
- OS is an **application**, not a framework
- Plugin system adds **complexity**
- Most users won't need extensibility

**When to implement:**
- If OS becomes a framework
- If users request plugin support

---

## Implementation Roadmap

### Phase 1: Foundation (1-2 weeks)
1. ✅ **Repository Pattern for Django ORM**
   - Create base repository
   - Refactor CRM, Finance, Projects modules
   - Add tests
   - Document pattern

2. ✅ **Biome Configuration for Frontend**
   - Replace ESLint
   - Update scripts
   - Test linting/formatting

### Phase 2: Provider Abstraction (2-3 weeks)
3. ✅ **Factory Pattern for Storage Providers**
   - Create storage provider interface
   - Refactor S3 to provider
   - Add factory
   - Document pattern

4. ✅ **Factory Pattern for Email Providers**
   - Create email provider interface
   - Implement providers (SendGrid, Resend, SES)
   - Add factory
   - Document pattern

5. ✅ **Factory Pattern for SMS Providers**
   - Create SMS provider interface
   - Refactor Twilio to provider
   - Add factory
   - Document pattern

### Phase 3: Enhancement (1 week)
6. ✅ **Persistent Configuration**
   - Add ConfigSetting model
   - Create PersistentConfig class
   - Add API routes
   - Document usage

### Phase 4: Future (as needed)
7. ⏳ **GraphQL** (when needed)
8. ⏳ **Plugin System** (if becomes framework)

---

## Summary

### Immediate Actions
1. **Add repository pattern for Django ORM** (foundation for data access)
2. **Add factory pattern for storage providers** (enables multi-provider support)
3. **Add factory pattern for email providers** (enables multi-provider support)
4. **Add factory pattern for SMS providers** (enables multi-provider support)
5. **Replace ESLint with Biome** (frontend only, quick win)

### Future Considerations
- Persistent configuration when adding user-editable settings
- GraphQL when adding complex queries
- Plugin system if application becomes framework

---

## Files to Create/Modify

### New Files
```
backend/modules/
├── crm/
│   └── repositories/
│       ├── base.py
│       ├── lead_repository.py
│       └── prospect_repository.py
├── finance/
│   └── repositories/
│       └── invoice_repository.py
├── documents/
│   └── storage/
│       ├── base.py
│       ├── factory.py
│       └── s3.py
├── communications/
│   └── email/
│       ├── base.py
│       ├── factory.py
│       └── sendgrid.py
├── sms/
│   └── providers/
│       ├── base.py
│       ├── factory.py
│       └── twilio.py
└── core/
    ├── models.py (add ConfigSetting)
    └── config/
        └── persistent_config.py

frontend/
└── biome.json

docs/
└── patterns/
    ├── repository-pattern.md
    ├── factory-pattern.md
    └── persistent-config.md
```

### Modified Files
```
backend/api/crm/views.py (use repositories)
backend/api/finance/views.py (use repositories)
backend/api/projects/views.py (use repositories)
backend/modules/documents/views.py (use storage factory)
backend/modules/communications/views.py (use email factory)
backend/modules/sms/views.py (use SMS factory)
backend/config/settings.py (remove hardcoded configs)
frontend/package.json (scripts, dependencies)
frontend/.eslintrc.json → frontend/biome.json (replace)
env.example (add STORAGE_PROVIDER, EMAIL_PROVIDER, SMS_PROVIDER)
```

---

## Key Differences from Other Templates

1. **Django ORM**
   - Repository pattern adapted for Django ORM (not Prisma/Drizzle)
   - Uses Django's `only()` and `select_related()` for optimization

2. **Multi-tenant Architecture**
   - Repository pattern must respect firm-scoped queries
   - Factory patterns must support per-firm configuration

3. **Python Backend**
   - Uses Ruff (not Biome) for Python linting
   - Uses type hints and generics for type safety

4. **Existing Factory Patterns**
   - Already has factory pattern for accounting integrations
   - Can extend this pattern to other providers

5. **Service Layer**
   - Already has service layer pattern (sync services)
   - Repository pattern complements service layer

---

**Last Updated:** 2024-12-19
**Target:** OS
**Source Repositories:** cal.com, esperanto, omni-storage, open-webui, hoppscotch
