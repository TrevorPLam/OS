# AGENTS.md — AD Sync Module (Active Directory Integration)

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `src/modules/ad_sync/`

## Purpose

Active Directory integration for user provisioning, group sync, and SSO.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | ADSyncConfig, ADSyncRun, ADUser, ADGroup (~471 LOC) |
| `connector.py` | LDAP connection handling |
| `sync_service.py` | User/group synchronization |
| `tasks.py` | Background sync tasks |
| `views.py` | Admin AD management |
| `serializers.py` | AD serializers |

## Domain Model

```
ADSyncConfig (connection settings per firm)
    └── ADSyncRun (sync execution history)
    └── ADUser (synced users)
    └── ADGroup (synced groups)
```

## Key Models

### ADSyncConfig

AD connection configuration:

```python
class ADSyncConfig(models.Model):
    firm: OneToOne[Firm]
    
    # Connection
    server_url: str                   # ldaps://ad.company.com:636
    service_account_dn: str           # CN=ServiceAccount,OU=...
    encrypted_password: str           # Encrypted at rest
    base_dn: str                      # DC=company,DC=com
    
    # Sync settings
    is_enabled: bool
    sync_type: str                    # full, delta
    sync_schedule: str                # manual, hourly, daily, weekly
    
    # Filtering
    ou_filter: str                    # Specific OU to sync
    group_filter: str                 # Only sync users in these groups
    
    # Attribute mapping
    attribute_mapping: JSONField      # AD attr → User field
    
    # Status
    last_sync_at: DateTime
    last_sync_status: str
    last_error: str
```

### ADSyncRun

Sync execution record:

```python
class ADSyncRun(models.Model):
    config: FK[ADSyncConfig]
    
    sync_type: str                    # full, delta
    status: str                       # running, completed, failed
    
    started_at: DateTime
    completed_at: DateTime
    
    # Stats
    users_created: int
    users_updated: int
    users_disabled: int
    groups_synced: int
    errors: int
    
    error_log: JSONField              # Detailed errors
```

### ADUser

Synced AD user:

```python
class ADUser(models.Model):
    config: FK[ADSyncConfig]
    
    # AD identifiers
    object_guid: str                  # Unique AD identifier
    sam_account_name: str             # Login name
    distinguished_name: str           # Full DN
    
    # Synced attributes
    email: str
    first_name: str
    last_name: str
    display_name: str
    department: str
    title: str
    
    # Status
    is_enabled: bool
    last_synced_at: DateTime
    
    # Local user link
    user: FK[User]                    # Linked platform user
```

## LDAP Connector

```python
from modules.ad_sync.connector import ADConnector

connector = ADConnector(config)

# Test connection
result = connector.test_connection()

# Search users
users = connector.search_users(
    base_dn=config.base_dn,
    filter="(objectClass=user)",
    attributes=["sAMAccountName", "mail", "givenName", "sn"],
)

# Search groups
groups = connector.search_groups(
    base_dn=config.base_dn,
    filter="(objectClass=group)",
)
```

## Sync Service

```python
from modules.ad_sync.sync_service import ADSyncService

service = ADSyncService(config)

# Full sync
run = service.full_sync()

# Delta sync (changes since last sync)
run = service.delta_sync()
```

## Sync Flow

```
1. ADSyncConfig configured with connection details
2. Scheduled task triggers sync (or manual)
3. Create ADSyncRun record
4. Connect to AD via LDAPS
5. Query users/groups based on filters
6. For each AD user:
   a. Check if ADUser exists (by object_guid)
   b. Create or update ADUser
   c. Create or update linked User
   d. Handle disabled accounts
7. For each AD group:
   a. Sync group membership
   b. Map to firm roles (if configured)
8. Update ADSyncRun with stats
```

## Attribute Mapping

```json
{
  "email": "mail",
  "first_name": "givenName",
  "last_name": "sn",
  "username": "sAMAccountName",
  "department": "department",
  "title": "title",
  "phone": "telephoneNumber"
}
```

## Group → Role Mapping

```json
{
  "CN=Admins,OU=Groups,DC=company,DC=com": "firm_admin",
  "CN=Staff,OU=Groups,DC=company,DC=com": "staff",
  "CN=Contractors,OU=Groups,DC=company,DC=com": "contractor"
}
```

## Security

1. **LDAPS Required**: Only secure LDAP (port 636)
2. **Service Account**: Dedicated account with read-only access
3. **Password Encryption**: Service account password encrypted at rest
4. **OU Filtering**: Limit sync to specific organizational units

## Dependencies

- **Depends on**: `firm/`, `auth/`
- **Used by**: User provisioning, SSO
- **External**: ldap3 library

## URLs

Admin endpoints (`/api/v1/ad-sync/`):

```
# Configuration
GET        /config/
PUT        /config/
POST       /config/test-connection/

# Sync
POST       /sync/                     # Trigger manual sync
GET        /sync/status/
GET        /sync/runs/
GET        /sync/runs/{id}/

# Users
GET        /users/
GET        /users/{id}/
POST       /users/{id}/link/          # Link to platform user

# Groups
GET        /groups/
PUT        /groups/role-mapping/
```
