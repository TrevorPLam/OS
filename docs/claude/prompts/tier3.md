# 🔒 TIER 3 EXECUTION PROMPT — DATA INTEGRITY & PRIVACY

You are executing Tier 3 only of a multi-tier build.
Tier 3 makes the system defensible: purge/tombstones, audit taxonomy+retention, privacy-first support flows, and signing evidence retention. No billing feature work.

## Authority

* `/docs/claude/NOTES_TO_CLAUDE.md` is authoritative.
* Assume Tier 0–2 are implemented. Do not re-architect prior tiers except for surgical fixes required by Tier 3 guarantees.

## Scope (WHAT YOU MAY DO)

You may modify only what is required to implement:

1. Purge semantics (tombstones; content removed, metadata retained)
2. Audit event taxonomy (structured events; no content logging)
3. Audit retention policy hooks (enforceable retention mechanism, not necessarily full ops automation)
4. Audit review governance plumbing (fields/workflow primitives to support reviews)
5. Privacy-first support workflow primitives (metadata-only diagnostics; customer-export intake scaffolding)
6. Document signing lifecycle metadata (immutable signing events; evidence retention independent of content)

### Explicitly IN SCOPE

* Tombstone strategy for:
  * messages/comments bodies
  * document content pointers/versions
  * any rich-text notes fields that contain customer content
* Purge API/actions:
  * Master Admin purge (firm-side)
  * Break-glass purge (platform-side) only if already required by Notes/policy
  * reason-required, confirmation-required, immutable audit entry
* Audit logging system:
  * structured event model/table (or equivalent)
  * event categories:
    * AUTH, PERMISSIONS, BREAK_GLASS, BILLING_METADATA, PURGE, CONFIG
  * required fields:
    * firm_id always
    * client_id when applicable
    * actor_id / actor_role
    * action_type
    * target_type + target_id(s)
    * timestamp
    * reason (mandatory for break-glass/purge)
  * prohibition: do not store content payloads
* Retention policy primitives:
  * retention fields/config (per category)
  * ability to expire/archive audit rows without touching customer content
* Review governance primitives:
  * "review status" and "reviewed_by/at" for break-glass and purge events (or a review table)
* Support primitives (no content):
  * diagnostic snapshots using metadata only (counts, timestamps, error codes)
  * customer-provided export intake model with:
    * firm_id
    * uploader
    * retention/expiry timestamp
    * storage pointer (must be treated as sensitive)
* Document signing evidence:
  * immutable signing event model
  * link to document version/hash (not plaintext content)
  * signer identity, timestamp, method, document_version_id/hash
  * signing evidence survives content purge (tombstone retains hashes + event metadata)

### Explicitly OUT OF SCOPE (DO NOT TOUCH)

* Implementing billing/payment workflows (Tier 4)
* Changing pricing logic
* Broad refactors unrelated to purge/audit/support/signing
* Storing or logging customer content "for debugging"
* UI polish beyond minimal admin/serviceability
* Building full SOC2 program (only primitives here)

## Invariants (MUST HOLD)

* Purge removes content but preserves metadata and relationships (tombstone).
* Audit logs never contain customer content.
* Platform remains blind by default (privacy-first).
* Break-glass actions are fully auditable; purge actions are fully auditable.
* Signing events are immutable and remain provable without storing document plaintext.

## Execution Steps (DO THESE IN ORDER)

1. Identify all "content-bearing" fields/models (messages, comments, docs, notes).
2. Implement tombstone schema changes (purged_at, purged_by, purge_reason, is_purged, content_hash/version refs as needed).
3. Implement purge operations:
   * permission-gated (Master Admin / Break-glass as applicable)
   * confirmation + reason required
   * write immutable audit event
4. Implement structured audit event model + writer utilities:
   * central helper for emitting events
   * banlist/guardrails preventing content fields being logged
5. Add retention + review primitives:
   * retention policy representation
   * review record/status for break-glass + purge events
6. Implement privacy-first support primitives:
   * metadata-only diagnostic snapshot generator
   * customer export intake model with expiry/retention fields
7. Implement document signing evidence model:
   * immutable events
   * document version/hash binding
   * survives purge (tombstone keeps version/hash + event metadata)

## Completion Checklist (STOP WHEN TRUE)

* [ ] Purge works via tombstones for all content-bearing models in scope.
* [ ] Every purge emits an immutable audit event with required fields.
* [ ] Audit event system exists, structured, tenant-scoped, content-free.
* [ ] Retention + review primitives exist for auditability.
* [ ] Support diagnostics can be generated without content access.
* [ ] Signing events are immutable and bound to a document version/hash, and survive purges.

## Output Requirements

Before stopping, report:

1. Models/fields treated as "content-bearing"
2. Tombstone fields added and where
3. Purge entry points and permission gates
4. Audit event schema + categories + writer utility location
5. How you prevented content from being logged
6. Retention/review primitives added (what/where)
7. Support primitives added (what metadata, where stored, expiry)
8. Signing evidence model details (fields + link to version/hash)
9. What was intentionally NOT touched

## Stop Conditions

* If you hit a decision requiring policy (e.g., retention durations, which roles can purge): STOP AND ASK.
* Do not proceed to Tier 4.
* No temporary shortcuts, no content logging for debugging.
