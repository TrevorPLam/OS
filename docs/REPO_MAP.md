# Repository Structure Map

**Purpose:** Directory-by-directory explanation of the ConsultantPro codebase.

**Last Updated:** 2025-12-30
**Evidence:** Based on static analysis of repository structure and code inspection.

---

## Root Level

### Configuration & Tooling
```
/
├── Makefile              # Orchestration: setup, lint, test, verify (evidence: Makefile:11-158)
├── pyproject.toml        # Python tooling config: ruff, black, pytest (evidence: pyproject.toml:1-69)
├── requirements.txt      # Python dependencies (evidence: referenced in .github/workflows/ci.yml:101)
├── .github/              # CI/CD workflows
│   └── workflows/
│       ├── ci.yml        # Main CI pipeline: lint, test, security, docker (evidence: .github/workflows/ci.yml:1-323)
│       └── docs.yml      # Docs validation: structure, links, OpenAPI drift (evidence: .github/workflows/docs.yml:1-127)
```

### Documentation (Root Level)
```
├── README.md             # Main entry: quickstart, architecture overview (evidence: README.md:1-170)
├── CONTRIBUTING.md       # Development workflow, test guidance (evidence: CONTRIBUTING.md:1-37)
├── SECURITY.md           # Security vulnerability reporting (evidence: SECURITY.md:1-20)
├── CHANGELOG.md          # Release history (evidence: README.md:28)
├── TODO.md               # Current work & roadmap (evidence: TODO.md:1-505)
└── codingconstitution.md # PLANNED: Symlink to docs/codingconstitution.md
```

---

## `/src/` - Application Code

**Evidence:** `src/config/settings.py:33-72` lists all installed Django apps.

### Configuration
```
src/config/
├── settings.py           # Django settings: env validation, middleware, apps (evidence: src/config/settings.py:1-100+)
├── urls.py               # Root URL routing (evidence: settings.py:95)
├── health.py             # Health/readiness endpoints (evidence: TODO.md:41 - CONST-2)
└── sentry_middleware.py  # Sentry context middleware (evidence: settings.py:88)
```

### Business Modules

**Evidence:** `src/config/settings.py:48-72` defines module organization.

#### Tier 0: Foundation
```
src/modules/firm/         # Multi-tenant foundation, workspace/firm management
                          # Evidence: settings.py:50, README.md:122-129
src/modules/auth/         # Authentication & authorization
                          # Evidence: settings.py:51
```

#### Core Business Domains
```
src/modules/crm/          # Pre-sale: Leads, Prospects, Proposals
                          # Evidence: settings.py:52
src/modules/clients/      # Post-sale: Client management & portal
                          # Evidence: settings.py:53, README.md:142-144
src/modules/projects/     # Project/task management
                          # Evidence: settings.py:54
src/modules/finance/      # Billing, invoicing, payments
                          # Evidence: settings.py:55
src/modules/documents/    # Document management with versioning
                          # Evidence: settings.py:56
```

#### Engines & Automation
```
src/modules/pricing/      # Pricing engine with versioned rulesets
                          # Evidence: settings.py:58, TODO.md:203 (DOC-09.1)
src/modules/delivery/     # Delivery templates & DAG instantiation
                          # Evidence: settings.py:59, TODO.md:205 (DOC-12.1)
src/modules/recurrence/   # Recurrence engine for recurring events
                          # Evidence: settings.py:60, TODO.md:206 (DOC-10.1)
src/modules/orchestration/ # Multi-step workflow orchestration
                          # Evidence: settings.py:61, TODO.md:207 (DOC-11.1)
```

#### Communications & Integration
```
src/modules/communications/ # Messages, conversations, threads
                            # Evidence: settings.py:62, TODO.md:202 (DOC-33.1)
src/modules/email_ingestion/ # Email ingestion with mapping/triage
                             # Evidence: settings.py:63, TODO.md:208 (DOC-15.1)
src/modules/calendar/     # Calendar, appointments, booking links
                          # Evidence: settings.py:64, TODO.md:209 (DOC-34.1)
src/modules/sms/          # SMS messaging (Twilio integration)
                          # Evidence: settings.py:71
```

#### Supporting Modules
```
src/modules/core/         # Shared infrastructure: audit, purge, governance
                          # Evidence: settings.py:49
src/modules/marketing/    # Marketing automation: tags, segments, campaigns
                          # Evidence: settings.py:65
src/modules/support/      # Support/ticketing with SLA tracking
                          # Evidence: settings.py:66
src/modules/onboarding/   # Client onboarding workflows
                          # Evidence: settings.py:67
src/modules/knowledge/    # Knowledge system: SOPs, training, playbooks
                          # Evidence: settings.py:68, TODO.md:222 (DOC-35.1)
src/modules/jobs/         # Background job queue & DLQ
                          # Evidence: settings.py:69, TODO.md:247 (DOC-20.1)
src/modules/snippets/     # Quick text insertion (HubSpot-style)
                          # Evidence: settings.py:70
src/modules/assets/       # Asset management
                          # Evidence: settings.py:57
```

### Frontend
```
src/frontend/             # React/TypeScript frontend application
                          # Evidence: README.md:84-94, Makefile:22
```

### Tests
```
src/tests/                # Test suites
                          # Evidence: pyproject.toml:68
```

---

## `/docs/` - Documentation

**Evidence:** Diátaxis framework per `docs/README.md:3`.

### Organized Documentation (Diátaxis)
```
docs/
├── README.md                    # Documentation map & index
├── codingconstitution.md        # **THE CONSTITUTION** - governance rules
│
├── 01-tutorials/                # Learning-oriented tutorials
├── 02-how-to/                   # Problem-solving guides
├── 03-reference/                # Technical reference material
│   ├── requirements/            # Canonical requirements (DOC-1 to DOC-35)
│   └── api/                     # API reference & OpenAPI spec
├── 04-explanation/              # Understanding-oriented explanations
├── 05-decisions/                # ADRs (Architecture Decision Records)
├── 06-user-guides/              # End-user documentation
└── 07-api-client/               # API client integration guides
```

### Operational Documentation
```
docs/
├── RUNBOOKS/                    # Operational runbooks
│   ├── README.md                # Runbook index
│   └── ROLLBACK.md              # Rollback procedures
├── compliance/                  # Compliance documentation
│   ├── ARCHITECTURAL_BOUNDARIES.md
│   ├── PAGINATION_VERIFICATION.md
│   └── FEATURE_FLAG_POLICY.md
└── ARCHIVE/                     # Archived/outdated docs
    ├── README.md                # Archive policy & index
    ├── analysis-2025-12-30/     # Historical analysis docs
    └── roadmap-legacy-2025-12-30/ # Legacy roadmap docs
```

### Implementation Tracking
```
docs/
├── *_IMPLEMENTATION.md          # ~25 implementation tracking docs
│   # Evidence: TODO.md:198-256 references DOC-* implementations
│
└── (Spec files 1-35)            # TO BE MOVED to docs/03-reference/requirements/
```

---

## `/spec/` - Frozen Specifications

**Evidence:** `spec/README.md:1-27`

```
spec/
├── README.md                    # Spec index
├── SYSTEM_INVARIANTS.md         # Core system rules
├── CHECKLIST.md                 # Spec completeness checklist
├── billing/                     # Billing schemas & contracts
├── contracts/                   # Cross-module contracts
├── dms/                         # Document management specs
├── portal/                      # Portal surface spec
└── reporting/                   # Reporting metadata
```

**Note:** These are **frozen seam decisions** distinct from `docs/03-reference/requirements/` (DOC-1 to DOC-35).

---

## `/scripts/` - Repository Tooling

**Evidence:** `ls /home/user/OS/scripts/` and Makefile references.

```
scripts/
├── README.md                         # Scripts documentation
├── validate_docs_structure.py        # Validates required docs directories (evidence: docs/Makefile:16)
├── check_markdown_links.py           # Checks markdown link validity (evidence: docs/Makefile:17)
├── validate_repo_policy.py           # Validates repo policy compliance (evidence: .github/workflows/docs.yml:56)
├── check_openapi_tier_a.py           # Checks OpenAPI tier A coverage (evidence: .github/workflows/docs.yml:114)
├── lint_firm_scoping.py              # Lints firm scoping patterns (evidence: scripts/ directory listing)
└── setup-deploy-key.sh               # Deploy key setup script (evidence: scripts/ directory listing)
```

---

## Key Patterns & Conventions

### Module Structure
**Evidence:** Consistent patterns observed across `src/modules/*/`.

Each Django app module typically contains:
```
modules/<domain>/
├── models.py            # Django models
├── serializers.py       # DRF serializers
├── views.py             # DRF ViewSets
├── urls.py              # URL routing
├── permissions.py       # Custom permissions
├── admin.py             # Django admin config
├── migrations/          # Database migrations
└── tests/               # Module-specific tests
```

### Firm Scoping (Tier 0)
**Evidence:** Constitution Section 4.1, TODO.md:213 (DOC-05.1).

All business data is scoped to a `Firm` (tenant) using:
- `FirmScopedQuerySet` utility (evidence: TODO.md:213)
- Middleware: `FirmContextMiddleware` (evidence: settings.py:86)

### Multi-Tenancy Architecture
**Evidence:** README.md:122-129, Constitution Section 13.1.

- **Firm-level tenant isolation** - Hard boundaries between firms
- **Portal containment** - `PortalContainmentMiddleware` (evidence: settings.py:90)
- **Break-glass access** - `BreakGlassImpersonationMiddleware` (evidence: settings.py:92)

---

## How to Navigate This Repo

1. **Starting point**: `README.md` for quickstart
2. **Understand rules**: `docs/codingconstitution.md` for governance
3. **Find docs**: `docs/README.md` for documentation map
4. **Understand architecture**: `docs/BOUNDARY_RULES.md`, `docs/THREAT_MODEL.md`
5. **Run commands**: `Makefile` targets (`make lint`, `make test`, `make verify`)

---

**Verification Status:** STATIC-ONLY
**Evidence Sources:** File paths, Makefile targets, settings.py configuration, TODO.md references.
**Commands NOT executed:** Directory listings and file reads only; no command execution performed.
