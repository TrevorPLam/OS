# SECURITY_BASELINE.md

Last Updated: 2026-01-02

This is the minimum security posture expected for any repo using this governance framework.

## 1) Secrets
- No secrets in git. Ever.
- `.env` files must be gitignored.
- Use per-environment secret stores when deploying (cloud secret managers, CI secrets).

## 2) Authentication & authorization (if applicable)
- Prefer short-lived tokens.
- Prefer scoped credentials (least privilege).
- Log auth failures without leaking sensitive info.

## 3) Dependencies
- Pin dependencies using lockfiles when supported.
- Run dependency audits in CI (language-specific).

## 4) Data handling
- Identify sensitive data types in `repo.manifest.yaml` (PII, financial, credentials).
- Minimize data retention and log redaction.

## 5) Incident response (minimum)
If you suspect compromise:
1) Follow `docs/EMERGENCY_PROTOCOL.md`
2) Rotate credentials
3) Identify scope
4) Document in `docs/AMENDMENTS.md` or an ADR
