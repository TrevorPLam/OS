# SCIM 2.0 Research (Provisioning Strategy)

**Status:** Research Complete  
**Last Updated:** January 5, 2026  
**Owner:** Identity & Access Management  
**Canonical Status:** Supporting  
**Related Tasks:** SCIM-1 (Research SCIM 2.0 specification), SCIM-2 through SCIM-5  
**Priority:** LOW  
**Reference:** RFC 7643 (Schemas), RFC 7644 (Protocol)

## Goals

- Validate feasibility and scope for SCIM 2.0 provisioning to support enterprise identity providers (Okta, Azure AD, OneLogin).  
- Identify minimal viable endpoints, data model, and security expectations for ConsultantPro’s multi-tenant environment.

## Key Findings

1. **Core Resources:** Users and Groups with patch/replace semantics; schemas must include custom extension for firm/role metadata.  
2. **Endpoints Required:** `/scim/v2/Users`, `/scim/v2/Groups`, `/scim/v2/ServiceProviderConfig`, `/scim/v2/Schemas`, and `/scim/v2/ResourceTypes`.  
3. **Filtering & Paging:** Must support `filter`, `startIndex`, `count`, and sort; idempotent provisioning expects stable external IDs.  
4. **Patch Semantics:** SCIM PATCH with `add`, `replace`, `remove` operations; bulk is optional but recommended for performance.  
5. **AuthN/AuthZ:** Bearer tokens per tenant; audits for every create/update/delete mapped to firm scope. Mutual TLS optional but beneficial for enterprise customers.

## Data Model Recommendations

- Extend SCIM user with: `urn:consultantpro:tenant:1.0:firmId`, `role`, `timezone`, `locale`, and `status`.  
- Map SCIM group to ConsultantPro roles/teams with safeguards preventing escalation beyond firm admin unless explicitly allowed.  
- Preserve `externalId` from IdP for idempotency; store `meta.lastModified` and `version` (etag) for concurrency.

## API & Validation

- Implement as Django app `src/modules/auth/scim/` with DRF views + serializers enforcing schema validation.  
- Enforce required attributes: `userName`, `name.givenName`, `name.familyName`, `emails`, `active`.  
- Validate uniqueness on `(firm_id, userName)`; reject cross-firm operations.  
- Return correct error types per RFC 7644 (e.g., `scimType` for uniqueness errors).

## Security & Compliance

- Tenant isolation on every request; authorization middleware resolves firm via token claims.  
- Rate limiting per tenant; lockouts on repeated failures.  
- Audit logging for all SCIM writes with correlation IDs to support investigations.  
- PII minimization: limit default attribute set; allow opt-in attributes via schema extensions.

## Implementation Risks & Mitigations

- **Drift with IdPs:** Differences in attribute mappings; mitigate with mapping templates per provider.
- **Bulk Operations:** Large payloads may stress DB; cap `count` and paginate in IdP configs.
- **Role Escalation:** Strict validation on role changes; require elevated token scope for admin assignments.

## Edge Cases & Test Matrix

- **PATCH Replace vs Add:** Validate correct behavior when attributes move between operations; ensure `remove` on non-existent paths returns proper `scimType`.
- **Case Sensitivity:** SCIM userName comparisons are case insensitive; enforce normalized indexes to prevent duplicates across case variations.
- **Filter Semantics:** Support composite filters (e.g., `userName eq "a" and active eq true`) and handle pagination boundaries correctly when `startIndex + count` exceeds total results.
- **Concurrency:** Reject updates when `If-Match` etag is stale; include `weak etag` handling per RFC guidance.
- **Deprovision vs Delete:** Preserve users with `active=false` for auditability; hard deletes only allowed for firm administrators with elevated scope.
- **Schema Extensibility:** Reject unregistered extensions; ensure custom attributes remain namespaced under `urn:consultantpro:tenant:1.0`.

## Acceptance Criteria (SCIM-1)

- Documented SCIM 2.0 scope, endpoints, and security expectations.
- Tenant-aware data model extensions identified.
- Risks and mitigations captured to inform SCIM-2 implementation.
- Edge cases and test expectations documented to seed SCIM-2 through SCIM-6 acceptance tests.
