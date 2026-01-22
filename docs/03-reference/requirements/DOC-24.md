# Security Model (SECURITY_MODEL)

Threat model summary, secrets handling, audit and incident hooks.

Normative for security expectations.

---

## 1) Threat model (summary)

Portal risks:
- account scope escalation
- insecure direct object reference (IDOR)
- document link leakage
- session fixation / token theft

Staff risks:
- overprivileged roles
- audit log access abuse
- injection via uploads/email content

Integration risks:
- OAuth token theft
- webhook spoofing (if used)
- replay attacks

---

## 2) Requirements (MUST)
1. Server-side authz enforcement everywhere.
2. Strong tenant isolation (firm-scoped row-level isolation enforced via FirmScopedQuerySet). See ADR-0010.
3. Secrets MUST be stored in a secrets manager, not repo/env files committed.
4. Signed URLs short-lived; no public buckets.
5. Audit logs append-only, protected.
6. Rate limiting and abuse detection for portal endpoints.
7. Input validation for all external content (email bodies, attachments, filenames).

---

## 3) Incident/breach hooks
- ability to revoke portal sessions and integration connections
- export audit trail for investigation
- notify administrators (policy-defined)

---
