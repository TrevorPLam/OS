# SECURITYAUDIT.md — Security Audit Runbook

**Authority & Precedence:**
1) CODEBASECONSTITUTION.md
2) READMEAI.md
3) TODO.md (Task Truth Source)
4) This runbook (SECURITYAUDIT.md)
5) Supporting docs (SECURITY.md, SECURITY_REVIEW.md, SECURITY_HARDENING_COMPLETE.md)

**Purpose:** Provide consistent security verification and escalation steps while preserving prior security reviews and hardening notes.

## AGENT EXECUTION
- **Inputs to Inspect:** SECURITY.md, SECURITY_REVIEW.md, SECURITY_HARDENING_COMPLETE.md, TODO.md security tasks, environment configuration docs, dependency advisories.
- **Outputs to Produce:**
  - Security findings/tasks added to TODO.md with IDs and owners.
  - Notes appended to the `Summary` section below.
- **Stop Rules:**
  - Do not expose secrets; redact sensitive values in findings.
  - Do not downgrade existing security controls without explicit authorization.
  - For critical issues, stop work and file P0 escalation with containment steps.

## Standard Checklist
- Authentication and authorization enforced for all entry points.
- Webhook signature verification and secret validation in place.
- Input validation and output encoding present at boundaries.
- Rate limiting and abuse protections enabled where applicable.
- Audit logging for sensitive actions and firm-scoped data access.
- Dependency vulnerability review and patching cadence established.

## Preserved Project Guidance (from SECURITY_REVIEW.md and SECURITY_HARDENING_COMPLETE.md)
- Follow documented security review findings and ensure remediation tasks remain tracked.
- Maintain hardening measures already completed; do not remove without replacement.

---

## Summary (append-only)
- Pending entries.
