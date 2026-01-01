# CRM Module Documentation

## Overview

The CRM (Customer Relationship Management) module handles pre-sale operations including lead management, sales pipeline, account management, and relationship tracking.

**Workflow**: Lead → Prospect → Proposal → Contract → Client (in clients module)

## Models

### Account (Task 3.1)

Represents a company/organization in the CRM system. Accounts can be prospects, customers, partners, vendors, or competitors.

**Key Features:**
- Company information and business details
- Hierarchical relationships (parent-subsidiary)
- Owner/manager assignment
- Billing and shipping addresses
- Firm-scoped tenant isolation

**Fields:**
- `name`: Company/Organization name (required)
- `legal_name`: Legal entity name if different
- `account_type`: Type of account (prospect, customer, partner, vendor, competitor, other)
- `status`: Active, inactive, or archived
- `industry`: Industry sector
- `website`: Company website
- `employee_count`: Number of employees
- `annual_revenue`: Annual revenue if known
- `owner`: Primary account owner/manager
- `parent_account`: Parent account for subsidiary relationships
- `firm`: Firm this account belongs to (TIER 0)

**Relationships:**
- Has many `AccountContact` (contacts at the account)
- Can have child accounts (subsidiaries)
- Has many `AccountRelationship` (relationships with other accounts)

**API Endpoints:**
- `GET /api/crm/accounts/` - List accounts
- `POST /api/crm/accounts/` - Create account
- `GET /api/crm/accounts/{id}/` - Retrieve account
- `PUT /api/crm/accounts/{id}/` - Update account
- `DELETE /api/crm/accounts/{id}/` - Delete account
- `GET /api/crm/accounts/{id}/contacts/` - Get account contacts
- `GET /api/crm/accounts/{id}/relationships/` - Get account relationships

### AccountContact (Task 3.1)

Represents an individual contact person at an account. These are pre-sale contacts before they become clients.

**Key Features:**
- Personal and professional information
- Contact preferences and communication settings
- Primary contact and decision maker flags
- Marketing opt-out options

**Fields:**
- `account`: Account this contact belongs to (required)
- `first_name`, `last_name`: Contact name (required)
- `email`: Email address (required, unique per account)
- `phone`, `mobile_phone`: Phone numbers
- `job_title`, `department`: Professional information
- `is_primary_contact`: Whether this is the primary contact
- `is_decision_maker`: Whether this contact is a decision maker
- `preferred_contact_method`: Email, phone, or SMS
- `opt_out_marketing`: Marketing opt-out flag
- `is_active`: Active status

**API Endpoints:**
- `GET /api/crm/account-contacts/` - List contacts
- `POST /api/crm/account-contacts/` - Create contact
- `GET /api/crm/account-contacts/{id}/` - Retrieve contact
- `PUT /api/crm/account-contacts/{id}/` - Update contact
- `DELETE /api/crm/account-contacts/{id}/` - Delete contact

### AccountRelationship (Task 3.1)

Tracks business relationships between accounts, forming a relationship graph for account management.

**Key Features:**
- Directed relationships between accounts
- Multiple relationship types
- Timeline tracking (start/end dates)
- Status management

**Relationship Types:**
- Parent-Subsidiary
- Partnership
- Vendor-Client
- Competitor
- Referral Source
- Strategic Alliance
- Reseller
- Other

**Fields:**
- `from_account`: Source account in the relationship (required)
- `to_account`: Target account in the relationship (required)
- `relationship_type`: Type of relationship (required)
- `status`: Active, inactive, or ended
- `start_date`, `end_date`: Relationship timeline
- `notes`: Notes about the relationship

**Validation:**
- Prevents self-referential relationships
- Ensures both accounts belong to the same firm
- Validates end_date is after start_date
- Unique constraint on (from_account, to_account, relationship_type)

**API Endpoints:**
- `GET /api/crm/account-relationships/` - List relationships
- `POST /api/crm/account-relationships/` - Create relationship
- `GET /api/crm/account-relationships/{id}/` - Retrieve relationship
- `PUT /api/crm/account-relationships/{id}/` - Update relationship
- `DELETE /api/crm/account-relationships/{id}/` - Delete relationship

## Existing Models

### Lead

Marketing-captured prospects before qualification. Represents initial contact.

**Status Flow**: New → Contacted → Qualified → Converted (to Prospect)

### Prospect

Active sales opportunities after lead qualification. Can have multiple proposals.

**Stage Flow**: Discovery → Qualification → Proposal → Negotiation → Won/Lost

### Campaign

Marketing campaigns that generate leads and track ROI.

### Proposal

Formal proposals sent to prospects or existing clients. Can be converted to engagements.

**Types:**
- Prospective Client (new business)
- Expansion (existing client)
- Renewal (existing client)

### Contract

Signed contracts with clients. Created from accepted proposals.

### Activity

Activity timeline tracking all interactions with leads, prospects, and clients.

**Activity Types**: Call, Email, Meeting, Note, Task, Proposal Sent, Contract Signed, Follow-up, Other

## Tenant Isolation (TIER 0)

All CRM models enforce firm-level tenant isolation:

- Models have `firm` foreign key (or inherit via relationships)
- ViewSets use `FirmScopedMixin` for automatic filtering
- Queries are automatically scoped to `request.firm`
- Portal users are explicitly denied access via `DenyPortalAccess` permission

## Permissions

- **Staff Users**: Full access to CRM module within their firm
- **Portal Users**: Explicitly denied access (pre-sale is internal only)
- **Platform Operators**: Metadata-only access (break-glass for content)

## Implementation Notes

### Task 3.1 Completion

Task 3.1 "Build Account & Contact relationship graph (CRM)" includes:

✅ **Account Model**: Company/organization management with hierarchical relationships
✅ **AccountContact Model**: Individual contacts at accounts  
✅ **AccountRelationship Model**: Relationship graph between accounts
✅ **Admin Interface**: Full admin support for all three models
✅ **Serializers**: REST API serializers with related data
✅ **ViewSets**: CRUD operations with firm-scoped isolation
✅ **URL Routing**: API endpoints registered
✅ **Migration**: Database migration created (0004_add_account_contact_relationship_models.py)
✅ **Documentation**: This reference document

## Usage Examples

### Creating an Account

```python
from modules.crm.models import Account

account = Account.objects.create(
    firm=firm,
    name="Acme Corporation",
    account_type="prospect",
    status="active",
    industry="Technology",
    website="https://acme.example.com",
    owner=sales_rep,
)
```

### Adding a Contact to an Account

```python
from modules.crm.models import AccountContact

contact = AccountContact.objects.create(
    account=account,
    first_name="John",
    last_name="Doe",
    email="john.doe@acme.example.com",
    job_title="CTO",
    is_primary_contact=True,
    is_decision_maker=True,
)
```

### Creating a Relationship Between Accounts

```python
from modules.crm.models import AccountRelationship

relationship = AccountRelationship.objects.create(
    from_account=parent_account,
    to_account=subsidiary_account,
    relationship_type="parent_subsidiary",
    status="active",
    start_date=date.today(),
)
```

### Querying the Relationship Graph

```python
# Get all subsidiaries of an account
subsidiaries = account.child_accounts.all()

# Get all parent-subsidiary relationships
parent_sub_relationships = account.relationships_from.filter(
    relationship_type="parent_subsidiary",
    status="active"
)

# Get all partnerships
partnerships = AccountRelationship.objects.filter(
    from_account=account,
    relationship_type="partnership",
    status="active"
)
```

## Database Schema

### Indexes

**Account:**
- `crm_account_firm_status_idx`: (firm, status)
- `crm_account_firm_type_idx`: (firm, account_type)
- `crm_account_firm_owner_idx`: (firm, owner)
- `crm_account_parent_idx`: (parent_account)

**AccountContact:**
- `crm_acc_contact_acc_act_idx`: (account, is_active)
- `crm_acc_contact_acc_pri_idx`: (account, is_primary_contact)
- `crm_acc_contact_email_idx`: (email)

**AccountRelationship:**
- `crm_acc_rel_from_status_idx`: (from_account, status)
- `crm_acc_rel_to_status_idx`: (to_account, status)
- `crm_acc_rel_type_idx`: (relationship_type)

### Unique Constraints

- Account: (firm, name) - Account names must be unique within a firm
- AccountContact: (account, email) - Contact emails must be unique per account
- AccountRelationship: (from_account, to_account, relationship_type) - Prevents duplicate relationships

## Related Documentation

- [System Invariants](../../spec/SYSTEM_INVARIANTS.md)
- [Architecture Overview](../04-explanation/architecture-overview.md)
- [API Usage Guide](./api-usage.md)
