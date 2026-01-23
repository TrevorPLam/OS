# Agent Capabilities

This document defines all capabilities that agents are authorized to perform in this repository.

## Purpose

Capabilities define the boundaries of agent autonomy. Each capability has a specific scope, constraints, and required approvals.

---

## Capability Matrix

| Capability | Autonomous | Requires HITL | Risk Level |
|-----------|------------|---------------|------------|
| create_feature | No | Yes (planning) | 🟡 Medium |
| modify_existing | Partial | Depends on risk | 🟢 Low - 🔴 High |
| add_dependency | No | Yes (always) | 🟡 Medium |
| change_api_contract | No | Yes (always) | 🔴 High |
| change_schema | No | Yes (always) | 🔴 High |
| update_security | No | Yes (always) | 🔴 High |
| update_release_process | No | Yes (always) | 🔴 High |
| apply_waiver | No | Yes (human only) | 🟡 Medium |
| create_adr | Partial | Yes (approval) | 🟢 Low |
| create_task_packet | Yes | No | 🟢 Low |
| run_verification_profiles | Yes | No | 🟢 Low |

---

## 1. Create Feature

**Capability**: `create_feature`

### Description
Create new features including new files, directories, and functionality.

### Scope
- Create new domain/feature directories
- Add new UI components
- Add new domain services
- Add new data repositories
- Add corresponding tests
- Update documentation

### Constraints
- Must follow boundary model: `src/<domain>/<feature>/<layer>/`
- Must include tests
- Must update documentation
- Must respect platform layer rules
- Cannot create cross-feature dependencies without ADR

### Autonomous Actions
- Create file structure
- Implement basic functionality
- Write tests
- Update documentation

### Requires HITL
- Feature planning and requirements clarification
- External system integration
- Cross-feature dependencies
- Security-sensitive features
- Financial/payment features

### Example
```markdown
## Feature: User Password Reset

**Autonomous**:
- Create src/auth/reset/ directory structure
- Create resetService.ts, resetRepository.ts
- Create tests
- Update docs

**HITL Required**:
- Email service integration (external system)
- Token expiration policy (security)
- Reset link format (requirements clarification)
```

---

## 2. Modify Existing

**Capability**: `modify_existing`

### Description
Modify existing code, including bug fixes, improvements, and refactoring.

### Scope
- Fix bugs
- Improve performance
- Refactor code
- Update logic
- Enhance functionality

### Constraints
- Cannot break existing tests
- Cannot break API contracts
- Must maintain backward compatibility
- Must respect boundaries
- Must follow existing patterns

### Autonomous Actions (Low Risk)
- Bug fixes (internal logic)
- Code style improvements
- Performance optimizations (proven safe)
- Internal refactoring (same feature)
- Documentation updates

### Requires HITL (High Risk)
- Breaking changes
- API contract changes
- Schema changes
- Authentication/authorization changes
- Payment/financial logic changes
- External system integration changes
- Cross-feature modifications

### Risk Assessment

**🟢 Low Risk** (autonomous):
- Internal bug fix with tests
- Style/formatting
- Documentation
- Adding logging
- Non-breaking feature enhancement

**🟡 Medium Risk** (careful review):
- Performance changes
- Refactoring across multiple files
- Dependency updates (minor versions)
- Configuration changes

**🔴 High Risk** (requires HITL):
- Breaking changes
- Security-related
- Schema changes
- External system changes
- Authentication changes
- Payment changes

### Example
```markdown
## Modification: Fix Login Bug

**Risk Level**: 🟢 Low

**Change**: Fix null check in validateCredentials
**Files**: src/auth/login/domain/authService.ts
**Tests**: Added test case for null email
**Backward Compatible**: Yes
**HITL Required**: No

✓ Autonomous
```

```markdown
## Modification: Change Token Expiration

**Risk Level**: 🔴 High

**Change**: Reduce JWT token expiration from 24h to 1h
**Impact**: Users will be logged out more frequently
**Security Implications**: Yes (security improvement)
**Breaking Change**: Yes (existing tokens become invalid faster)
**HITL Required**: Yes

→ Created HITL-2024-01-15-token-expiration.md
```

---

## 3. Add Dependency

**Capability**: `add_dependency`

### Description
Add new dependencies to package.json, requirements.txt, or other dependency files.

### Scope
- Add npm packages (frontend)
- Add pip packages (backend)
- Update lock files
- Update documentation

### Constraints
- **ALWAYS requires HITL**
- Must justify need
- Must check for security vulnerabilities
- Must check license compatibility
- Must document usage

### Autonomous Actions
- None (always requires HITL)

### Requires HITL (Always)
- Security review
- License review
- Necessity justification
- Alternative evaluation

### HITL Process
1. Agent proposes dependency
2. Provides justification
3. Lists alternatives considered
4. Checks for vulnerabilities
5. Human reviews and approves
6. Agent adds dependency

### Example
```markdown
## Dependency Addition: axios

**Proposed Dependency**: axios@1.6.0
**Purpose**: HTTP client for API calls
**Current**: Using native fetch (limited functionality)

**Justification**:
- Need request interceptors for auth tokens
- Need automatic retry logic
- Need request/response transformation
- fetch doesn't support these features natively

**Alternatives Considered**:
- Native fetch: Lacks needed features
- ky: Smaller but less mature
- got: Node-only, not browser-compatible
- superagent: Older, less maintained

**Security**: No known vulnerabilities
**License**: MIT (compatible)
**Size**: 13KB gzipped
**Weekly Downloads**: 41M

**HITL Required**: Yes
→ Created HITL-2024-01-15-add-axios.md
```

---

## 4. Change API Contract

**Capability**: `change_api_contract`

### Description
Change public API signatures, endpoints, request/response formats.

### Scope
- Modify API endpoints
- Change request parameters
- Change response formats
- Add/remove API methods
- Change error responses

### Constraints
- **ALWAYS requires HITL**
- Must maintain backward compatibility or provide migration
- Must update API documentation
- Must version if breaking
- Must notify consumers

### Autonomous Actions
- None (always requires HITL)

### Requires HITL (Always)
- Breaking change assessment
- Migration plan
- Consumer notification plan
- Versioning strategy
- Documentation updates

### Example
```markdown
## API Change: Add pagination to /users endpoint

**Current**: GET /users → Returns all users (array)
**Proposed**: GET /users?page=1&limit=20 → Returns paginated users

**Breaking Change**: Yes (response format changes)
**Migration Strategy**: 
- Add v2 endpoint: GET /v2/users?page=1&limit=20
- Deprecate v1: GET /users (maintain for 6 months)
- Add deprecation warning to v1 response

**Affected Consumers**: 
- Frontend (internal)
- Mobile app (internal)
- Third-party integrations (unknown)

**Documentation**: Update API docs, add migration guide

**HITL Required**: Yes
→ Created HITL-2024-01-15-users-pagination.md
```

---

## 5. Change Schema

**Capability**: `change_schema`

### Description
Change database schema, models, or data structures.

### Scope
- Add/remove database tables
- Add/remove columns
- Change column types
- Add/remove indexes
- Change relationships

### Constraints
- **ALWAYS requires HITL**
- Must provide migration scripts
- Must provide rollback scripts
- Must test with production-like data
- Must plan for downtime (if any)

### Autonomous Actions
- None (always requires HITL)

### Requires HITL (Always)
- Migration strategy
- Rollback strategy
- Data loss assessment
- Performance impact assessment
- Downtime planning

### Example
```markdown
## Schema Change: Add email_verified column to users

**Change**: Add `email_verified` boolean column to `users` table
**Migration**: Set existing users to `email_verified = false`
**Default**: `false` for new users
**Rollback**: Drop column

**Data Impact**: 
- Existing users: Set to false (require verification)
- New users: Start as false
- No data loss

**Performance Impact**:
- Migration: ~2 seconds for 100k users
- Index: Not needed (infrequent queries)

**Downtime**: None (online migration)

**HITL Required**: Yes
→ Created HITL-2024-01-15-email-verified-column.md
```

---

## 6. Update Security

**Capability**: `update_security`

### Description
Change security-related code, configurations, or policies.

### Scope
- Authentication logic
- Authorization rules
- Cryptography
- Secrets handling
- Security configurations
- Access controls

### Constraints
- **ALWAYS requires HITL**
- Must be reviewed by security team
- Must include security testing
- Must document security rationale
- Must follow security baseline

### Autonomous Actions
- None (always requires HITL)

### Requires HITL (Always)
- Security review
- Security testing evidence
- Threat model assessment
- Compliance verification

### Example
```markdown
## Security Update: Implement rate limiting on login

**Change**: Add rate limiting to login endpoint
**Mechanism**: 5 attempts per IP per 15 minutes
**Storage**: Redis with TTL
**Lockout**: 15 minute cooldown after 5 failed attempts

**Threat Addressed**: Brute force attacks

**Security Assessment**:
- Effectiveness: High (industry standard)
- False Positives: Low (generous limit)
- Bypass Risk: Medium (IP-based, VPN bypass possible)
- Monitoring: Log all lockouts

**Testing**: 
- Unit tests for rate limit logic
- Integration tests for lockout behavior
- Load test with multiple IPs

**HITL Required**: Yes
→ Created HITL-2024-01-15-login-rate-limit.md
```

---

## 7. Update Release Process

**Capability**: `update_release_process`

### Description
Change how releases are built, tested, or deployed.

### Scope
- CI/CD configuration
- Deployment scripts
- Release workflows
- Versioning strategy
- Rollback procedures

### Constraints
- **ALWAYS requires HITL**
- Must test in staging first
- Must document changes
- Must have rollback plan
- Must notify team

### Autonomous Actions
- None (always requires HITL)

### Requires HITL (Always)
- Process change justification
- Testing in staging
- Team training
- Documentation updates

### Example
```markdown
## Release Process: Add automated security scan to CI

**Change**: Add security scanning step to GitHub Actions workflow
**Tool**: npm audit + Snyk
**When**: Every PR and before release
**Blocks Merge**: Yes (if high/critical vulnerabilities)

**Impact**:
- CI time: +2 minutes
- False positives: Possible (use waivers)
- Security: Improved (catches known vulnerabilities)

**Rollback**: Remove security scan step from workflow

**HITL Required**: Yes
→ Created HITL-2024-01-15-ci-security-scan.md
```

---

## 8. Apply Waiver

**Capability**: `apply_waiver`

### Description
Apply waivers to bypass quality gates.

### Scope
- Coverage waivers
- Performance waivers
- Linting waivers
- Boundary waivers

### Constraints
- **HUMANS ONLY** - Agents cannot approve waivers
- Agents can generate waiver documents
- Agents can propose waivers
- Only humans can mark waivers as approved

### Autonomous Actions
- Generate waiver document
- Fill in waiver template
- Identify what gate failed
- Propose remediation plan

### Requires HITL (Always - Human Approval)
- Human reviews waiver
- Human assesses risk
- Human approves or rejects
- Human sets expiration date

### Example
```markdown
## Waiver: Coverage decrease for data migration

**Generated By**: Agent
**Gate Failed**: Coverage ratchet (85% → 83%)
**Reason**: Data migration script has low test value
**Remediation Plan**: 
- Migration tested manually in staging
- One-time script, will be archived after use
- Target: Remove script after migration complete

**Proposed Expiration**: 2024-02-15 (30 days)
**Approved By**: [Human to fill in]
**Status**: Pending Human Approval

→ HITL-2024-01-15-migration-coverage-waiver.md
```

---

## 9. Create ADR

**Capability**: `create_adr`

### Description
Create Architecture Decision Records for significant decisions.

### Scope
- Document architectural decisions
- Explain rationale
- List alternatives
- Document consequences

### Constraints
- Can draft ADR autonomously
- Requires human approval to finalize
- Must follow ADR template
- Must link to relevant code/docs

### Autonomous Actions
- Draft ADR content
- Research alternatives
- Document trade-offs
- Propose recommendation

### Requires HITL
- Final approval
- Alternative validation
- Consequence verification
- Adoption decision

### Example
```markdown
## ADR Draft: Use JWT for Authentication

**Status**: Proposed (awaiting approval)
**Drafted By**: Agent

**Context**:
Need authentication system for API. Options: JWT, session-based, OAuth2.

**Decision** (Proposed):
Use JWT (JSON Web Tokens) for authentication.

**Rationale**:
- Stateless (no server session storage)
- Scalable (works across multiple servers)
- Standard (RFC 7519)
- Mobile-friendly (easy to store and send)

**Alternatives**:
1. Session-based: Requires session store, less scalable
2. OAuth2: Overkill for first-party app
3. Basic Auth: Not secure enough

**Consequences**:
- Token expiration handling needed
- Refresh token mechanism required
- Can't revoke tokens easily (use short expiration)

**HITL Required**: Yes (approval)
→ HITL-2024-01-15-jwt-auth-adr.md
```

---

## 10. Create Task Packet

**Capability**: `create_task_packet`

### Description
Create task packet documents that define work to be done.

### Scope
- Break down large tasks
- Define work items
- List file changes
- Specify verification
- Document acceptance criteria

### Constraints
- Must follow task packet template
- Must include filepaths
- Must include verification commands
- Must be specific and actionable

### Autonomous Actions
- Create task packet document
- Break down into subtasks
- List affected files
- Define verification steps
- Create acceptance criteria

### Requires HITL
- Only if task requirements are unclear
- Only if scope is ambiguous

### Example
```markdown
## Task Packet: Implement Password Reset

**Task ID**: TASK-123
**Type**: Feature
**Priority**: P1
**Created By**: Agent

**Objective**:
Add password reset functionality for users who forget their password.

**Scope**:
- Create reset request endpoint
- Create reset confirmation endpoint
- Send reset email with token
- Validate token and update password

**Files to Create**:
- src/auth/reset/domain/resetService.ts
- src/auth/reset/data/resetRepository.ts
- src/auth/reset/ui/ResetForm.tsx
- tests/auth/reset.test.ts

**Files to Modify**:
- src/auth/login/domain/authService.ts (add reset method)
- docs/auth/README.md (add reset documentation)

**Verification Commands**:
- npm run lint -- src/auth/reset/
- npm test -- tests/auth/reset.test.ts
- npm run type-check

**Acceptance Criteria**:
- [ ] User can request password reset
- [ ] Reset email sent with unique token
- [ ] Token expires after 1 hour
- [ ] User can set new password with valid token
- [ ] Tests pass (coverage ≥ 85%)
- [ ] Documentation updated

**HITL Required**: Yes (email service integration)
```

---

## 11. Run Verification Profiles

**Capability**: `run_verification_profiles`

### Description
Run verification commands and report results.

### Scope
- Run linting
- Run tests
- Run type checking
- Run security scans
- Run boundary checks
- Run governance checks

### Constraints
- Must run all commands in profile
- Must report all results
- Must not suppress failures
- Must generate evidence

### Autonomous Actions
- Run verification commands
- Collect results
- Generate reports
- Create waivers if needed
- Document evidence

### Requires HITL
- Only if verification fails and unclear how to fix

### Example
```markdown
## Verification Profile: CI

**Profile**: ci (from repo.manifest.yaml)
**Commands**:
1. make lint
2. make typecheck
3. make test

**Results**:

✓ make lint
  - Backend: PASS
  - Frontend: PASS

✓ make typecheck
  - Backend: PASS (mypy)

✓ make test
  - Backend: PASS (247/247 tests)
  - Frontend: PASS (89/89 tests)
  - Coverage: 87% (target: 85%)

**Status**: All checks passed ✓

**Evidence**:
- Logs: /.repo/logs/verification-2024-01-15.log
- Coverage report: /coverage/lcov-report/index.html
```

---

## Capability Expansion

New capabilities can be added through:
1. Proposal via HITL
2. Documentation in this file
3. Approval by repository owner
4. Communication to agents

---

## Related Documents

- **Agents Framework**: `/.repo/agents/AGENTS.md`
- **Agent Roles**: `/.repo/agents/roles.md`
- **Principles**: `/.repo/policy/PRINCIPLES.md`
- **Security Baseline**: `/.repo/policy/SECURITY_BASELINE.md`
- **Quality Gates**: `/.repo/policy/QUALITY_GATES.md`
