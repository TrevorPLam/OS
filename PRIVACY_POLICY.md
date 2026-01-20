# Privacy Policy

**Last Updated:** January 20, 2026

ConsultantPro is designed with privacy-first, firm-scoped data handling. This policy summarizes how data is retained and how users can request deletion.

## Data Retention Summary

Retention periods are defined in [docs/DATA_RETENTION_POLICY.md](docs/DATA_RETENTION_POLICY.md). Key defaults:

- **System logs:** 90 days
- **Webhook events:** 180 days
- **Audit trails:** 7 years (compliance minimum)

Retention policies may be extended when required by legal hold or regulatory obligations.

## Webhook Data Minimization

Stripe webhook payloads are stored in a redacted form to minimize exposure of sensitive data. The
platform scrubs the following fields before persisting webhook event data:

- Card numbers and CVV/CVC values
- Email addresses
- Phone numbers

This redaction applies to nested webhook payload fields and any free-text fields that match these
patterns.

## Data Deletion Requests

Data subjects can request deletion or export of their data. Firms should route requests through the platform’s erasure workflow, which follows documented retention and legal hold rules.

## Contact

For privacy questions or data requests, contact: **privacy@consultantpro.com**
