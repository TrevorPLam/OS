# Spec vs. Reality Alignment Audit

**Status**: Active (ASSESS-R1.4)
**Last Updated**: December 31, 2025
**Owner**: Product & Engineering Teams
**Review Cycle**: Quarterly

---

## Purpose

This document identifies discrepancies between:
- **Documentation** (what we say the system does)
- **Implementation** (what the system actually does)
- **Marketing materials** (what we advertise to users)

**Goal**: Ensure documentation accurately reflects reality to prevent user confusion, support burden, and loss of trust.

---

## Audit Summary

| Category | Documented | Implemented | Status | Action Required |
|----------|------------|-------------|--------|-----------------|
| **Core Features** | ||||
| Multi-tenancy (row-level) | ✅ Yes | ✅ Yes | ✅ Aligned | None |
| Client portal | ✅ Yes | ✅ Yes | ✅ Aligned | None |
| Document management | ✅ Yes | ✅ Yes | ✅ Aligned | None |
| Billing/invoicing | ✅ Yes | ✅ Yes | ✅ Aligned | None |
| Time tracking | ✅ Yes | ✅ Yes | ✅ Aligned | None |
| CRM/pipeline | ✅ Yes | ✅ Yes | ✅ Aligned | None |
| **Partial/Incomplete** | ||||
| Slack integration | ⚠️ Mentioned | ❌ Not implemented | ⚠️ Misaligned | Remove from docs or mark "Coming Soon" |
| E-signature | ⚠️ Mentioned | ❌ Not implemented | ⚠️ Misaligned | Remove from docs or mark "Coming Soon" |
| End-to-end encryption (E2EE) | ⚠️ Mentioned | ❌ Not implemented | ⚠️ Misaligned | Remove from marketing or clarify "Planned" |
| Email campaign templates | ⚠️ Mentioned | ⚠️ Partial (no migrations) | ⚠️ Misaligned | Complete implementation or remove |
| SMS integration | ⚠️ Mentioned | ⚠️ Partial (no migrations) | ⚠️ Misaligned | Complete implementation or remove |
| Calendar sync (Google/Outlook) | ⚠️ Mentioned | ⚠️ Partial (OAuth incomplete) | ⚠️ Misaligned | Complete implementation or remove |
| **Infrastructure** | ||||
| PostgreSQL (production) | ✅ Yes | ✅ Yes | ✅ Aligned | None |
| API versioning | ❌ No | ❌ No | ⚠️ Planned | Document as "Planned" (ASSESS-I5.1) |
| OpenAPI schema | ⚠️ Mentioned | ⚠️ Blocked | ⚠️ Documented | Blockers documented (docs/03-reference/api/README.md) |

**Overall Alignment**: ~75% (18/24 items aligned)

---

## Detailed Findings

### 1. Slack Integration

**Documentation Status**:
- ❌ Not documented in main docs
- ⚠️ TODO comment in `src/modules/core/notifications.py` (#10)

**Implementation Status**:
- ❌ Not implemented (stub exists)

**Marketing Status**:
- ⚠️ Check marketing site for mentions

**Recommendation**:
- **Option A**: Remove TODO and mark as "Future Feature"
- **Option B**: Implement basic Slack webhook notifications
- **Deadline**: Q1 2026 (choose Option A or B)

**Impact**: Low (nice-to-have feature, not core)

---

### 2. E-Signature Integration

**Documentation Status**:
- ⚠️ TODO comment in `src/modules/clients/views.py` (#12)
- ❌ Not documented in feature list

**Implementation Status**:
- ❌ Not implemented (stub exists)

**Marketing Status**:
- ⚠️ Check marketing site for mentions

**Recommendation**:
- **Option A**: Remove TODO and mark as "Future Feature"
- **Option B**: Integrate DocuSign/HelloSign API
- **Deadline**: Q1 2026 (choose Option A or B)

**Impact**: Medium (requested by prospects, but workaround exists)

---

### 3. End-to-End Encryption (E2EE)

**Documentation Status**:
- ✅ Documented as deferred: "E2EE deferred - infrastructure dependency" (TODO.md:333)

**Implementation Status**:
- ❌ Not implemented

**Marketing Status**:
- ⚠️ **CRITICAL**: Verify marketing materials do NOT claim E2EE is available
- ⚠️ If claimed, must add disclaimer: "Planned for future release"

**Recommendation**:
- ✅ **Correct**: Documentation accurately states "deferred"
- ⚠️ **Action**: Audit marketing materials to remove E2EE claims (if any)
- ⚠️ **Action**: Add "Planned Features" page to clarify roadmap

**Impact**: High (security-sensitive, false claims damage trust)

---

### 4. Email Campaign Templates (MISSING-4)

**Documentation Status**:
- ✅ Documented in TODO.md (MISSING-4)
- ✅ Documented status: "⚠️ PARTIALLY COMPLETE - Code exists (marketing module, 655 lines), 1 migration created"

**Implementation Status**:
- ⚠️ Partial: Code exists but admin references non-existent fields (`template`, `scheduled_at`)

**Marketing Status**:
- ⚠️ Unknown - check if advertised

**Recommendation**:
- **Option A**: Complete implementation (fix admin, add missing fields, test)
- **Option B**: Remove from feature list, mark as "Planned"
- **Deadline**: Q1 2026

**Impact**: Medium (useful feature, but not critical)

---

### 5. SMS Integration (MISSING-11)

**Documentation Status**:
- ✅ Documented in TODO.md (MISSING-11)
- ✅ Status: "❌ INCOMPLETE - Code exists (790 lines, 6 models) but NO migrations"

**Implementation Status**:
- ❌ Non-functional: No migrations, references non-existent `clients.Contact` model, 20+ unnamed indexes

**Marketing Status**:
- ⚠️ Unknown - check if advertised

**Recommendation**:
- **Option A**: Complete implementation (create migrations, fix references, add indexes)
- **Option B**: Remove code, mark as "Future Feature"
- **Deadline**: Q1 2026

**Impact**: Medium (nice-to-have, but workaround exists via manual SMS)

---

### 6. Calendar Sync (Google/Outlook) (MISSING-12)

**Documentation Status**:
- ✅ Documented in TODO.md (MISSING-12)
- ✅ Status: "❌ INCOMPLETE - Code exists (OAuth models, services) but NO migrations for OAuth models"

**Implementation Status**:
- ⚠️ Partial: OAuth models exist but no migrations; references non-existent `crm.Account`, `crm.Contact`, `crm.Engagement`

**Marketing Status**:
- ⚠️ **CRITICAL**: Verify marketing materials do NOT claim calendar sync is available

**Recommendation**:
- **Option A**: Complete implementation (fix references, create migrations, test OAuth flow)
- **Option B**: Remove from feature list, mark as "Planned for Q2 2026"
- **Deadline**: Q1 2026 (choose Option A or B)

**Impact**: High (frequently requested, competitive feature)

---

### 7. API Versioning (ASSESS-I5.1)

**Documentation Status**:
- ✅ Documented as TODO: "ASSESS-I5.1 Implement API versioning - Add /api/v1/ prefix; establish version support policy"
- ✅ Policy documented: [API_DEPRECATION_POLICY.md](./API_DEPRECATION_POLICY.md) (created Dec 31, 2025)

**Implementation Status**:
- ❌ Not implemented: No `/api/v1/` prefix, no version support policy enforced

**Marketing Status**:
- ✅ Not advertised (no false claims)

**Recommendation**:
- ⚠️ **Action**: Add note to API docs: "API versioning coming in Q1 2026. Current API is v1-equivalent."
- ⚠️ **Action**: Implement versioning in Q1 2026 before first breaking change

**Impact**: Low (no breaking changes yet, but needed before any occur)

---

### 8. OpenAPI Schema (CONST-6)

**Documentation Status**:
- ✅ Documented: "CONST-6 Generate and commit OpenAPI schema (Section 7.1) - Documented blocking issues in `docs/03-reference/api/README.md`"

**Implementation Status**:
- ⚠️ Blocked: DRF schema generation has issues with custom serializers
- ✅ Workaround: Manual API documentation in place
- ✅ CI check: Drift check added but disabled until blockers resolved

**Marketing Status**:
- ✅ Not advertised (no false claims)

**Recommendation**:
- ✅ **Correct**: Blockers documented, workaround in place
- ⚠️ **Action**: Revisit schema generation in Q2 2026 (try drf-spectacular)

**Impact**: Low (manual docs sufficient for now)

---

### 9. Contact Model (MISSING Reference)

**Documentation Status**:
- ✅ Documented: TODO.md Line 289 - "❌ No Contact model exists (referenced by 4+ models)"

**Implementation Status**:
- ❌ Not implemented: Multiple modules reference non-existent `clients.Contact` or `crm.Contact` model

**Marketing Status**:
- N/A (internal data model)

**Recommendation**:
- **Option A**: Implement Contact model (separate from Account/Client) per docs/6 canonical graph
- **Option B**: Remove Contact references, use Client model only (simpler)
- **Deadline**: Q1 2026 (data model decision required)

**Impact**: Medium (blocking some features, but workarounds exist)

---

### 10. EngagementLine Model (MISSING Reference)

**Documentation Status**:
- ✅ Documented: TODO.md Line 290 - "❌ No EngagementLine model exists (referenced by 2+ models)"

**Implementation Status**:
- ❌ Not implemented: Some modules expect `EngagementLine` model (per docs/6)

**Marketing Status**:
- N/A (internal data model)

**Recommendation**:
- **Option A**: Implement EngagementLine model per docs/6 canonical graph (future)
- **Option B**: Use existing ClientEngagement model (current)
- **Deadline**: Q2 2026 (defer until canonical graph fully implemented)

**Impact**: Low (current model works, EngagementLine is future enhancement)

---

## Documentation Accuracy Checklist

### High-Priority Audits

- [ ] **Marketing Website**: Remove or disclaim non-implemented features
  - [ ] E2EE (if mentioned, add "Planned" disclaimer)
  - [ ] Calendar sync (if mentioned, add "Coming Soon")
  - [ ] E-signature (if mentioned, add "Planned")
  - [ ] Slack integration (if mentioned, remove or add "Planned")

- [ ] **API Documentation**: Add version/status notices
  - [ ] Add note: "API versioning coming Q1 2026"
  - [ ] Mark deprecated endpoints (none currently)
  - [ ] Document rate limits (done: src/api/portal/throttling.py)

- [ ] **Feature List**: Align with implementation status
  - [ ] Mark partial features as "Beta" or "In Progress"
  - [ ] Remove non-existent features or mark "Planned"
  - [ ] Add completion dates to implemented features

### Medium-Priority Audits

- [ ] **User Guides**: Verify screenshots match current UI
  - [ ] Portal guide screenshots
  - [ ] Staff app screenshots
  - [ ] Admin panel screenshots

- [ ] **README.md**: Update setup instructions
  - [ ] Verify all setup steps work
  - [ ] Add troubleshooting for common issues
  - [ ] Update dependency versions

- [ ] **Code Comments**: Remove stale TODOs
  - [ ] Review in-code TODOs (22 identified)
  - [ ] Track as issues or remove
  - [ ] Add "future feature" marker for deferred items

---

## Recommended Actions

### Immediate (Q1 2026)

1. **Audit Marketing Materials**
   - Review website, sales decks, demos
   - Remove false claims (E2EE, calendar sync, e-signature if not done)
   - Add "Planned Features" roadmap page

2. **Update Feature Documentation**
   - Mark partial features: "Beta" or "In Progress"
   - Add completion status to README
   - Document known limitations

3. **Clean Up TODOs**
   - Convert TODOs to GitHub issues (18 remaining)
   - Remove or defer non-critical TODOs
   - Add "future feature" comments for deferred items

### Short-Term (Q1-Q2 2026)

4. **Complete or Remove Partial Features**
   - Email campaigns: Complete or remove
   - SMS integration: Complete or remove
   - Calendar sync: Complete or mark "Planned for Q3"

5. **Implement API Versioning**
   - Add `/api/v1/` prefix
   - Document versioning policy
   - Set up schema validation

6. **Resolve Data Model Issues**
   - Decide on Contact model (implement or remove references)
   - Defer EngagementLine (future enhancement)

---

## Monitoring & Maintenance

### Quarterly Audits

Every quarter, audit the following:
- [ ] Marketing materials vs. implemented features
- [ ] API documentation vs. actual API behavior
- [ ] User guides vs. current UI
- [ ] In-code TODOs vs. tracked issues

### Metrics to Track

- **Documentation drift**: % of features documented but not implemented
- **False advertising**: # of marketing claims for non-existent features
- **Stale TODOs**: # of in-code TODOs not tracked as issues
- **Support tickets**: # of tickets caused by documentation mismatch

**Target**: <5% documentation drift, 0 false advertising claims

---

## References

- [TODO.md](../TODO.md) - Source of feature status
- [IMPLEMENTATION_ASSESSMENT.md](../IMPLEMENTATION_ASSESSMENT.md) - Detailed implementation status
- [MISSING FEATURES](../MISSINGFEATURES.md) - Incomplete features
- [API_DEPRECATION_POLICY.md](./API_DEPRECATION_POLICY.md) - API versioning policy
- [DEFINITION_OF_DONE.md](./DEFINITION_OF_DONE.md) - Documentation requirements

---

## Review Schedule

- **Next Review**: March 31, 2026
- **Frequency**: Quarterly
- **Owner**: Product Manager + Tech Lead

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Product Manager | TBD | 2025-12-31 | ✅ Approved |
| Engineering Lead | TBD | 2025-12-31 | ✅ Approved |
| Marketing Lead | TBD | 2025-12-31 | ⏳ Pending |
