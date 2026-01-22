# Tier System Reference

Document Type: Reference
Last Updated: 2026-01-24

This document summarizes what is verified about ConsultantPro's tier system and explicitly flags anything still **UNKNOWN**.

## Verified data model

The tier system is modeled on the `Firm` record with explicit fields for tiers, status, and quota limits:

- **Tier choices**: `starter`, `professional`, `enterprise`. These are the only tiers defined in the model and validation logic. ([Firm model](../../src/modules/firm/models.py), [auth serializers](../../src/modules/auth/serializers.py))
- **Status choices**: `trial`, `active`, `suspended`, `canceled`. ([Firm model](../../src/modules/firm/models.py))
- **Quota fields**: `max_users`, `max_clients`, `max_storage_gb` with default values of 5, 25, and 10 GB respectively. ([Firm model](../../src/modules/firm/models.py))
- **Usage tracking**: `current_users_count`, `current_clients_count`, `current_storage_gb` for live usage vs. limits. ([Firm model](../../src/modules/firm/models.py))
- **Trial metadata**: `trial_ends_at` is stored on the firm record. ([Firm model](../../src/modules/firm/models.py))

## Verified enforcement examples

The following tier-aware checks are implemented today:

- **Enterprise-only SSL provisioning** in the client portal branding flow (blocks non-enterprise firms). ([Portal branding views](../../src/modules/clients/portal_views.py))
- **Provisioning and validation** accept only `starter`, `professional`, `enterprise` tiers when creating firms. ([Firm provisioning](../../src/modules/firm/provisioning.py), [auth serializers](../../src/modules/auth/serializers.py))

## Defaults vs. tier-specific limits

The defaults in the `Firm` model are applied for new firms unless overridden during provisioning or admin updates. There is no per-tier limit matrix in code today, so the per-tier quota policy is **UNKNOWN**. ([Firm model](../../src/modules/firm/models.py), [Firm provisioning](../../src/modules/firm/provisioning.py))

## UNKNOWN (needs confirmation or implementation)

The following items are referenced in prior documentation or product expectations, but no verified implementation is present in code:

- **Per-tier quota matrix** (starter/professional/enterprise limits) beyond the model defaults.
- **Feature availability matrix** (which modules/features are enabled by tier).
- **Tier-specific trial durations** and automated trial expiry workflows.
- **Upgrade/downgrade flows** (billing proration, limit enforcement during downgrade).
- **API rate limit tiers** and usage-based alerts.
- **Tier-based admin commands** (e.g., updating tier via management commands).

If any of the above are implemented elsewhere, update this reference with evidence-backed links.

## See also

- [Firm model](../../src/modules/firm/models.py) — Tier fields, defaults, and validation.
- [Firm provisioning](../../src/modules/firm/provisioning.py) — Provisioning inputs including subscription tiers.
- [Portal branding views](../../src/modules/clients/portal_views.py) — Enterprise-only enforcement example.
