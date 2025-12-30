# Glossary

**Purpose:** Project-specific terms and definitions for ConsultantPro.

**Evidence:** Terms extracted from codebase, documentation, and configuration files.

---

## A

**ADR (Architecture Decision Record)**
A document recording an architectural decision, its context, and consequences.
**Evidence:** `docs/05-decisions/README.md`, `docs/05-decisions/ADR-0000-template.md`

**Audit Event**
An immutable log entry recording a sensitive action with metadata (actor, timestamp, object_id).
**Evidence:** `docs/codingconstitution.md:363` - "append-only audit trail"

**Autopay**
Automated recurring payment workflow for subscriptions.
**Evidence:** TODO.md:310 - "4.6: Recurring payments/autopay workflow"

---

## B

**Break-Glass Access**
Emergency access to customer content by platform operators, subject to time limits, approval, and auditing.
**Evidence:** `README.md:129` - "Break-glass access: Audited emergency access", `src/config/settings.py:92` - BreakGlassImpersonationMiddleware

**Boundary Rules**
Architectural constraints enforcing module dependencies and layering.
**Evidence:** `docs/BOUNDARY_RULES.md`, `.github/workflows/ci.yml:48-51` - import-linter enforcement

---

## C

**Constitution**
The `codingconstitution.md` document defining non-negotiable rules for the repository.
**Evidence:** `docs/codingconstitution.md:1-412`, Section 2.1 - "Supremacy"

**Correlation ID**
Unique identifier that tracks a request across service boundaries and async operations.
**Evidence:** TODO.md:212 - DOC-21.1, `docs/codingconstitution.md:320` - Section 12.2

---

## D

**DAG (Directed Acyclic Graph)**
Graph structure used for delivery templates to prevent circular dependencies.
**Evidence:** TODO.md:205 - DOC-12.1, `docs/DELIVERY_TEMPLATE_IMPLEMENTATION.md`

**Diátaxis**
Documentation framework organizing docs into tutorials, how-to, reference, and explanation.
**Evidence:** `docs/README.md:3` - [Diátaxis framework](https://diataxis.fr/)

**DLQ (Dead Letter Queue)**
Queue for messages that failed processing after maximum retry attempts.
**Evidence:** TODO.md:207 - DOC-11.1, `docs/codingconstitution.md:246-250` - Section 9.5

**DOC-N (DOC-1 through DOC-35)**
Canonical requirements specifications numbered 1-35.
**Evidence:** TODO.md:188-256, files `docs/1` through `docs/35`

---

## E

**E2EE (End-to-End Encryption)**
Customer content encryption where platform cannot access plaintext.
**Evidence:** `README.md:129`, TODO.md:333 - "E2EE deferred - infrastructure dependency"

**Evidence-Based Documentation**
Documentation style requiring factual claims to cite code locations and verification status.
**Evidence:** `docs/STYLE_GUIDE.md`, Constitution Section 3.1-3.2

---

## F

**Firm**
Multi-tenant boundary representing a consulting company using the platform.
**Evidence:** `README.md:12`, TODO.md:328 - "Firm/Workspace tenancy"

**FirmScopedQuerySet**
QuerySet utility enforcing firm-level data isolation.
**Evidence:** TODO.md:213 - DOC-05.1, implemented in `src/modules/firm/utils.py`

---

## G

**Governance Classification**
Data classification system for PII/HR data redaction in logs and serializers.
**Evidence:** TODO.md:198 - DOC-07.1, `src/modules/core/governance.py`

---

## H

**Hallucination**
Documenting or implementing features/configs that don't exist in the codebase (forbidden by Constitution 3.1).
**Evidence:** `docs/codingconstitution.md:45-47`, `docs/STYLE_GUIDE.md`

---

## I

**Idempotency Key**
Unique identifier ensuring an operation executes at-most-once even if retried.
**Evidence:** `docs/codingconstitution.md:212` - Section 8.3, TODO.md:228 - DOC-13.1

**IDOR (Insecure Direct Object Reference)**
Security vulnerability where user can access objects they shouldn't by manipulating IDs.
**Evidence:** TODO.md:119 - ASSESS-S6.2 risk

---

## M

**Makefile Target**
Command defined in `Makefile` for common operations (setup, lint, test, verify).
**Evidence:** `Makefile:11-158`

**Multi-Tenant**
Architecture where a single codebase serves multiple isolated customers (firms).
**Evidence:** `README.md:8`, `docs/codingconstitution.md:354-357` - Section 13.1

---

## O

**OpenAPI**
Specification format for REST APIs, generated from Django code.
**Evidence:** `docs/03-reference/api/openapi.yaml`, `.github/workflows/docs.yml:58-94`

**Orchestration**
Multi-step workflow engine with retry logic, error classification, and DLQ routing.
**Evidence:** TODO.md:207 - DOC-11.1, `src/modules/orchestration/`

---

## P

**Portal**
Client-facing interface with restricted access (default-deny).
**Evidence:** `README.md:127` - "Client portal containment", `src/config/settings.py:90` - PortalContainmentMiddleware

**PII (Personally Identifiable Information)**
Data that can identify an individual (email, phone, SSN, etc.), subject to redaction rules.
**Evidence:** TODO.md:248 - DOC-21.2, `docs/NO_CONTENT_LOGGING_COMPLIANCE.md`

---

## R

**Recurrence Engine**
System for generating recurring events (appointments, invoices) with DST-safety and deduplication.
**Evidence:** TODO.md:206 - DOC-10.1, `src/modules/recurrence/`

**Runbook**
Operational procedure documenting how to handle failures or execute critical workflows.
**Evidence:** `docs/RUNBOOKS/README.md`, `docs/codingconstitution.md:339-344` - Section 12.6

---

## S

**SAST (Static Application Security Testing)**
Automated security scanning of source code (e.g., bandit for Python).
**Evidence:** `.github/workflows/ci.yml:193-197` - bandit, TODO.md:33 - CONST-1

**Spec (Specification)**
Frozen contract defining data schemas, API shapes, or system invariants.
**Evidence:** `spec/README.md`, `spec/SYSTEM_INVARIANTS.md`

**STRIDE**
Threat modeling framework: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege.
**Evidence:** TODO.md:47 - CONST-5, `docs/THREAT_MODEL.md`

---

## T

**Tenant**
Synonym for "Firm" - isolated customer boundary in multi-tenant architecture.
**Evidence:** `README.md:12`, Constitution Section 13.1

**Tier**
Governance level in the tiered implementation model (Tier 0-5).
**Evidence:** `README.md:34-48`, TODO.md:298-369

**Tombstone**
Soft-delete pattern retaining metadata while removing content.
**Evidence:** TODO.md:350 - "Purge semantics (tombstones, metadata retention)"

---

## U

**UNKNOWN**
Verification status indicating a claim cannot be confirmed without further evidence.
**Evidence:** `docs/STYLE_GUIDE.md` - Documentation Truthfulness section

---

## V

**VERIFIED**
Verification status indicating a command was executed and output captured.
**Evidence:** `docs/STYLE_GUIDE.md` - Evidence-First Writing section

**ViewSet**
Django REST Framework class for REST API endpoints.
**Evidence:** `src/api/portal/views.py`, `src/modules/crm/views.py` (throughout codebase)

---

## Acronyms Quick Reference

| Acronym | Full Name |
|---------|-----------|
| ADR | Architecture Decision Record |
| API | Application Programming Interface |
| CI/CD | Continuous Integration/Continuous Deployment |
| CORS | Cross-Origin Resource Sharing |
| DAG | Directed Acyclic Graph |
| DLQ | Dead Letter Queue |
| DRF | Django REST Framework |
| DST | Daylight Saving Time |
| E2EE | End-to-End Encryption |
| GDPR | General Data Protection Regulation |
| IA | Information Architecture |
| IDOR | Insecure Direct Object Reference |
| MVP | Minimum Viable Product |
| PII | Personally Identifiable Information |
| RBAC | Role-Based Access Control |
| REST | Representational State Transfer |
| SAST | Static Application Security Testing |
| SLA | Service Level Agreement |
| STRIDE | Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege |
| UTC | Coordinated Universal Time |

---

**Last Updated:** 2025-12-30
**Evidence Source:** Terms extracted from codebase analysis (constitution, TODO, README, settings, docs)
