# AGENTS.md — CRM Module (Pre-Sale Operations)

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `src/modules/crm/`

## Purpose

Manages **pre-sale** operations: Lead → Prospect → Proposal → (Win) → Client conversion.

**IMPORTANT**: This module is for PRE-SALE only. Post-sale client management is in `modules/clients/`.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | Account, Lead, Prospect, Proposal, Contract, Pipeline, Deal, Campaign (~3470 LOC) |
| `views.py` | CRM entity CRUD |
| `serializers.py` | CRM serializers |
| `lead_scoring.py` | Lead/prospect scoring algorithm |
| `scoring_views.py` | Scoring API endpoints |
| `scoring_serializers.py` | Score-related serializers |
| `enrichment_service.py` | Lead data enrichment |
| `enrichment_tasks.py` | Async enrichment jobs |
| `assignment_automation.py` | Lead/deal auto-assignment |
| `deal_rotting_alerts.py` | Stale deal notifications |
| `signals.py` | Post-save hooks (scoring, notifications) |

## Domain Model

```
Account (company)
    └── Lead (unqualified contact)
            └── Prospect (qualified, in sales process)
                    └── Proposal (pricing/scope document)
                            └── Contract (signed agreement)
                                    → Client (in modules/clients/)

Pipeline
    └── Stage (customizable stages)
            └── Deal (opportunity with value)
```

## Key Models

### Account

Company/organization in CRM:

```python
class Account(models.Model):
    firm: FK[Firm]
    name: str
    account_type: str          # prospect, customer, partner, vendor
    industry: str
    website: str
    annual_revenue: Decimal
```

### Lead

Unqualified contact:

```python
class Lead(models.Model):
    firm: FK[Firm]
    account: FK[Account]       # Optional company link
    first_name: str
    last_name: str
    email: str
    status: str               # new, contacted, qualified, unqualified
    source: str               # web, referral, event, cold_outreach
    score: int                # 0-100, calculated
```

### Prospect

Qualified lead in active sales:

```python
class Prospect(models.Model):
    firm: FK[Firm]
    lead: FK[Lead]            # Source lead
    assigned_to: FK[User]
    status: str               # qualifying, proposal_sent, negotiating
    expected_value: Decimal
    expected_close_date: Date
```

### Deal

Pipeline opportunity:

```python
class Deal(models.Model):
    firm: FK[Firm]
    pipeline: FK[Pipeline]
    stage: FK[Stage]
    prospect: FK[Prospect]
    value: Decimal
    close_date: Date
    probability: int          # 0-100%
    # Deal rotting: days_in_stage tracked
```

### Proposal

Sales proposal with pricing:

```python
class Proposal(models.Model):
    firm: FK[Firm]
    prospect: FK[Prospect]
    status: str              # draft, sent, accepted, rejected
    valid_until: Date
    total_value: Decimal
    # Links to pricing/RuleSet for quote generation
```

### Pipeline & Stage

Customizable sales pipeline:

```python
class Pipeline(models.Model):
    firm: FK[Firm]
    name: str
    is_default: bool

class Stage(models.Model):
    pipeline: FK[Pipeline]
    name: str
    order: int
    probability: int         # Default win probability
    rotting_days: int        # Alert after N days
```

## Workflows

### Lead → Client Conversion

```
1. Lead created (manual, import, or web form)
2. Lead scored automatically (lead_scoring.py)
3. Lead qualified → Prospect created
4. Proposal created and sent
5. Proposal accepted → Contract generated
6. Contract signed → Client created (in modules/clients/)
```

### Deal Pipeline Flow

```
1. Deal enters pipeline at first stage
2. Sales rep moves through stages
3. Deal rotting alerts if stuck (deal_rotting_alerts.py)
4. Deal won → triggers client creation
5. Deal lost → archived with loss reason
```

## Lead Scoring

Calculated in `lead_scoring.py`:

```python
def calculate_lead_score(lead):
    """
    Factors:
    - Demographic fit (industry, size): 30%
    - Behavioral signals (opens, clicks): 25%
    - Engagement recency: 20%
    - Source quality: 15%
    - Explicit interest signals: 10%
    """
```

## Dependencies

- **Depends on**: `firm/`, `core/`
- **Triggers**: `clients/` when Proposal accepted
- **Uses**: `pricing/` for quote generation

## URLs

All routes under `/api/v1/crm/`:

```
# Accounts
GET/POST   /accounts/
GET/PUT    /accounts/{id}/

# Leads
GET/POST   /leads/
GET/PUT    /leads/{id}/
POST       /leads/{id}/qualify/        # Convert to Prospect

# Prospects  
GET/POST   /prospects/
GET/PUT    /prospects/{id}/

# Deals
GET/POST   /deals/
GET/PUT    /deals/{id}/
PUT        /deals/{id}/move-stage/
GET        /deals/analytics/

# Pipelines
GET/POST   /pipelines/
GET/PUT    /pipelines/{id}/stages/

# Proposals
GET/POST   /proposals/
GET/PUT    /proposals/{id}/
POST       /proposals/{id}/send/
POST       /proposals/{id}/accept/     # Creates Client

# Campaigns
GET/POST   /campaigns/
GET/PUT    /campaigns/{id}/
```
