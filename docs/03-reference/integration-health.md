# Integration Health Monitoring
**Document Type:** Reference  
**Version:** 1.0.0  
**Last Updated:** 2026-01-08  
**Owner:** Integrations  
**Status:** Draft  
**Dependencies:** READMEAI.md; TODO.md; CODEBASECONSTITUTION.md

## Purpose
Defines the health monitoring API for native integrations (Salesforce, Slack, Google Analytics) so admins can detect repeated failures and token expiry risks.

## Endpoint
- `GET /api/v1/integrations/health/` (auth required; firm context + `can_manage_settings`)

## Response Shape
```
{
  "generated_at": "2026-01-08T12:34:56Z",
  "cards": {
    "salesforce": [
      {
        "id": 1,
        "status": "active|warning|error|expired",
        "last_synced_at": "...",
        "expires_at": "...",
        "last_error": "...",
        "error_count_24h": 2,
        "token_expiring": false
      }
    ],
    "slack": [
      {
        "id": 2,
        "status": "active|warning|error|disabled",
        "last_health_check": "...",
        "last_error": "...",
        "error_count_24h": 1
      }
    ],
    "google_analytics": [
      {
        "id": 3,
        "status": "active|warning|error|disabled",
        "last_event_at": "...",
        "last_error": "..."
      }
    ]
  },
  "alerts": [
    {
      "integration": "salesforce",
      "level": "warning",
      "message": "Repeated Salesforce sync failures detected in the last 24 hours.",
      "connection_id": 1
    }
  ]
}
```

## Alert Rules
- **Repeated failures (24h):** ≥ 3 errors in Salesforce sync logs or Slack message logs produces a warning alert.
- **Token expiry warning:** Salesforce tokens expiring within 3 days emit a warning alert.
- **Config error state:** Google Analytics configs in `error` status emit a warning alert.

## Notes
- Health cards are intended for admin dashboards and integration health summaries.
- Alerts should be surfaced to firm admins with recommended remediation (token refresh, reconnect, or retry syncs).
