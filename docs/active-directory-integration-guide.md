# Active Directory Integration Guide

**Last Updated:** January 2, 2026  
**Feature:** Active Directory User Synchronization (AD-1 through AD-5)  
**Priority:** HIGH - Deal-breaker for enterprise customers

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Scheduled Synchronization](#scheduled-synchronization)
- [Provisioning Rules](#provisioning-rules)
- [Group Mapping](#group-mapping)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Active Directory (AD) integration enables enterprise customers to:
- Automatically sync users from their on-premises or Azure Active Directory
- Map AD groups to platform roles
- Apply custom provisioning rules for user creation
- Schedule automatic synchronization (hourly, daily, weekly)
- Maintain AD-managed user accounts

This implementation uses **LDAPS (LDAP over TLS)** for secure communication with Active Directory.

---

## Features

### ✅ AD-1: Organizational Unit Sync
- Connect to AD via LDAPS (port 636)
- Sync users from specific OUs
- OU selection and filtering
- Group membership tracking

### ✅ AD-2: Attribute Mapping
- Map AD fields (mail, UPN, GUID) to user fields
- Custom attribute mapping configuration
- Conflict detection for duplicate users
- Flexible transformation rules

### ✅ AD-3: Provisioning Rules Engine
- Rules-based user provisioning system
- Condition-based user creation
- Automatic role assignment rules
- Auto-disable rules for deactivated AD accounts

### ✅ AD-4: Scheduled Synchronization
- Cron-based sync jobs (hourly, daily, weekly)
- Manual on-demand sync capability
- Delta/incremental sync (only changed users)
- Full sync option

### ✅ AD-5: Group Sync
- Sync AD security groups as distribution groups
- Group member synchronization
- Handle large groups (up to 2,000 users with pagination)
- Auto-update group membership

---

## Configuration

### Prerequisites

1. **AD Service Account** with read permissions
   - Create a service account in AD with read-only access
   - Grant access to specific OUs you want to sync
   - Note the Distinguished Name (DN)

2. **LDAPS Certificate**
   - Ensure your AD server has a valid SSL/TLS certificate
   - LDAPS must be enabled on port 636

3. **Network Access**
   - Ensure the application server can reach AD on port 636
   - Configure firewall rules if necessary

### Creating AD Sync Configuration

#### Via Django Admin

1. Navigate to **Admin** → **AD Sync** → **AD Sync Configurations**
2. Click **Add AD Sync Configuration**
3. Fill in the required fields:
   - **Firm**: Select the firm to configure
   - **Server URL**: `ldaps://ad.company.com:636`
   - **Service Account DN**: `CN=ServiceAccount,OU=Service Accounts,DC=company,DC=com`
   - **Encrypted Password**: Service account password (will be encrypted)
   - **Base DN**: `DC=company,DC=com`
   - **OU Filter** (optional): `OU=Employees,DC=company,DC=com`
4. Configure sync settings:
   - **Is Enabled**: Check to enable sync
   - **Sync Type**: `delta` (recommended) or `full`
   - **Sync Schedule**: `daily`, `hourly`, `weekly`, or `manual`
   - **Auto Disable Users**: Check to auto-disable users when AD account is disabled
5. **Save** the configuration

#### Via API

```bash
# Test connection first
curl -X POST https://api.example.com/api/v1/ad-sync/configs/test_connection/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "ldaps://ad.company.com:636",
    "service_account_dn": "CN=ServiceAccount,OU=Service Accounts,DC=company,DC=com",
    "password": "service_account_password",
    "base_dn": "DC=company,DC=com"
  }'

# Create configuration
curl -X POST https://api.example.com/api/v1/ad-sync/configs/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "firm": 1,
    "server_url": "ldaps://ad.company.com:636",
    "service_account_dn": "CN=ServiceAccount,OU=Service Accounts,DC=company,DC=com",
    "encrypted_password": "service_account_password",
    "base_dn": "DC=company,DC=com",
    "ou_filter": "OU=Employees,DC=company,DC=com",
    "is_enabled": true,
    "sync_type": "delta",
    "sync_schedule": "daily",
    "auto_disable_users": true
  }'
```

---

## API Endpoints

### Configurations

- `GET /api/v1/ad-sync/configs/` - List all configurations
- `GET /api/v1/ad-sync/configs/{id}/` - Get configuration details
- `POST /api/v1/ad-sync/configs/` - Create new configuration
- `PUT /api/v1/ad-sync/configs/{id}/` - Update configuration
- `DELETE /api/v1/ad-sync/configs/{id}/` - Delete configuration

### Sync Operations

- `POST /api/v1/ad-sync/configs/{id}/trigger_sync/` - Trigger manual sync
  ```json
  {
    "sync_type": "manual"  // or "full" or "delta"
  }
  ```

- `POST /api/v1/ad-sync/configs/test_connection/` - Test AD connection

### Sync Logs

- `GET /api/v1/ad-sync/logs/` - List sync history
- `GET /api/v1/ad-sync/logs/{id}/` - Get sync log details

### Provisioning Rules

- `GET /api/v1/ad-sync/rules/` - List provisioning rules
- `POST /api/v1/ad-sync/rules/` - Create provisioning rule
- `PUT /api/v1/ad-sync/rules/{id}/` - Update provisioning rule
- `DELETE /api/v1/ad-sync/rules/{id}/` - Delete provisioning rule

### Group Mappings

- `GET /api/v1/ad-sync/groups/` - List group mappings
- `POST /api/v1/ad-sync/groups/` - Create group mapping
- `PUT /api/v1/ad-sync/groups/{id}/` - Update group mapping
- `DELETE /api/v1/ad-sync/groups/{id}/` - Delete group mapping

### User Mappings

- `GET /api/v1/ad-sync/users/` - List AD user mappings
- `GET /api/v1/ad-sync/users/{id}/` - Get user mapping details

---

## Scheduled Synchronization

### Using Cron

Add to your crontab:

```bash
# Hourly sync (every hour at minute 5)
5 * * * * /path/to/scripts/sync_ad_cron.sh hourly

# Daily sync (every day at 2 AM)
0 2 * * * /path/to/scripts/sync_ad_cron.sh daily

# Weekly sync (every Sunday at 3 AM)
0 3 * * 0 /path/to/scripts/sync_ad_cron.sh weekly
```

### Manual Sync via Management Command

```bash
# Sync all firms with scheduled sync
python manage.py sync_ad

# Sync specific firm (full sync)
python manage.py sync_ad --firm-id 1 --full

# Sync specific firm (delta sync)
python manage.py sync_ad --firm-id 1 --delta
```

---

## Provisioning Rules

Provisioning rules control how users are created and assigned roles when synced from AD.

### Rule Types

#### 1. AD Group Membership
Assign roles based on AD group membership:

```json
{
  "name": "Assign Manager Role to Managers Group",
  "condition_type": "ad_group",
  "condition_value": {
    "group_dn": "CN=Managers,OU=Groups,DC=company,DC=com"
  },
  "action_type": "assign_role",
  "action_value": {
    "role": "manager"
  },
  "priority": 100
}
```

#### 2. OU Path Match
Assign roles based on OU location:

```json
{
  "name": "Assign Staff Role to Employees OU",
  "condition_type": "ou_path",
  "condition_value": {
    "ou_path": "OU=Employees"
  },
  "action_type": "assign_role",
  "action_value": {
    "role": "staff"
  },
  "priority": 200
}
```

#### 3. Attribute Value Match
Assign roles based on AD attribute values:

```json
{
  "name": "Assign Billing Role by Department",
  "condition_type": "attribute_value",
  "condition_value": {
    "attribute": "department",
    "value": "Accounting"
  },
  "action_type": "assign_role",
  "action_value": {
    "role": "billing"
  },
  "priority": 150
}
```

### Rule Priority

Rules are evaluated in order of priority (lower number = higher priority).
The first matching rule is applied.

---

## Group Mapping

Map AD security groups to platform roles for automatic assignment.

### Example

```json
{
  "ad_group_dn": "CN=Developers,OU=Groups,DC=company,DC=com",
  "ad_group_name": "Developers",
  "is_enabled": true,
  "sync_members": true,
  "assign_role": "staff"
}
```

When group sync runs, all members of the "Developers" AD group will be assigned the "staff" role.

---

## Security

### Best Practices

1. **Use LDAPS** - Always use LDAPS (port 636) for encrypted communication
2. **Read-Only Service Account** - Create a dedicated read-only AD service account
3. **Least Privilege** - Grant access only to specific OUs needed
4. **Strong Passwords** - Use strong passwords for service accounts
5. **Regular Rotation** - Rotate service account passwords quarterly
6. **Audit Logs** - All AD queries are logged for security audit trail
7. **IP Whitelisting** - Restrict LDAPS access to known application IPs

### Password Encryption

AD service account passwords are encrypted at rest using Fernet symmetric encryption with Django's SECRET_KEY.

---

## Troubleshooting

### Connection Issues

**Error:** `Connection refused` or `Timeout`
- **Solution:** Check firewall rules, ensure LDAPS port 636 is open

**Error:** `SSL certificate verification failed`
- **Solution:** Ensure AD server has valid SSL certificate, or use `verify_ssl=False` for testing only

### Sync Issues

**Error:** `No users found`
- **Solution:** Check OU filter, ensure service account has read permissions

**Error:** `User skipped - missing email`
- **Solution:** Ensure users in AD have email addresses populated

**Error:** `Duplicate user`
- **Solution:** Check for existing users with same email, use conflict resolution

### Performance Issues

**Problem:** Sync takes too long
- **Solution:** Use delta sync instead of full sync
- **Solution:** Adjust OU filter to sync only necessary OUs
- **Solution:** Check network latency between app server and AD

---

## Support

For issues or questions about AD integration:
1. Check sync logs in Django admin
2. Review error messages in application logs
3. Verify AD connection using test connection endpoint
4. Contact support with sync log ID for assistance

---

**Implementation Notes:**
- Based on ldap3 library (pure Python, actively maintained)
- Supports Active Directory, Azure AD (with Azure AD Connect), OpenLDAP
- Tested with AD domains up to 10,000+ users
- Delta sync uses AD's `whenChanged` attribute for efficiency
