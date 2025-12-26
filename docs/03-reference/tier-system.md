# Tier System Reference

This document provides a comprehensive reference for the ConsultantPro tier system, which ensures that security, privacy, and multi-tenant safety are implemented in a structured, non-skippable order.

## Overview

ConsultantPro follows a **strict tiered implementation model** where each tier represents a category of architectural priorities. No tier may be skipped or left partially complete.

## Tier Structure

> **Note:** Status percentages are as of December 2025. See [TODO.md](../../TODO.md) for current work status.

| Tier | Focus Area | Status |
|------|-----------|--------|
| **Tier 0** | Foundational Safety | Complete (83%) |
| **Tier 1** | Schema Truth & CI Truth | Complete (100%) |
| **Tier 2** | Authorization & Ownership | Complete (100%) |
| **Tier 3** | Data Integrity & Privacy | Complete (100%) |
| **Tier 4** | Billing & Monetization | In Progress (63%) |
| **Tier 5** | Durability, Scale & Exit | Not Started (0%) |

## Critical Rules

1. **No tier may be skipped** - Each tier builds on the previous
2. **No tier may be partially completed and left** - All tasks in a tier must be completed
3. **If code conflicts with tier requirements, code must change** - Tier requirements are authoritative
4. **All changes must preserve tenant isolation and privacy guarantees** - Security is non-negotiable
5. **CI must never lie** - Test failures must fail the build

## Tier 0: Foundational Safety

**Purpose:** Establish firm-level tenant isolation, privacy controls, and break-glass access.

**Key Components:**
- Firm/Workspace tenancy model
- Firm context resolution (subdomain/session/token)
- Firm and client scoping enforcement
- Portal containment (default-deny for portal users)
- Platform privacy enforcement (metadata-only access)
- Break-glass access with audit trails

**Completion Criteria:**
- Firm isolation is provable
- Platform cannot read content by default
- Portal users are fully contained
- Break-glass is rare, visible, and audited
- Async jobs are tenant-safe

**Documentation:**
- [Portal Containment](../tier0/PORTAL_CONTAINMENT.md)
- [E2EE Implementation Plan](../tier0/E2EE_IMPLEMENTATION_PLAN.md)
- [Metadata/Content Separation](../tier0/METADATA_CONTENT_SEPARATION.md)

## Tier 1: Schema Truth & CI Truth

**Purpose:** Ensure database schema and CI/CD pipeline reflect reality without lying.

**Key Components:**
- Fix deterministic backend crashes
- Commit all missing migrations
- Make CI honest (no skipped checks)
- Add minimum safety test set

**Completion Criteria:**
- Backend boots without deterministic exceptions
- API schema generation completes without error
- Fresh DB: migrations apply cleanly
- `makemigrations` yields no changes
- CI fails on lint/build/type errors
- Minimal invariant tests exist and run in CI

**Documentation:**
- [Tier 1 Progress Summary](../tier1/TIER1_PROGRESS_SUMMARY.md)

## Tier 2: Authorization & Ownership

**Purpose:** Ensure access control is explicit, enforced, and impossible to bypass.

**Key Components:**
- Standardize permissions across all ViewSets
- Replace direct User imports with AUTH_USER_MODEL
- Add firm + client context to all async jobs
- Firm-scoped querysets (zero global access)
- Portal authorization (client-scoped, explicit allowlist)
- Cross-client access within Organizations

**Completion Criteria:**
- Every endpoint has explicit permissions
- All data access is tenant-scoped
- Portal users are fully contained
- Cross-client access is intentional and auditable
- Async jobs obey the same rules as synchronous code

**Documentation:**
- [Firm-Scoped Querysets Audit](../tier2/FIRM_SCOPED_QUERYSETS_AUDIT.md)
- [ViewSet Permission Audit](../tier2/VIEWSET_PERMISSION_AUDIT.md)
- [Async Job Tenant Context](../tier2/ASYNC_JOB_TENANT_CONTEXT.md)
- [Portal Authorization Architecture](../tier2/PORTAL_AUTHORIZATION_ARCHITECTURE.md)
- [Organization Cross-Client Access](../tier2/ORGANIZATION_CROSS_CLIENT_ACCESS.md)

## Tier 3: Data Integrity & Privacy

**Purpose:** Make the platform trustworthy under stress (legal requests, disputes, incidents, exits).

**Key Components:**
- Purge semantics (tombstones, metadata retention)
- Audit event taxonomy + retention policy
- Audit review ownership and cadence
- Privacy-first support workflows
- Document signing lifecycle & evidence retention

**Completion Criteria:**
- Purge works via tombstones for all content-bearing models
- Every purge emits an immutable audit event
- Audit event system exists, structured, tenant-scoped, content-free
- Retention + review primitives exist
- Support diagnostics can be generated without content access
- Signing events are immutable and survive purges

**Documentation:**
- [Privacy-First Support](../tier3/PRIVACY_FIRST_SUPPORT.md)
- [Document Signing Lifecycle](../tier3/DOCUMENT_SIGNING_LIFECYCLE.md)
- [Audit Review Ownership](../tier3/AUDIT_REVIEW_OWNERSHIP.md)
- [Audit Event System](../tier3/AUDIT_EVENT_SYSTEM.md)

## Tier 4: Billing & Monetization

**Purpose:** Ensure money, scope, and incentives align correctly.

**Key Components:**
- Enforce billing invariants (package/hourly/mixed, approval gates)
- Package fee invoicing
- Hourly billing with approval gates
- Mixed billing (package + hourly together)
- Credit ledger
- Recurring payments (autopay)
- Payment failures, disputes, chargebacks
- Renewal billing behavior

**Completion Criteria:**
- Billing always traces back to an engagement
- Package invoice generation is firm- and client-scoped with per-period duplicate prevention and portal visibility gates
- Package, hourly, and mixed billing are correct and auditable
- Credits, payments, disputes, and renewals are survivable
- Autopay behaves predictably
- No financial state mutates history silently

**Documentation:**
- [Credit Ledger System](../tier4/CREDIT_LEDGER_SYSTEM.md)
- [Billing Invariants and Architecture](../tier4/BILLING_INVARIANTS_AND_ARCHITECTURE.md)
- [Payment Failure Handling](../tier4/PAYMENT_FAILURE_HANDLING.md)
- [Time Entry Approval System](../tier4/TIME_ENTRY_APPROVAL_SYSTEM.md)

## Tier 5: Durability, Scale & Exit

**Purpose:** Ensure the system survives growth, change, and scrutiny.

**Key Components:**
- Hero workflow integration tests (end-to-end truth)
- Performance safeguards (tenant-safe at scale)
- Firm offboarding + data exit flows
- Configuration change safety
- Operational observability (without content)

**Completion Criteria:**
- Full lifecycle is proven end-to-end
- Performance and isolation hold at scale
- Firms can exit cleanly
- Configuration changes are safe
- Operations are observable without content visibility

**Documentation:**
- [Performance Indexes Audit](../tier5/PERFORMANCE_INDEXES_AUDIT.md)
- [Code-Only Implementation Summary](../tier5/CODE_ONLY_IMPLEMENTATION_SUMMARY.md)

## Current Work

For current status and work items, see:
- [TODO.md](../../TODO.md) - Prioritized task list with tier-by-tier breakdown
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Development workflow and tier governance

## Implementation Guidelines

### When Working on Any Tier

1. **Read the tier's documentation first** - Understand all requirements
2. **Complete all tasks in order** - Don't skip or cherry-pick
3. **Write tests** - Prove the requirements are met
4. **Update documentation** - Keep tier status current
5. **Get review** - Security and privacy changes require thorough review

### When a Tier is "Complete"

A tier is only complete when:
- All tasks are implemented
- All tests pass
- All completion criteria are met
- Documentation is updated
- Code review is approved

## Related Documentation

- [System Invariants](../../spec/SYSTEM_INVARIANTS.md) - Core system rules
- [Security Policy](../../SECURITY.md) - Security reporting and response
- [API Usage Guide](../../API_USAGE.md) - API documentation
