# Active Directory Integration Research

**Status:** Research Complete  
**Date:** January 2, 2026  
**Related Features:** Active Directory Integration (AD-1 through AD-5)  
**Priority:** HIGH (Deal-breaker for enterprise customers)

## Executive Summary

This document evaluates options for implementing Active Directory (AD) integration to enable enterprise user provisioning, synchronization, and authentication. AD integration is a critical requirement for enterprise customers who need centralized user management.

## Business Requirements

### Must-Have Features (Deal-breakers)
1. **User synchronization** from AD Organizational Units (OUs)
2. **Attribute mapping** (email, UPN, GUID, etc.)
3. **Group membership sync** for role assignment
4. **Scheduled synchronization** (hourly, daily, weekly)
5. **Delta/incremental sync** to avoid full refreshes
6. **SSO/SAML authentication** (separate from sync, but often required together)

### Nice-to-Have Features
1. **Provisioning rules engine** (conditional user creation)
2. **Auto-disable** on AD account deactivation
3. **Custom attribute mapping** configuration UI
4. **Manual on-demand sync** capability
5. **Conflict resolution** for duplicate users

## Implementation Options

### Option 1: LDAP Protocol (Direct Integration) - Recommended

**Protocol:** Lightweight Directory Access Protocol (LDAP)  
**Port:** 389 (LDAP), 636 (LDAPS - TLS encrypted)  
**Python Library:** `ldap3` (pure Python, actively maintained)

#### Pros
- ✅ **Industry standard** - LDAP is the native protocol for AD
- ✅ **Full control** - Direct access to AD data structure
- ✅ **No additional server** - Connect directly from Django application
- ✅ **Mature libraries** - ldap3 is stable and well-documented
- ✅ **Fine-grained queries** - Can query specific OUs, attributes, filters
- ✅ **Free and open source** - No licensing costs
- ✅ **Widely supported** - Works with AD, OpenLDAP, FreeIPA, etc.
- ✅ **Supports pagination** - Can handle large directories (10k+ users)
- ✅ **Read-only by default** - Safe, no risk of modifying AD
- ✅ **Delta sync capable** - Query only changed entries since last sync

#### Cons
- ⚠️ **Firewall complexity** - Requires opening LDAPS (636) port from cloud to on-prem AD
- ⚠️ **Certificate management** - Need valid SSL/TLS certificates for LDAPS
- ⚠️ **Network latency** - Queries can be slow if AD is on-prem and app is in cloud
- ⚠️ **Requires AD credentials** - Service account with read permissions needed

#### Architecture Diagram

```
┌─────────────────┐         LDAPS (636)         ┌──────────────────┐
│ Django App      │ ─────────────────────────> │ On-Prem AD       │
│ (Cloud)         │         TLS Encrypted       │ Domain Controller│
│                 │ <───────────────────────── │                  │
│ - ldap3 library │         Query Results       │ - Users          │
│ - Sync jobs     │                             │ - Groups         │
│ - Celery tasks  │                             │ - OUs            │
└─────────────────┘                             └──────────────────┘
```

#### Security Considerations
- ✅ **TLS encryption** - Use LDAPS (port 636) for encrypted communication
- ✅ **Read-only service account** - Create AD service account with read-only permissions
- ✅ **Least privilege** - Only grant access to specific OUs needed
- ✅ **Credential storage** - Store AD credentials in secrets manager (AWS Secrets Manager, Vault)
- ✅ **IP whitelisting** - Restrict LDAPS access to known application IPs
- ✅ **Audit logging** - Log all AD queries for security audit trail

#### Example Code

```python
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException
import ssl

class ActiveDirectoryConnector:
    def __init__(self, server_url, service_account_dn, password, base_dn):
        """
        Initialize AD connector
        
        Args:
            server_url: ldaps://ad.company.com:636
            service_account_dn: CN=ServiceAccount,OU=Service Accounts,DC=company,DC=com
            password: Service account password
            base_dn: DC=company,DC=com
        """
        # Create TLS context
        tls = ssl.create_default_context()
        tls.check_hostname = False
        tls.verify_mode = ssl.CERT_REQUIRED
        
        # Create server object
        self.server = Server(
            server_url,
            use_ssl=True,
            tls=tls,
            get_info=ALL
        )
        
        # Create connection
        self.conn = Connection(
            self.server,
            user=service_account_dn,
            password=password,
            auto_bind=True,
            raise_exceptions=True
        )
        
        self.base_dn = base_dn
    
    def search_users(self, ou_filter=None, attributes=None):
        """
        Search for users in AD
        
        Args:
            ou_filter: OU=Employees,DC=company,DC=com (optional)
            attributes: List of attributes to retrieve
        
        Returns:
            List of user entries
        """
        if attributes is None:
            attributes = [
                'sAMAccountName',  # Username
                'mail',            # Email
                'userPrincipalName',  # UPN
                'objectGUID',      # Unique ID
                'givenName',       # First name
                'sn',              # Last name (surname)
                'displayName',     # Display name
                'memberOf',        # Group memberships
                'whenChanged',     # Last modified timestamp
                'userAccountControl',  # Account status (enabled/disabled)
            ]
        
        search_base = ou_filter if ou_filter else self.base_dn
        
        # Search filter: Active users only (not disabled, not deleted)
        search_filter = '(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))'
        
        self.conn.search(
            search_base=search_base,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=attributes,
            paged_size=1000  # Pagination for large results
        )
        
        return self.conn.entries
    
    def search_groups(self, ou_filter=None):
        """Search for security groups in AD"""
        search_base = ou_filter if ou_filter else self.base_dn
        
        search_filter = '(objectClass=group)'
        
        self.conn.search(
            search_base=search_base,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=['cn', 'distinguishedName', 'member', 'whenChanged'],
            paged_size=1000
        )
        
        return self.conn.entries
    
    def get_delta_users(self, since_timestamp):
        """
        Get users modified since a specific timestamp (delta sync)
        
        Args:
            since_timestamp: datetime object
        
        Returns:
            List of modified user entries
        """
        # Convert to AD timestamp format (Windows FILETIME)
        ad_timestamp = int((since_timestamp - datetime(1601, 1, 1)).total_seconds() * 10000000)
        
        search_filter = f'(&(objectClass=user)(objectCategory=person)(whenChanged>={ad_timestamp}))'
        
        self.conn.search(
            search_base=self.base_dn,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes='*',
            paged_size=1000
        )
        
        return self.conn.entries
    
    def is_user_enabled(self, user_entry):
        """
        Check if user account is enabled
        
        userAccountControl flag: 0x0002 = ACCOUNTDISABLE
        """
        uac = int(user_entry.userAccountControl.value)
        return not (uac & 0x0002)  # Check if ACCOUNTDISABLE bit is NOT set
    
    def close(self):
        """Close connection"""
        self.conn.unbind()
```

#### Sync Job Implementation

```python
# celery task for scheduled sync
@shared_task
def sync_ad_users():
    """Synchronize users from Active Directory"""
    from modules.firm.models import Firm, User
    from modules.ad_sync.models import ADSyncConfig, ADSyncLog
    
    # Get all firms with AD sync enabled
    firms = Firm.objects.filter(ad_sync_enabled=True)
    
    for firm in firms:
        try:
            config = firm.ad_sync_config
            
            # Connect to AD
            connector = ActiveDirectoryConnector(
                server_url=config.server_url,
                service_account_dn=config.service_account_dn,
                password=decrypt(config.encrypted_password),
                base_dn=config.base_dn
            )
            
            # Determine sync type (full or delta)
            last_sync = config.last_sync_at
            if config.sync_type == 'delta' and last_sync:
                users = connector.get_delta_users(since_timestamp=last_sync)
            else:
                users = connector.search_users(ou_filter=config.ou_filter)
            
            # Process users
            created_count = 0
            updated_count = 0
            disabled_count = 0
            
            for ad_user in users:
                # Map AD attributes to User model
                email = ad_user.mail.value if ad_user.mail else None
                if not email:
                    continue  # Skip users without email
                
                # Check if user exists
                user, created = User.objects.get_or_create(
                    firm=firm,
                    email=email,
                    defaults={
                        'first_name': ad_user.givenName.value if ad_user.givenName else '',
                        'last_name': ad_user.sn.value if ad_user.sn else '',
                        'is_active': connector.is_user_enabled(ad_user),
                        'ad_guid': str(ad_user.objectGUID.value),
                        'ad_upn': ad_user.userPrincipalName.value if ad_user.userPrincipalName else None,
                    }
                )
                
                if created:
                    created_count += 1
                    # Apply provisioning rules (auto-assign role based on AD group)
                    apply_provisioning_rules(user, ad_user, config)
                else:
                    # Update existing user
                    user.first_name = ad_user.givenName.value if ad_user.givenName else user.first_name
                    user.last_name = ad_user.sn.value if ad_user.sn else user.last_name
                    
                    # Auto-disable if AD account is disabled
                    if config.auto_disable_users:
                        is_enabled = connector.is_user_enabled(ad_user)
                        if user.is_active and not is_enabled:
                            user.is_active = False
                            disabled_count += 1
                    
                    user.save()
                    updated_count += 1
            
            # Log sync results
            ADSyncLog.objects.create(
                firm=firm,
                sync_type=config.sync_type,
                users_created=created_count,
                users_updated=updated_count,
                users_disabled=disabled_count,
                status='success',
                duration_seconds=(datetime.now() - start_time).seconds
            )
            
            # Update last sync timestamp
            config.last_sync_at = datetime.now()
            config.save()
            
            connector.close()
            
        except LDAPException as e:
            # Log error
            ADSyncLog.objects.create(
                firm=firm,
                sync_type=config.sync_type,
                status='error',
                error_message=str(e)
            )
```

#### Implementation Effort
- **AD-1:** Implement AD Organizational Unit sync (16-20 hours)
  - LDAP connection setup
  - User search and sync logic
  - Error handling and logging
- **AD-2:** Build AD attribute mapping (12-16 hours)
  - Attribute mapping configuration model
  - Mapping UI in admin panel
  - Conflict resolution logic
- **AD-3:** Create provisioning rules engine (12-16 hours)
  - Rules model and engine
  - Condition evaluation
  - Role assignment automation
- **AD-4:** Add scheduled synchronization (12-16 hours)
  - Celery task setup
  - Cron schedule configuration
  - Delta sync implementation
- **AD-5:** Implement AD group sync (12-16 hours)
  - Group search and mapping
  - Member sync
  - Auto-update logic

**Total Effort: 64-88 hours**

### Option 2: Microsoft Graph API (Cloud-only)

**API:** https://graph.microsoft.com  
**Auth:** OAuth 2.0  
**Library:** `msal` (Microsoft Authentication Library)

#### Pros
- ✅ **Modern REST API** - HTTP-based, easy to use
- ✅ **Azure AD native** - Best for Azure AD (cloud-based AD)
- ✅ **No firewall issues** - Outbound HTTPS only
- ✅ **Rich API** - Can access users, groups, calendars, emails, etc.
- ✅ **Delta query support** - Efficient incremental sync

#### Cons
- ❌ **Azure AD only** - Does NOT work with on-prem Active Directory
- ❌ **OAuth complexity** - Requires app registration in Azure AD
- ❌ **Rate limits** - 3,000 requests per 5 minutes
- ❌ **Licensing dependency** - Requires Azure AD Premium for some features
- ❌ **Not suitable for hybrid environments**

#### When to Use
- ✅ Customer uses Azure AD (cloud-based)
- ✅ No on-prem Active Directory
- ✅ Microsoft 365 / Office 365 customers

#### Example Code

```python
from msal import ConfidentialClientApplication
import requests

class AzureADConnector:
    def __init__(self, tenant_id, client_id, client_secret):
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=self.authority
        )
    
    def get_token(self):
        """Get access token"""
        result = self.app.acquire_token_for_client(scopes=self.scope)
        return result.get('access_token')
    
    def get_users(self):
        """Get all users"""
        token = self.get_token()
        headers = {'Authorization': f'Bearer {token}'}
        
        url = "https://graph.microsoft.com/v1.0/users"
        response = requests.get(url, headers=headers)
        
        return response.json()['value']
```

### Option 3: Azure AD Connect (Microsoft's Tool)

**What it is:** Microsoft's official on-prem to Azure AD sync tool

#### Pros
- ✅ **Official Microsoft solution**
- ✅ **Handles sync automatically**
- ✅ **Password hash sync** (optional)

#### Cons
- ❌ **Requires Azure AD** - Forces customers to use Azure AD (not free)
- ❌ **No direct API access** - Still need to use Graph API
- ❌ **Another moving part** - Another tool to maintain
- ❌ **Not our integration** - We'd still need to integrate with Azure AD via Graph API

**Verdict:** Not a solution for us, but customers might already use it

### Option 4: SCIM 2.0 Protocol (Future Enhancement)

**Protocol:** System for Cross-domain Identity Management  
**Standard:** RFC 7643, RFC 7644

#### Overview
- Industry standard for user provisioning
- Used by Okta, Azure AD, Google Workspace
- REST API for user CRUD operations

#### Pros
- ✅ **Industry standard** - Works with many identity providers
- ✅ **Bidirectional** - Can provision users FROM platform TO AD (advanced use case)
- ✅ **Well-defined spec** - Clear contracts

#### Cons
- ⚠️ **Requires SCIM server** - We'd need to build SCIM endpoints
- ⚠️ **Complex spec** - More complex than LDAP
- ⚠️ **Not primary integration** - Most customers want LDAP sync

**Recommendation:** Implement SCIM later (Phase 2) for Okta/Azure AD provisioning

## Comparison Matrix

| Feature | LDAP (ldap3) | Graph API | Azure AD Connect | SCIM 2.0 |
|---------|-------------|-----------|------------------|----------|
| On-Prem AD Support | ✅ Yes | ❌ No | ✅ Yes (with Azure AD) | ❌ No |
| Azure AD Support | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Setup Complexity | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Network Requirements | Inbound 636 | Outbound 443 | Both | Outbound 443 |
| Cost | FREE | FREE (with Azure AD) | Requires Azure AD | FREE (with provider) |
| Control | FULL | API Limits | Minimal | FULL (if we build) |
| Enterprise-ready | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Phase 2 |

## Recommendation

### **Primary Solution: LDAP via ldap3** ✅

#### Justification

1. **Supports on-prem AD** - Most enterprise customers have on-prem Active Directory
2. **No vendor lock-in** - Works with any LDAP-compliant directory (AD, OpenLDAP, FreeIPA)
3. **Full control** - Direct access to AD, no API rate limits
4. **Industry standard** - LDAP is the native protocol for AD
5. **Free and open source** - No licensing costs
6. **Proven technology** - Used by thousands of enterprise applications

### **Secondary Solution: Microsoft Graph API** ✅

For customers using Azure AD (cloud-only), provide Graph API integration as an alternative.

#### Hybrid Strategy

```
┌─────────────────────────────────────────┐
│ Django App (ConsultantPro)              │
│                                          │
│ ┌────────────────┐   ┌────────────────┐ │
│ │ LDAP Connector │   │ Graph API      │ │
│ │ (ldap3)        │   │ Connector      │ │
│ └────────────────┘   └────────────────┘ │
│         │                    │           │
└─────────┼────────────────────┼───────────┘
          │                    │
          │                    │
   ┌──────▼──────┐      ┌─────▼─────┐
   │ On-Prem AD  │      │ Azure AD  │
   │ (LDAPS 636) │      │ (Graph    │
   │             │      │  API)     │
   └─────────────┘      └───────────┘
```

## Implementation Plan

### Phase 1: Core LDAP Integration (32-44 hours)

#### Week 1: Foundation (16-20 hours)
- Create AD sync module structure
- Implement LDAP connector with ldap3
- Build user search and retrieval
- Create sync configuration model
- Build admin UI for AD configuration
- Add credentials encryption (AWS Secrets Manager)

#### Week 2: Sync Logic (16-24 hours)
- Implement full sync job (Celery task)
- Add delta sync capability
- Build attribute mapping system
- Create provisioning rules engine
- Implement group sync
- Add sync logging and monitoring

### Phase 2: Advanced Features (32-44 hours)

#### Week 3-4: Enterprise Features
- Configurable attribute mapping UI
- Conflict resolution UI
- Manual sync trigger (admin button)
- Sync status dashboard
- Error notification system
- Dry-run mode (preview sync without applying)

### Phase 3: Graph API Integration (20-28 hours)

#### Week 5: Azure AD Support
- Implement Graph API connector
- OAuth 2.0 flow for Azure AD
- User and group sync via Graph API
- Delta query implementation

### Total Estimated Effort: 84-116 hours (within the 64-88 hour base + enhancements)

## Security Checklist

- [ ] Use LDAPS (port 636) with TLS encryption
- [ ] Store AD credentials in secrets manager (AWS Secrets Manager, Vault)
- [ ] Create read-only AD service account with least privilege
- [ ] Restrict LDAPS access to specific OUs only
- [ ] IP whitelist for AD access
- [ ] Audit log all AD queries
- [ ] Encrypt AD credentials at rest
- [ ] Rotate service account password quarterly
- [ ] Monitor for failed authentication attempts
- [ ] Set up alerts for sync failures

## Testing Strategy

1. **Unit Tests** - Test LDAP queries, attribute mapping, provisioning rules
2. **Integration Tests** - Test against local OpenLDAP test server
3. **Manual Testing** - Test with customer AD (in sandbox/staging)
4. **Performance Testing** - Sync 10k+ users, measure time and memory
5. **Error Testing** - Test network failures, invalid credentials, timeout scenarios

## References

- ldap3 Documentation: https://ldap3.readthedocs.io/
- Microsoft Graph API: https://docs.microsoft.com/en-us/graph/
- Active Directory Schema: https://docs.microsoft.com/en-us/windows/win32/ad/active-directory-schema
- SCIM 2.0 Specification: https://datatracker.ietf.org/doc/html/rfc7643

## Next Steps

1. ✅ **Research Complete** - LDAP (ldap3) selected as primary solution
2. [ ] Create AD sync module structure (4 hours)
3. [ ] Implement LDAP connector (8-12 hours)
4. [ ] Build sync configuration UI (6-8 hours)
5. [ ] Implement full sync job (8-12 hours)
6. [ ] Update P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md to mark research task as complete

---

**Research Completed By:** Development Team  
**Approved By:** [Pending Review]  
**Implementation Target:** Q1 2026
