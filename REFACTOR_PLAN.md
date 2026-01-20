# PRODUCTION REFACTOR PLAN - DETERMINISTIC TRANSFORMATION

**Date:** 2026-01-20  
**Status:** Phase 0 - Planning  
**Baseline:** FORENSIC_AUDIT.md (71 issues identified)  
**Target:** Production-grade, elite codebase  

---

## 1. TARGET ARCHITECTURE DESCRIPTION

### 1.1 Architectural Principles (Non-Negotiable)

**Determinism over cleverness:**
- All configuration explicit (no magic defaults)
- All side effects documented and isolated
- All error paths defined
- All state transitions enumerated

**Explicit over implicit:**
- Dependency injection instead of global state
- Type contracts instead of duck typing
- Explicit permissions instead of implicit checks
- Explicit resource cleanup (context managers)

**Compile-time failure over runtime failure:**
- Strict type checking (MyPy strict mode)
- Schema validation at boundaries (Pydantic)
- Exhaustiveness checks on enums/unions
- Contract testing between services

**Automation over convention:**
- Pre-commit hooks enforce style
- CI gates block bad code
- Dependency scans automatic
- Type generation from schemas

**Guardrails over trust:**
- Rate limiting on all endpoints
- Input validation on all boundaries
- Query timeouts on all DB access
- Circuit breakers on external services

**Observability over optimism:**
- Structured logging everywhere
- Distributed tracing on all requests
- Error boundaries in all components
- Health checks on all services

**Delete code aggressively:**
- Remove unused imports
- Remove dead code paths
- Remove redundant abstractions
- Remove duplicate logic

### 1.2 Target Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                           │
│  - Rate limiting, CORS, CSP headers                     │
│  - Request ID generation, auth validation               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                       │
│  - DRF ViewSets (thin, delegating to services)         │
│  - Serializers (validation + type conversion)          │
│  - Permissions (explicit, testable)                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Service Layer                          │
│  - Business logic (pure functions where possible)       │
│  - Transaction management                               │
│  - Event publishing                                     │
│  - External API clients (with retries, timeouts)       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Repository Layer                        │
│  - Query optimization (select_related, prefetch)        │
│  - Firm scoping enforcement                             │
│  - Pagination                                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Domain Models                         │
│  - Django models (state only)                           │
│  - Encrypted fields                                     │
│  - RLS policies                                         │
└─────────────────────────────────────────────────────────┘
```

### 1.3 Module Boundaries (Enforced)

**Core Principles:**
1. Modules depend ONLY on core, never on each other directly
2. Cross-module communication via events or explicit service contracts
3. No circular dependencies (enforced by import-linter)
4. Each module has clear public API (explicit __all__)

**Dependency Rules:**
```
┌──────────────────────────────────────────────────────┐
│  Core (No dependencies on business modules)          │
│  - Encryption, audit, security, telemetry            │
└──────────────────────────────────────────────────────┘
         ↑              ↑              ↑
         │              │              │
┌────────┴───────┐ ┌───┴────────┐ ┌──┴────────────┐
│  CRM           │ │  Clients   │ │  Finance      │
│  (Depends on:  │ │  (Depends  │ │  (Depends on: │
│   core only)   │ │   on: core │ │   core only)  │
└────────────────┘ └────────────┘ └───────────────┘
```

### 1.4 Security Architecture

**Zero-Trust Model:**
- Every request authenticated
- Every operation authorized
- Every input validated
- Every output sanitized

**Defense in Depth:**
1. **Network:** Rate limiting, DDoS protection, WAF
2. **Application:** CSRF tokens, CSP headers, input validation
3. **Data:** Encryption at rest, RLS, audit logging
4. **Identity:** MFA, constant-time comparisons, session management

**Secret Management:**
- No secrets in code (fail fast if missing)
- Secrets in environment only
- Rotation automated
- Access audited

---

## 2. REFACTOR PLAN (PHASED, SAFE, REVERSIBLE)

### Phase 0: Foundation (Week 1) - IMMEDIATE P0 FIXES

**Goal:** Stop the bleeding. Fix critical security vulnerabilities.

**Changes:**
1. **Fix Hardcoded Encryption Key** (Issue #5.1)
   - Location: `src/modules/core/encryption.py:80`
   - Change: Remove fallback, raise exception if not set
   - Prevents: All encrypted data compromise
   - Reversal: `git revert <commit>` restores fallback

2. **Fix Timing Attack on OTP** (Issue #5.3)
   - Location: `src/modules/auth/mfa_views.py:287,299`
   - Change: Replace `==` with `hmac.compare_digest()`
   - Prevents: MFA bypass via timing analysis
   - Reversal: Single line change, easily reverted

3. **Fix CSRF Bypass on SAML** (Issue #5.2)
   - Location: `src/modules/auth/saml_views.py:119,142,212`
   - Change: Add SAML RelayState validation, remove @csrf_exempt
   - Prevents: Account takeover via CSRF
   - Reversal: Restore @csrf_exempt decorator

4. **Fix Production Dockerfile** (Issue #8.5)
   - Location: `Dockerfile:40`
   - Change: Replace runserver with gunicorn
   - Prevents: DEBUG leaks, DoS, no SSL
   - Reversal: Change CMD back to runserver

5. **Add Type Validation to Webhooks** (Issue #1.3)
   - Location: `src/api/finance/webhooks.py:250`
   - Change: Validate `amount_received` is numeric before division
   - Prevents: Webhook crash → revenue loss
   - Reversal: Remove validation

**Validation:**
- Run existing tests: `pytest src/tests/`
- Manual test: OTP login flow, SAML login, Stripe webhook
- Docker build test: `docker build .`

**Rollback Strategy:** Each change is independent, can be reverted individually.

---

### Phase 1: CI/CD Foundation (Week 1-2)

**Goal:** Enable automated quality gates to prevent future regressions.

**Changes:**
1. **Create GitHub Actions Workflow**
   - File: `.github/workflows/ci.yml`
   - Jobs: test, lint, typecheck, security-scan
   - Prevents: Broken code merging to main
   - Why: Issue #8.1 - No CI/CD automation

2. **Add Pre-commit Hooks**
   - File: `.pre-commit-config.yaml` (update existing)
   - Hooks: black, ruff, mypy, git-secrets
   - Prevents: Style drift, secret commits
   - Why: Issue #8.4 - No SAST in pipeline

3. **Configure Dependency Scanning**
   - Tool: pip-audit in CI
   - Prevents: Known CVEs in production
   - Why: Issue #6.2, #6.4 - CVE risks

**New Invariants:**
- All PRs must pass CI before merge (branch protection)
- All commits must pass pre-commit hooks
- All dependencies scanned weekly

**Validation:**
- Push test commit, verify CI runs
- Try committing with lint error, verify blocked

---

### Phase 2: Security Hardening (Week 2-3)

**Goal:** Eliminate remaining critical security vulnerabilities.

**Changes:**
1. **Fix SAML Null Checks** (Issue #1.5)
   - Location: `src/modules/auth/saml_views.py:173-175`
   - Change: Defensive attribute extraction with defaults
   - Prevents: IndexError crashes on SSO

2. **Fix OAuth State Validation** (Issue #5.4)
   - Location: `src/modules/auth/oauth_views.py`
   - Change: Strong state parameter validation
   - Prevents: OAuth CSRF attacks

3. **Sanitize Error Messages** (Issue #5.1 findings)
   - Location: `src/modules/auth/saml_views.py:163,209,243`
   - Change: Generic error messages, log details server-side
   - Prevents: Information disclosure

4. **Add Rate Limiting to MFA Endpoints** (Issue #5.15 findings)
   - Location: `src/modules/auth/mfa_views.py:80,127`
   - Change: Add @ratelimit decorators
   - Prevents: Brute-force TOTP

5. **Scrub Sensitive Data from Logs** (Issue #5.10)
   - Location: `src/api/finance/webhooks.py:112`
   - Change: Redact PII before storing event_data
   - Prevents: PCI-DSS violation

**New Invariants:**
- All auth endpoints rate-limited
- All error messages generic (no stack traces to client)
- All webhook payloads sanitized before storage

---

### Phase 3: Performance Optimization (Week 3-5)

**Goal:** Fix N+1 queries, add pagination, optimize hot paths.

**Changes:**
1. **Add Pagination to All ViewSets** (Issue #4.2)
   - Location: All DRF ViewSets
   - Change: Add `pagination_class = PageNumberPagination`
   - Prevents: Memory exhaustion, slow APIs
   - Why: Issue #4.2 - Missing pagination

2. **Fix N+1 Queries - Calendar** (Issue #4.1)
   - Location: `src/modules/calendar/serializers.py`
   - Change: Add prefetch_related() for hosts, pools
   - Prevents: 80+ queries per API call

3. **Fix N+1 Queries - Automation** (Issue #4.3)
   - Location: `src/modules/automation/views.py:163-166`
   - Change: Single query with prefetch_related
   - Prevents: 10,000 queries for large workflows

4. **Add Query Timeouts Globally** (Issue #4.2 findings)
   - Location: `config/database.py` (new file)
   - Change: Default query timeout 5s
   - Prevents: Slow queries blocking workers

5. **Optimize Invoice Total Calculation** (Issue #4.7)
   - Location: `src/modules/finance/models.py`
   - Change: Denormalize total field + trigger
   - Prevents: O(n) recalculation per access

**New Invariants:**
- All list endpoints paginated (max 100 per page)
- All queries timeout after 5s
- All hot-path queries optimized (< 10ms p95)

**Measurement:**
- Django Debug Toolbar enabled in dev
- Query count assertions in tests
- APM monitoring in production (Sentry)

---

### Phase 4: Type System Hardening (Week 5-6)

**Goal:** Eliminate type unsoundness, enable strict mypy.

**Changes:**
1. **Re-enable MyPy Checks Gradually** (Issue #1.1)
   - Location: `pyproject.toml:70-98`
   - Change: Enable 1 error code per week
   - Prevents: Runtime type errors
   - Why: Issue #1.1 - MyPy effectively disabled

2. **Add Pydantic Schemas for Webhooks** (Issue #1.3)
   - Location: `src/api/finance/webhooks.py`
   - Change: Validate all webhook payloads
   - Prevents: Type coercion bugs

3. **Generate TypeScript Types from DRF** (Issue #1.4)
   - Location: `src/frontend/src/api/types.ts`
   - Tool: drf-spectacular + openapi-typescript
   - Prevents: Frontend/backend contract drift

4. **Add Exhaustiveness Checks** (Issue #1.2)
   - Location: `src/modules/automation/executor.py`
   - Change: Use TypedDict + Literal for node types
   - Prevents: Silent failures on new node types

**New Invariants:**
- All API boundaries validated with Pydantic
- All frontend API calls typed
- All mypy errors are CI failures
- All enum switches exhaustive

---

### Phase 5: Observability & Resilience (Week 6-8)

**Goal:** Make failures visible, add graceful degradation.

**Changes:**
1. **Add React Error Boundaries** (Issue #2.8)
   - Location: `src/frontend/src/App.tsx`
   - Change: Wrap routes in ErrorBoundary
   - Prevents: White screen of death

2. **Add Distributed Tracing** (Issue #CC.1)
   - Tool: OpenTelemetry + Sentry
   - Change: Trace all HTTP requests
   - Prevents: Cannot debug cross-service issues

3. **Add Structured Logging** (Issue #7.7)
   - Location: All modules
   - Change: Use structlog with JSON output
   - Prevents: Inconsistent log levels, missing context

4. **Add Health Check Endpoints** (Issue #CC.3)
   - Location: `config/health.py`
   - Endpoints: `/health/`, `/ready/`, `/live/`
   - Prevents: LB routing to unhealthy pods

5. **Add Background Job Monitoring** (Issue #7.4)
   - Location: Celery/Huey config
   - Change: Sentry integration for worker errors
   - Prevents: Silent job failures

**New Invariants:**
- All requests traced (X-Request-ID header)
- All errors logged with context (user, firm, request)
- All background jobs monitored
- All services have health checks

---

### Phase 6: Testing Infrastructure (Week 8-12)

**Goal:** Increase test coverage from 10% to 60%+.

**Strategy:**
1. **Prioritize by Risk:**
   - Auth flows: 100% coverage required
   - Payment processing: 100% coverage
   - Business logic: 80% coverage
   - Serializers: 60% coverage

2. **Add Contract Tests:**
   - API endpoint tests (Postman/pytest)
   - Frontend/backend integration
   - Webhook replay tests

3. **Add Security Tests:**
   - Timing attack tests (OTP)
   - CSRF protection tests
   - XSS/injection tests
   - Permission boundary tests

4. **Add Performance Tests:**
   - Query count assertions
   - Response time budgets
   - Load testing (Locust)

**New Invariants:**
- All new code must have tests (CI check)
- All security-critical paths: 100% coverage
- All payment paths: 100% coverage
- Overall coverage: 60%+ (CI gate)

---

### Phase 7: Architecture Refactoring (Week 12-20)

**Goal:** Break circular dependencies, extract abstractions.

**Changes:**
1. **Extract Calendar Abstractions** (Issue #3.2)
   - Problem: booking_service ↔ workflow_services circular
   - Solution: Extract interface, use dependency injection
   - Prevents: Tight coupling, testing difficulties

2. **Extract Payment Gateway Abstraction** (Issue #3.4)
   - Problem: Stripe details in view layer
   - Solution: Payment gateway interface + adapters
   - Prevents: Vendor lock-in, testing difficulties

3. **Normalize CRM Model Dependencies** (Issue #3.3)
   - Problem: 9 submodels with circular imports
   - Solution: Define clear boundaries + DTOs
   - Prevents: Refactoring cascades

4. **Add Domain Events** (Issue #3.7)
   - Problem: Finance depends on clients, crm, projects
   - Solution: Event-driven communication
   - Prevents: Tight coupling, prevents microservices

**New Invariants:**
- No circular imports (import-linter enforced)
- All cross-module calls via interfaces or events
- All modules define explicit public API (__all__)

---

## 3. AUTOMATIONS & GUARDRAILS ADDED

### 3.1 Pre-commit Hooks (Enforced Locally)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: black
        name: black
        entry: black
        language: system
        types: [python]
        
      - id: ruff
        name: ruff
        entry: ruff check --fix
        language: system
        types: [python]
        
      - id: mypy
        name: mypy
        entry: mypy
        language: system
        types: [python]
        pass_filenames: false
        args: [src/]
        
      - id: git-secrets
        name: git-secrets
        entry: git-secrets --scan
        language: system
        
      - id: eslint
        name: eslint
        entry: npm run lint
        language: system
        types: [typescript, tsx]
        files: ^src/frontend/
```

**Prevents:**
- Style drift (black, ruff)
- Type errors (mypy)
- Secret leaks (git-secrets)
- Frontend lint errors (eslint)

**Failure Mode:** Commit blocked if any check fails.

---

### 3.2 CI/CD Pipeline (Enforced on PR)

```yaml
# .github/workflows/ci.yml
name: CI

on: [pull_request, push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest --cov=src --cov-fail-under=60
      
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run linters
        run: |
          black --check src/
          ruff check src/
          mypy src/
          
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Security scan
        run: |
          pip-audit --strict
          bandit -r src/
          
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Frontend checks
        run: |
          cd src/frontend
          npm ci
          npm run typecheck
          npm run test
          npm run build
```

**Prevents:**
- Broken tests merging
- Type errors deploying
- Known CVEs in production
- Frontend build failures

**Failure Mode:** PR cannot merge if CI fails.

---

### 3.3 Branch Protection Rules

```yaml
# .github/settings.yml (using Probot)
branches:
  - name: main
    protection:
      required_status_checks:
        strict: true
        contexts:
          - test
          - lint
          - security
          - frontend
      required_pull_request_reviews:
        required_approving_review_count: 1
      enforce_admins: true
      restrictions: null
```

**Prevents:**
- Direct pushes to main
- Merging without code review
- Merging with failing CI

---

### 3.4 Query Performance Monitoring

```python
# config/query_guards.py (enhanced)
from django.db import connection
from django.db.backends.signals import connection_created

def enable_query_logging(sender, connection, **kwargs):
    """Enable query logging and timeouts."""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            # Set statement timeout (5 seconds default)
            cursor.execute("SET statement_timeout = '5s'")
            # Enable query logging for slow queries
            cursor.execute("SET log_min_duration_statement = 100")

connection_created.connect(enable_query_logging)

# In tests: assert query count
from django.test.utils import override_settings
from django.db import connection

@override_settings(DEBUG=True)
def test_list_appointments_query_count(self):
    """Ensure no N+1 queries."""
    with self.assertNumQueries(5):  # 1 auth + 1 appointments + 3 prefetch
        response = self.client.get('/api/calendar/appointments/')
    assert response.status_code == 200
```

**Prevents:**
- Slow queries (> 5s timeout)
- N+1 queries (test assertions)
- Query performance regression (CI)

**Failure Mode:** Query timeout → 500 error. Test fails if query count exceeds limit.

---

### 3.5 Rate Limiting (Global)

```python
# config/middleware.py (new)
from django_ratelimit.decorators import ratelimit
from django.conf import settings

class GlobalRateLimitMiddleware:
    """Apply rate limiting to all endpoints."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip rate limiting for static files
        if request.path.startswith('/static/'):
            return self.get_response(request)
            
        # Apply per-IP rate limit
        @ratelimit(key='ip', rate='100/m', block=True)
        def _rate_limited_view(request):
            return self.get_response(request)
        
        return _rate_limited_view(request)

# settings.py
MIDDLEWARE = [
    'config.middleware.GlobalRateLimitMiddleware',
    # ... other middleware
]
```

**Prevents:**
- DoS attacks
- Brute force attacks
- API abuse

**Failure Mode:** Returns 429 Too Many Requests after limit exceeded.

---

### 3.6 Input Validation (Pydantic Schemas)

```python
# src/api/finance/schemas.py (new)
from pydantic import BaseModel, Field, validator
from decimal import Decimal

class StripePaymentIntentSchema(BaseModel):
    """Validate Stripe payment intent webhook payload."""
    
    id: str = Field(..., min_length=1)
    amount_received: int = Field(..., ge=0)
    currency: str = Field(..., regex=r'^[a-z]{3}$')
    metadata: dict = Field(default_factory=dict)
    
    @validator('amount_received')
    def validate_amount(cls, v):
        """Ensure amount is reasonable."""
        if v > 100_000_00:  # $100k max
            raise ValueError('Amount exceeds maximum')
        return v
    
    def to_dollars(self) -> Decimal:
        """Convert cents to dollars safely."""
        return Decimal(self.amount_received) / 100

# In webhook handler:
def handle_payment_intent_succeeded(payment_intent_data, webhook_event=None):
    try:
        payment_intent = StripePaymentIntentSchema(**payment_intent_data)
        amount_received = payment_intent.to_dollars()
        # ... rest of handler
    except ValidationError as e:
        logger.error(f"Invalid payment intent data: {e}")
        raise
```

**Prevents:**
- Type coercion bugs
- Invalid data crashes
- Business logic errors

**Failure Mode:** Validation error → webhook returns 400, logs error, retries.

---

## 4. CODE DELETIONS JUSTIFIED

### 4.1 Remove Hardcoded Fallback Keys

**File:** `src/modules/core/encryption.py`

**Before:**
```python
backend = os.environ.get("KMS_BACKEND", "local").lower()  # Insecure default
if backend == "aws":
    return AWSKMSBackend()
return LocalKMSBackend(os.environ.get("LOCAL_KMS_MASTER_KEY", "local-dev-master-key"))
```

**After:**
```python
backend = os.environ.get("KMS_BACKEND")
if not backend:
    raise ValueError("KMS_BACKEND environment variable required")
    
if backend.lower() == "aws":
    return AWSKMSBackend()
elif backend.lower() == "local":
    key = os.environ.get("LOCAL_KMS_MASTER_KEY")
    if not key:
        raise ValueError("LOCAL_KMS_MASTER_KEY required for local backend")
    return LocalKMSBackend(key)
else:
    raise ValueError(f"Unknown KMS backend: {backend}")
```

**Why Deleted:** Fallback key exposed in source code. All encrypted data compromised if used.

**Bug Class Prevented:** Hardcoded secrets, insecure defaults.

**Failure Mode:** Application fails to start if env var not set (fail fast).

---

### 4.2 Remove @csrf_exempt from Auth Endpoints

**File:** `src/modules/auth/saml_views.py`

**Before:**
```python
@method_decorator(csrf_exempt, name='dispatch')
class SAMLACSView(View):
    """SAML Assertion Consumer Service."""
    # ...
```

**After:**
```python
class SAMLACSView(View):
    """SAML Assertion Consumer Service with CSRF protection."""
    
    def post(self, request):
        # Validate SAML RelayState matches session
        relay_state = request.POST.get('RelayState')
        expected_state = request.session.get('saml_state')
        
        if not relay_state or relay_state != expected_state:
            return HttpResponse("Invalid SAML state", status=400)
        
        # Clear used state
        del request.session['saml_state']
        # ... rest of handler
```

**Why Deleted:** CSRF protection completely disabled. Account takeover via CSRF possible.

**Bug Class Prevented:** CSRF attacks on authentication flows.

**Failure Mode:** SAML request fails if RelayState invalid (expected behavior).

---

### 4.3 Remove Print Statements

**Files:** Various (6 files with print statements)

**Before:**
```python
print(f"Provisioning firm: {firm_name}")  # Non-production logging
```

**After:**
```python
logger.info("Provisioning firm", extra={"firm_name": firm_name})
```

**Why Deleted:** Print statements don't respect log levels, not structured, not captured by monitoring.

**Bug Class Prevented:** Missing production logs, debugging difficulties.

**Failure Mode:** Logs appear in structured format with context.

---

### 4.4 Remove Unused Imports (Automated)

**Tool:** autoflake

**Command:** `autoflake --remove-all-unused-imports --recursive --in-place src/`

**Why Deleted:** Unused imports increase bundle size, slow builds, confuse readers.

**Bug Class Prevented:** Dependency bloat, security surface area.

**Failure Mode:** Build continues normally without unused imports.

---

## 5. NEW INVARIANTS INTRODUCED

### 5.1 Type System Invariants

**Invariant:** All API boundaries must have Pydantic schemas.

**How Enforced:**
- Code review checklist
- CI check: `grep -r "def post\|def put" src/api/ | xargs check-pydantic-schema.py`
- Pre-commit hook

**How It Fails:** CI fails if API handler lacks schema validation.

**Bug Class Prevented:** Type coercion, invalid data, crashes.

---

### 5.2 Security Invariants

**Invariant:** All authentication endpoints must be rate-limited.

**How Enforced:**
- Code review checklist
- CI check: `grep -r "@api_view" src/modules/auth/ | xargs check-ratelimit-decorator.py`

**How It Fails:** CI fails if auth endpoint lacks @ratelimit.

**Bug Class Prevented:** Brute force attacks, DoS.

---

**Invariant:** All OTP comparisons must use constant-time comparison.

**How Enforced:**
- Bandit security scanner (custom rule)
- Code review

**How It Fails:** `bandit` fails if non-constant-time comparison found in auth code.

**Bug Class Prevented:** Timing attacks, MFA bypass.

---

### 5.3 Performance Invariants

**Invariant:** All list endpoints must be paginated.

**How Enforced:**
- DRF setting: `'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination'`
- CI check: Test all list endpoints return `count`, `next`, `previous`

**How It Fails:** CI test fails if endpoint returns unpaginated list.

**Bug Class Prevented:** Memory exhaustion, DoS, slow APIs.

---

**Invariant:** All database queries must complete within 5 seconds.

**How Enforced:**
- PostgreSQL: `statement_timeout = '5s'`
- Middleware: Query timeout monitoring

**How It Fails:** Query raises `django.db.utils.OperationalError: statement timeout`.

**Bug Class Prevented:** Slow queries blocking workers, DoS.

---

### 5.4 Observability Invariants

**Invariant:** All requests must have X-Request-ID header.

**How Enforced:**
- Middleware: Generate X-Request-ID if missing
- Logger: Include request_id in all log entries

**How It Fails:** Logs include request_id field automatically.

**Bug Class Prevented:** Cannot trace requests across services.

---

**Invariant:** All errors must be logged with structured context.

**How Enforced:**
- Replace all `print()` with `logger.info/error()`
- Pre-commit hook: Block commits with `print(`

**How It Fails:** Pre-commit hook fails if print() detected.

**Bug Class Prevented:** Missing logs, debugging difficulties.

---

### 5.5 Testing Invariants

**Invariant:** All new code must have tests (60%+ coverage).

**How Enforced:**
- CI: `pytest --cov=src --cov-fail-under=60`
- Coverage report in PR comments

**How It Fails:** CI fails if coverage drops below 60%.

**Bug Class Prevented:** Untested code, regressions.

---

## 6. REMAINING KNOWN RISKS (IF ANY)

### 6.1 High-Risk Areas Still Requiring Work

**1. Circular Dependencies in CRM Module**
- **Status:** Identified but not yet refactored (Phase 7)
- **Risk:** Refactoring will touch 9 submodels, high chance of breaking changes
- **Mitigation:** Comprehensive test coverage before refactoring, feature flags
- **Timeline:** Week 12-16

**2. Calendar/Workflow Service Coupling**
- **Status:** Identified but not yet refactored (Phase 7)
- **Risk:** Tight coupling makes testing difficult, delays calendar features
- **Mitigation:** Extract interface, use dependency injection
- **Timeline:** Week 14-18

**3. python3-saml Maintenance**
- **Status:** Library unmaintained for 2+ years (Issue #6.1)
- **Risk:** Security vulnerabilities won't be patched
- **Mitigation:** Evaluate alternatives (T-035 in TODO.md), consider vendor directly
- **Decision Required:** Product owner to confirm SAML usage
- **Timeline:** Week 4 (investigation)

---

### 6.2 Technical Debt Not Addressed

**1. Frontend Type Generation**
- **Status:** Planned (Phase 4) but not prioritized
- **Risk:** Frontend/backend contract drift
- **Mitigation:** Manual API contract tests in interim
- **Timeline:** Week 5-6

**2. Test Coverage Backfill**
- **Status:** Incremental improvement (10% → 60%)
- **Risk:** Legacy code still untested, regressions possible
- **Mitigation:** Prioritize by risk (auth/payment first)
- **Timeline:** Ongoing through Week 12

**3. Microservices Decomposition**
- **Status:** Not planned in this phase
- **Risk:** Monolith performance limits, scaling bottlenecks
- **Mitigation:** Domain events prepare for future decomposition
- **Timeline:** Year 2 (not in scope)

---

### 6.3 External Dependencies

**1. Deployment Platform Decision**
- **Status:** Blocked (T-042 in TODO.md)
- **Risk:** Cannot configure monitoring, alerting, secrets rotation
- **Mitigation:** None until decision made
- **Owner:** Trevor (product owner)
- **Blocking:** Phase 5 (observability), rollout controls

**2. Payment Provider Lock-in**
- **Status:** Tight coupling to Stripe (Issue #3.4)
- **Risk:** Switching providers requires significant refactoring
- **Mitigation:** Payment gateway abstraction (Phase 7)
- **Timeline:** Week 16-18

---

### 6.4 Known Limitations

**1. SQLite in Development**
- **Status:** PostgreSQL-specific features (RLS) not testable locally
- **Risk:** RLS policies not validated until production
- **Mitigation:** Docker Compose with PostgreSQL for dev
- **Timeline:** Week 2

**2. Partial Frontend Coverage**
- **Status:** 68 frontend files, unknown test coverage
- **Risk:** UI regressions not caught
- **Mitigation:** Playwright E2E tests (existing), expand coverage
- **Timeline:** Week 10-12

---

## 7. EXECUTION CHECKLIST

### Week 1: Phase 0 + Phase 1 Start
- [ ] Fix hardcoded encryption key (Issue #5.1)
- [ ] Fix timing attack on OTP (Issue #5.3)
- [ ] Fix CSRF bypass on SAML (Issue #5.2)
- [ ] Fix production Dockerfile (Issue #8.5)
- [ ] Add type validation to webhooks (Issue #1.3)
- [ ] Create GitHub Actions workflow
- [ ] Enable pre-commit hooks
- [ ] Configure dependency scanning

### Week 2-3: Phase 2 (Security)
- [ ] Fix SAML null checks (Issue #1.5)
- [ ] Fix OAuth state validation (Issue #5.4)
- [ ] Sanitize error messages
- [ ] Add rate limiting to MFA
- [ ] Scrub sensitive data from logs

### Week 3-5: Phase 3 (Performance)
- [ ] Add pagination to all viewsets
- [ ] Fix N+1 queries (calendar)
- [ ] Fix N+1 queries (automation)
- [ ] Add query timeouts globally
- [ ] Optimize invoice calculations

### Week 5-6: Phase 4 (Type System)
- [ ] Re-enable MyPy checks gradually
- [ ] Add Pydantic schemas for webhooks
- [ ] Generate TypeScript types from DRF
- [ ] Add exhaustiveness checks

### Week 6-8: Phase 5 (Observability)
- [ ] Add React error boundaries
- [ ] Add distributed tracing
- [ ] Add structured logging
- [ ] Add health check endpoints
- [ ] Add background job monitoring

### Week 8-12: Phase 6 (Testing)
- [ ] Auth flows: 100% coverage
- [ ] Payment processing: 100% coverage
- [ ] Add contract tests
- [ ] Add security tests
- [ ] Add performance tests

### Week 12-20: Phase 7 (Architecture)
- [ ] Extract calendar abstractions
- [ ] Extract payment gateway abstraction
- [ ] Normalize CRM model dependencies
- [ ] Add domain events

---

## 8. SUCCESS CRITERIA

**Production Readiness Checklist:**

- [ ] All P0 security issues resolved (10 issues)
- [ ] CI/CD pipeline operational with 100% PR coverage
- [ ] Test coverage ≥ 60% (currently 10%)
- [ ] All API endpoints paginated
- [ ] All N+1 queries fixed
- [ ] MyPy strict mode enabled
- [ ] Distributed tracing operational
- [ ] Health checks passing
- [ ] Error tracking configured (Sentry)
- [ ] Rate limiting on all endpoints
- [ ] No circular dependencies (import-linter passes)
- [ ] All secrets in environment (no hardcoded values)
- [ ] Production Dockerfile uses gunicorn
- [ ] Branch protection enabled
- [ ] Pre-commit hooks enforced
- [ ] Documentation updated

**Verdict:** SHIPPABLE when all criteria met (estimated Week 20).

---

**End of Refactor Plan**
