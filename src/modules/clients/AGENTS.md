# AGENTS.md — Clients Module (Post-Sale Client Management)

Last Updated: 2026-01-06
Applies To: `src/modules/clients/`

## Purpose

Manages **post-sale** client relationships. Clients are created when a Proposal is accepted in the CRM module.

**IMPORTANT**: This module is for POST-SALE only. Pre-sale entities (Lead, Prospect, Proposal) are in `modules/crm/`.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | Organization, Client, Contact, ClientEngagement, WorkItem (~2700 LOC) |
| `views.py` | Client CRUD, engagement management |
| `serializers.py` | Client/Contact serializers |
| `portal_views.py` | Client portal endpoints |
| `portal_serializers.py` | Portal-safe serializers (limited fields) |
| `portal_branding.py` | White-label portal customization |
| `health_score_calculator.py` | Client health scoring algorithm |
| `health_score_views.py` | Health score API |
| `segmentation.py` | Client segmentation/filtering |
| `contact_merger.py` | Duplicate contact detection/merge |
| `bulk_operations.py` | Bulk client operations |
| `permissions.py` | Client-specific permissions |
| `middleware.py` | Client context middleware |
| `signals.py` | Post-save hooks |

## Domain Model

```
Organization (optional grouping)
    └── Client (company/individual)
            ├── Contact (people at client)
            ├── ClientEngagement (SOW/retainer)
            │       └── EngagementLine (line items)
            │               └── WorkItem (deliverables)
            └── ClientPortalUser (portal login)
```

## Key Models

### Organization

Optional grouping for cross-client visibility:

```python
class Organization(models.Model):
    firm: FK[Firm]
    name: str
    enable_cross_client_visibility: bool  # Share data within org
```

### Client

The core post-sale entity:

```python
class Client(models.Model):
    firm: FK[Firm]                    # REQUIRED: Tenant boundary
    organization: FK[Organization]    # Optional grouping
    name: str
    status: str                       # active, inactive, churned
    health_score: Decimal            # 0-100, calculated
    # ... contact info, billing address, etc.
```

### ClientEngagement

Represents a SOW, retainer, or project scope:

```python
class ClientEngagement(models.Model):
    client: FK[Client]
    name: str
    status: str                      # draft, active, completed
    start_date: Date
    end_date: Date
    budget: Decimal
    # Immutability: Once invoiced, cannot modify rates
```

### WorkItem

Individual deliverables within an engagement:

```python
class WorkItem(models.Model):
    engagement: FK[ClientEngagement]
    engagement_line: FK[EngagementLine]
    title: str
    status: str                      # todo, in_progress, done
    due_date: Date
    assigned_to: FK[User]
```

## Portal vs Staff Access

**Critical Security Boundary:**

| Endpoint Pattern | Who Can Access |
|------------------|----------------|
| `/api/v1/clients/` | Staff only |
| `/api/v1/portal/` | Portal users (clients) only |

Portal users:
- Can only see their own client's data
- Cannot see other clients, staff info, or internal notes
- Access controlled by `ClientPortalUser` model

## Health Score

Calculated in `health_score_calculator.py`:

```python
def calculate_health_score(client):
    """
    Factors:
    - Engagement activity (30%)
    - Payment history (25%)
    - Communication frequency (20%)
    - Project completion rate (15%)
    - Support ticket sentiment (10%)
    """
```

## Dependencies

- **Depends on**: `firm/`, `core/`
- **Used by**: `projects/`, `finance/`, `documents/`, `api/portal/`
- **Triggered by**: CRM module when Proposal is accepted

## URLs

Staff endpoints (`/api/v1/clients/`):
```
GET/POST   /                       # List/create clients
GET/PUT    /{id}/                  # Client detail
GET        /{id}/health-score/     # Health metrics
POST       /{id}/merge-contacts/   # Contact deduplication
GET        /segments/              # Segmentation queries
```

Portal endpoints (`/api/v1/portal/`):
```
GET        /profile/               # Current client profile
GET        /engagements/           # Their engagements
GET        /documents/             # Shared documents
```
