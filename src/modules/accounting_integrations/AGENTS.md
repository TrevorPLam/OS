# AGENTS.md — Accounting Integrations Module

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `src/modules/accounting_integrations/`

## Purpose

OAuth integration with QuickBooks Online and Xero for invoice/payment synchronization.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | AccountingOAuthConnection, SyncState, SyncLog (~366 LOC) |
| `quickbooks_service.py` | QuickBooks API client |
| `xero_service.py` | Xero API client |
| `sync_service.py` | Bi-directional sync logic |
| `views.py` | OAuth and sync endpoints |
| `serializers.py` | Connection serializers |
| `signals.py` | Post-sync hooks |

## Domain Model

```
AccountingOAuthConnection (OAuth tokens)
    └── AccountingSyncState (entity sync status)
    └── AccountingSyncLog (sync history)
```

## Key Models

### AccountingOAuthConnection

OAuth connection to accounting provider:

```python
class AccountingOAuthConnection(models.Model):
    firm: FK[Firm]
    user: FK[User]                    # Who connected
    
    provider: str                     # quickbooks, xero
    
    # OAuth tokens (encrypted)
    access_token: str
    refresh_token: str
    token_expires_at: DateTime
    
    # Provider account info
    realm_id: str                     # QuickBooks company ID
    tenant_id: str                    # Xero tenant ID
    
    status: str                       # active, expired, revoked, error
    
    # Sync settings
    sync_invoices: bool
    sync_payments: bool
    sync_customers: bool
    
    last_sync_at: DateTime
    last_error: str
```

### AccountingSyncState

Tracks sync status per entity type:

```python
class AccountingSyncState(models.Model):
    connection: FK[AccountingOAuthConnection]
    
    entity_type: str                  # invoice, payment, customer
    
    # Watermarks for incremental sync
    last_sync_at: DateTime
    last_modified_since: DateTime     # For delta queries
    
    # Stats
    total_synced: int
    total_errors: int
```

## QuickBooks Integration

```python
from modules.accounting_integrations.quickbooks_service import QuickBooksService

service = QuickBooksService(connection)

# Sync invoice to QuickBooks
qb_invoice = service.create_invoice(invoice)

# Fetch payments
payments = service.get_payments(since=last_sync)

# Sync customer
qb_customer = service.upsert_customer(client)
```

### QuickBooks Entity Mapping

| ConsultantPro | QuickBooks |
|---------------|------------|
| Client | Customer |
| Invoice | Invoice |
| Payment | Payment |
| InvoiceLineItem | Line |

## Xero Integration

```python
from modules.accounting_integrations.xero_service import XeroService

service = XeroService(connection)

# Sync invoice to Xero
xero_invoice = service.create_invoice(invoice)

# Fetch payments
payments = service.get_payments(since=last_sync)
```

### Xero Entity Mapping

| ConsultantPro | Xero |
|---------------|------|
| Client | Contact |
| Invoice | Invoice |
| Payment | Payment |
| InvoiceLineItem | LineItem |

## Sync Flow

```
1. User initiates sync (manual or scheduled)
2. Check token validity, refresh if needed
3. For each enabled entity type:
   a. Fetch changes from accounting provider
   b. Update local records
   c. Push local changes to provider
   d. Update SyncState watermarks
4. Log results to SyncLog
```

## Conflict Resolution

When same entity modified in both systems:

```python
# Default: Last-write-wins based on timestamp
# Configurable per firm

CONFLICT_STRATEGIES = {
    "last_write_wins": "Most recent modification wins",
    "consultant_pro_wins": "Our system is source of truth",
    "accounting_wins": "Accounting system is source of truth",
    "manual": "Flag for manual review",
}
```

## Token Refresh

Tokens auto-refresh before expiry:

```python
def ensure_valid_token(connection):
    if connection.token_expires_at < timezone.now() + timedelta(minutes=5):
        refresh_token(connection)
```

## Dependencies

- **Depends on**: `firm/`, `finance/`, `clients/`
- **Used by**: Finance module (invoice sync)
- **External**: QuickBooks Online API, Xero API

## URLs

All routes under `/api/v1/accounting/`:

```
# OAuth
GET        /oauth/quickbooks/         # Start QuickBooks OAuth
GET        /oauth/quickbooks/callback/
GET        /oauth/xero/               # Start Xero OAuth
GET        /oauth/xero/callback/

# Connections
GET        /connections/
GET        /connections/{id}/
DELETE     /connections/{id}/
PUT        /connections/{id}/settings/

# Sync
POST       /connections/{id}/sync/    # Manual sync
GET        /connections/{id}/sync-status/
GET        /connections/{id}/sync-logs/
```
