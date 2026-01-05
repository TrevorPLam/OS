# INTEGRATION_MAP.md — External Dependencies & Contracts

Document Type: Reference
Version: 2.0.0
Last Updated: 2026-01-02
Owner: Repository Root
Status: Active

Purpose: when this repo becomes a real app, list every integration here with a contract so AI doesn’t “wing it.”

---

## 1) Governance integrations (always-on)
- Git hooks: `.githooks/pre-commit`
- CI: `githubactions/workflows (disabled by default)/governance-ci.yml`
- Tool entrypoints:
  - `.github/copilot-instructions.md`
  - `.cursor/rules/00-governance/RULE.md`
  - `CLAUDE.md`
  - `.aider.conf.yml` (optional)

---

## 2) How to add a real integration (template)
For each integration (Stripe, Twilio, Google APIs, etc.) record:

- Name:
- Purpose:
- Auth method (OAuth, API key, service account):
- Required env vars (names only):
- Client library + version:
- Rate limits / retries:
- Webhooks (events + signature verification):
- Failure modes and fallback:
- Tests/mocks strategy:

Add an ADR if the integration changes architecture, auth, or data models.

---

## 3) Verification
- Update `repo.manifest.yaml` to include any new commands or env vars.
- Add at least one test or runnable verification command.
