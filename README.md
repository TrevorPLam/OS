# ConsultantPro - Multi-Firm SaaS Platform

**Privacy-First Architecture with Tiered Governance**

---

## 🚨 ARCHITECTURAL GOVERNANCE

This project follows a **strict tiered implementation model** to ensure security, privacy, and multi-tenant safety.

### Tier Structure

| Tier | Focus | Status |
|------|-------|--------|
| **Tier 0** | Foundational Safety (tenancy, privacy, break-glass) | 🔴 Not Started |
| **Tier 1** | Schema Truth & CI Truth (migrations, honest CI) | 🔴 Not Started |
| **Tier 2** | Authorization & Ownership (permissions, scoping) | 🔴 Not Started |
| **Tier 3** | Data Integrity & Privacy (purge, audit, signing) | 🔴 Not Started |
| **Tier 4** | Billing & Monetization (engagement-centric) | 🔴 Not Started |
| **Tier 5** | Durability, Scale & Exit (performance, offboarding) | 🔴 Not Started |

### Critical Rules

1. **No tier may be skipped**
2. **No tier may be partially completed and left**
3. **If code conflicts with `docs/claude/NOTES_TO_CLAUDE.md`, code must change**
4. **All changes must preserve tenant isolation and privacy guarantees**
5. **CI must never lie**

---

## 📋 Documentation

### Governance Documents

- **[NOTES_TO_CLAUDE.md](docs/claude/NOTES_TO_CLAUDE.md)** - Authoritative platform rules (THIS IS LAW)
- **[TODO.md](TODO.md)** - Tiered task list (Tier 0-5)
- **[to_claude](docs/claude/to_claude)** - Original architectural assessment

### Tier Execution Prompts

- **[Tier 0: Foundational Safety](docs/claude/prompts/tier0.md)**
- **[Tier 1: Schema & CI Truth](docs/claude/prompts/tier1.md)**
- **[Tier 2: Authorization](docs/claude/prompts/tier2.md)**
- **[Tier 3: Data Integrity](docs/claude/prompts/tier3.md)**
- **[Tier 4: Billing](docs/claude/prompts/tier4.md)**
- **[Tier 5: Scale & Exit](docs/claude/prompts/tier5.md)**

### Tier Details

- **[TIER0_FOUNDATIONAL_SAFETY.md](docs/claude/tiers/TIER0_FOUNDATIONAL_SAFETY.md)**
- **[TIER2_AUTHORIZATION_OWNERSHIP.md](docs/claude/tiers/TIER2_AUTHORIZATION_OWNERSHIP.md)**

---

## 🔒 Platform Architecture

### Multi-Tenant Model

- **Firm-level tenant isolation** - Hard boundaries between firms
- **Platform privacy enforcement** - Platform staff cannot read customer content by default
- **Break-glass access** - Audited emergency access with time limits and reason tracking
- **Client portal containment** - Default-deny for portal users
- **End-to-end encryption** - Customer content is E2EE
- **Immutable audit logs** - All critical actions tracked with metadata only

### Roles

**Platform:**
- Platform Operator: metadata-only access
- Break-Glass Operator: rare, audited content access

**Firm:**
- Firm Master Admin (Owner): full control, overrides
- Firm Admin: granular permissions
- Staff: least privilege, permissions enabled explicitly

**Client:**
- Portal Users: client-scoped access only

---

## 🚀 Getting Started

**First, read the documentation:**

1. Read `docs/claude/NOTES_TO_CLAUDE.md` for authoritative rules
2. Review `TODO.md` to understand the tiered task structure
3. Confirm which tier you're working on
4. Follow the execution prompt for your tier

**Development must proceed in tier order. No exceptions.**

---

## License

Proprietary - All Rights Reserved
