# READMEAI.md — AI Operating Console (Root)
Document Type: Governance
Version: 1.4.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Active
Dependencies: docs/codingconstitution.md; TODO.md; docs/DOCS_INDEX.md; docs/REPO_MAP.md; CHANGELOG.md; docs/SECURITY_BASELINE.md

Purpose: Single operational entrypoint for any AI working in this repository. Follow exactly.

------------------------------------------------------------
1. Document Hierarchy & Precedence
------------------------------------------------------------
If instructions conflict, follow this order (highest wins):

1) Constitution (docs/codingconstitution.md)
2) READMEAI.md (this file)
3) TODO.md (current priorities and acceptance criteria)
4) docs/README.md (documentation map)
5) All other documentation

Rule: The Constitution may only be changed via the Amendment process.

------------------------------------------------------------
2. Non-Negotiables
------------------------------------------------------------
2.1 Truth & Verification (Anti-Hallucination)
- Never invent facts about the repo.
- If you cannot verify something from files, state UNKNOWN and list:
  a) exact files inspected (paths)
  b) what you expected to find
  c) what is missing
  d) how to verify next

2.2 Small, Reversible Changes
- Prefer edits under 50 lines unless explicitly authorized or required by TODO acceptance criteria.
- Every meaningful change must be reversible via git (atomic commits or PR-shaped changes).

2.3 Constitutional Supremacy
- If a change violates the Constitution, refuse it and propose a compliant alternative.
- If no compliant alternative exists, initiate an Amendment before proceeding.

2.4 Confidence & Stop Rules
- Include a confidence score (0–100) for implementation decisions.
- If confidence < 70, switch to Planner Mode or mark BLOCKED.

------------------------------------------------------------
3. Mandatory Reader Path (Read in strict order)
------------------------------------------------------------
Before executing any task, read:

1) Constitution (docs/codingconstitution.md)
2) TODO.md
3) docs/README.md (Documentation map)
4) docs/REPO_MAP.md
5) Relevant module documentation for the task at hand

If any required file is missing:
- Check if it exists at an alternate location (docs/ vs root)
- State which file is missing and what you need from it
- Continue if you have sufficient context; otherwise mark BLOCKED

------------------------------------------------------------
4. Execution Modes
------------------------------------------------------------
Every response must declare exactly one mode at the top:

4.1 Planner Mode
- Output only: plan + file-level checklist + acceptance criteria + risks + validation steps.
- No edits.

4.2 Implementer Mode (default)
- Plan → Implement → Validate → Document loop.
- List all files changed and what changed.

4.3 Auditor Mode
- Compliance report against the Constitution.
- Must include: violations with file paths, severity, remediation plan.

4.4 Reviewer Mode
- Code review against standards.
- Check: testing, documentation, security, boundaries.

------------------------------------------------------------
5. Work Ordering Rules (Unless TODO overrides)
------------------------------------------------------------
Tier 1: Build/run blockers (dependencies, migrations, configuration)
Tier 2: Structural normalization (module organization, naming conventions)
Tier 3: Documentation alignment (docs match reality)
Tier 4: Safety rails (tests, linting, security checks)
Tier 5: Feature completion (new functionality)

------------------------------------------------------------
6. Django-Specific Rules
------------------------------------------------------------
6.1 Module Structure
- Each module lives in src/modules/<module_name>/
- Standard structure: models.py, views.py, serializers.py, urls.py, tests/
- No circular dependencies between modules

6.2 Database Changes
- Always create migrations: `python manage.py makemigrations`
- Never edit existing migrations
- RLS policies documented for tenant-scoped models

6.3 API Development
- All endpoints use Django REST Framework
- Serializers for all input/output
- Permission classes for authorization
- OpenAPI documentation via drf-spectacular

6.4 Testing
- pytest + pytest-django
- Test structure mirrors module structure
- Tests for: models, serializers, views, permissions, integrations

------------------------------------------------------------
7. Security Checklist (Always Validate)
------------------------------------------------------------
[ ] No hardcoded secrets (check environment variables)
[ ] RLS policies on tenant-scoped models
[ ] Permission checks on all API endpoints
[ ] Input validation and sanitization
[ ] Webhook signature verification
[ ] Rate limiting on sensitive endpoints
[ ] Audit logging for sensitive operations

------------------------------------------------------------
8. CI/CD Validation
------------------------------------------------------------
Before marking work complete, verify:
[ ] `make lint` passes (ruff + black)
[ ] `make test` passes (pytest)
[ ] `make openapi` generates valid spec
[ ] Docker builds successfully
[ ] Documentation updated

------------------------------------------------------------
9. Cross-Cutting Concerns
------------------------------------------------------------
9.1 Multi-Tenancy
- All user/client data must be scoped to Firm
- Use get_queryset() to filter by firm
- RLS at database level for defense in depth

9.2 Audit Logging
- Log who, what, when for sensitive operations
- Include metadata, not content (privacy)
- Use structured logging (JSON)

9.3 API Versioning
- Current version: /api/v1/
- Deprecation: 6-month minimum notice
- Version in URL, not headers

------------------------------------------------------------
10. Emergency Protocol
------------------------------------------------------------
If you encounter:
- Security vulnerability: Mark CRITICAL, document in SECURITY.md format
- Data loss risk: Stop immediately, document risk, propose mitigation
- Constitutional violation: Explain conflict, propose amendment or workaround

See docs/EMERGENCY_PROTOCOL.md for full procedures (if exists).
