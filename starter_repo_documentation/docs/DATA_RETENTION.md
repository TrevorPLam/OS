# DATA_RETENTION.md — Data Minimization, Retention, and Deletion
Document Type: Governance
Version: 1.0.0
Last Updated: 2026-01-01
Owner: Repository Root
Status: Active
Dependencies: docs/SECURITY_BASELINE.md; docs/DOMAIN_MODEL.md

Principles:
- Minimize data collection.
- Prefer metadata to raw content where feasible.
- Never log raw PII in analytics.

Retention defaults (v1 proposal):
- Actions/Audit: retained for user history; user can delete/export later.
- Notes: retained until user deletes.
- Files: retained until user deletes; avoid duplicating provider content unnecessarily.

Deletion:
- Support entity deletion and account deletion policy (TBD).
