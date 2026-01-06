# AGENTS.md — Integrations Module (Native Integration Hub)

Last Updated: 2026-01-06
Applies To: `src/modules/integrations/`

## Purpose

Native integration hub for common platforms (Salesforce, Slack, Google Analytics).

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | IntegrationConnection, IntegrationSyncLog |
| `services.py` | Integration service factory |
| `views.py` | Integration management endpoints |
| `serializers.py` | Integration serializers |

## Domain Model

```
IntegrationConnection (OAuth connection)
    └── IntegrationSyncLog (sync history)
```

## Supported Integrations

| Platform | Features |
|----------|----------|
| Salesforce | CRM sync, lead import |
| Slack | Notifications, deal alerts |
| Google Analytics | Traffic attribution |
| Zapier | Custom automations |

## Key Models

### IntegrationConnection

Platform connection:

```python
class IntegrationConnection(models.Model):
    firm: FK[Firm]
    
    platform: str                     # salesforce, slack, google_analytics
    
    # OAuth
    access_token: str
    refresh_token: str
    token_expires_at: DateTime
    
    # Settings
    settings: JSONField               # Platform-specific config
    
    is_active: bool
    last_sync_at: DateTime
```

## Dependencies

- **Depends on**: `firm/`, various modules based on integration
- **Used by**: CRM, Marketing

## URLs

All routes under `/api/v1/integrations/`:

```
GET        /available/                # List available integrations
GET        /connections/
POST       /connections/
DELETE     /connections/{id}/

GET        /oauth/{platform}/
GET        /oauth/{platform}/callback/
```
