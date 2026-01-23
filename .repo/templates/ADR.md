# ADR Template

## ADR-XXX: [Short Title]

**Status**: Proposed | Accepted | Deprecated | Superseded  
**Date**: YYYY-MM-DD  
**Author**: [Name]  
**Supersedes**: ADR-YYY (if applicable)  
**Superseded by**: ADR-ZZZ (if applicable)

## Context

[Describe the situation, problem, or decision that needs to be made. Keep it concise - 2-3 paragraphs max.]

### Background
[What led to this decision being necessary?]

### Problem
[What specific problem are we solving?]

### Constraints
[What constraints exist? Technical, business, timeline, etc.]

## Decision

[Clear statement of the decision made]

Example: We will use JWT (JSON Web Tokens) for authentication instead of session-based authentication.

## Rationale

[Why this decision was made - the reasoning]

Bullet points work well:
- Reason 1
- Reason 2
- Reason 3

Example:
- Stateless authentication scales horizontally
- Mobile apps can store tokens easily
- Industry standard with good library support
- No server-side session storage needed

## Alternatives Considered

### Alternative 1: [Name]
**Pros**:
- Pro 1
- Pro 2

**Cons**:
- Con 1
- Con 2

**Why Rejected**: [Reason]

### Alternative 2: [Name]
**Pros**:
- Pro 1

**Cons**:
- Con 1

**Why Rejected**: [Reason]

## Consequences

### Positive
- Benefit 1
- Benefit 2

### Negative
- Drawback 1
- Drawback 2

### Neutral
- Trade-off 1
- Trade-off 2

### Risks
- Risk 1 with mitigation
- Risk 2 with mitigation

Example:
### Positive
- Scalable across multiple servers
- Mobile-friendly
- Industry standard

### Negative
- Tokens can't be easily revoked
- Need refresh token mechanism
- Token size larger than session ID

### Neutral
- Requires client-side storage (localStorage or cookie)
- Need to handle token expiration

### Risks
- Token theft if XSS vulnerability exists
  - Mitigation: Use HttpOnly cookies, implement CSP

## Implementation

[High-level implementation plan]

### Files Affected
- `/path/to/file1.ts` - What changes
- `/path/to/file2.ts` - What changes

### Steps
1. Step 1
2. Step 2
3. Step 3

### Timeline
- Phase 1: [Date range]
- Phase 2: [Date range]

## Monitoring & Validation

[How will we know if this decision was correct?]

### Success Metrics
- Metric 1: Target value
- Metric 2: Target value

### Monitoring
- What to monitor
- Alert thresholds

Example:
### Success Metrics
- Authentication latency: <100ms p95
- Token expiration rate: <1% complaints
- Security incidents: 0

### Monitoring
- Track authentication failures
- Monitor token refresh rate
- Alert on unusual token patterns

## Related Documents

- ADR-YYY: [Related ADR]
- Task: TASK-XXX
- PR: #XXX
- Documentation: [Link]

## Notes

[Any additional context, links, or information]

---

## Example ADR

# ADR-042: Use JWT for Authentication

**Status**: Accepted  
**Date**: 2024-01-15  
**Author**: Tech Lead

## Context

We need an authentication system for our API. The system must support:
- Web application
- Mobile applications (iOS, Android)
- Third-party integrations (future)

Current state: No authentication implemented yet.

### Constraints
- Must scale to 100k users
- Must work across multiple servers
- Must support mobile clients
- Must be secure
- Must be implementable in 2 weeks

## Decision

We will use JWT (JSON Web Tokens) for authentication.

## Rationale

- **Stateless**: No server-side session storage needed, scales horizontally
- **Standard**: RFC 7519, widely adopted, good library support
- **Mobile-friendly**: Tokens easily stored and sent by mobile apps
- **Self-contained**: Token contains user info, reduces database queries
- **Cross-domain**: Works across different domains/services

## Alternatives Considered

### Alternative 1: Session-based Authentication
**Pros**:
- Easy to revoke sessions
- Smaller session ID
- Familiar pattern

**Cons**:
- Requires session store (Redis, DB)
- Harder to scale horizontally
- Adds infrastructure complexity

**Why Rejected**: Scalability concerns and infrastructure overhead

### Alternative 2: OAuth 2.0
**Pros**:
- Industry standard for third-party auth
- Good for social login

**Cons**:
- Overkill for first-party authentication
- More complex implementation
- Not needed yet

**Why Rejected**: Too complex for current needs; can add later for third-party integrations

## Consequences

### Positive
- Scalable: Works across multiple servers
- Fast: No session lookup needed
- Mobile-friendly: Easy to implement in mobile apps
- Flexible: Can add claims to token

### Negative
- Can't revoke tokens easily (need short expiration + refresh tokens)
- Token size (~200 bytes) vs session ID (~16 bytes)
- Must implement refresh token mechanism

### Neutral
- Need to store tokens in client (localStorage or HttpOnly cookie)
- Token expiration requires re-authentication

### Risks
- Token theft via XSS
  - Mitigation: Use HttpOnly cookies, implement CSP, keep tokens short-lived
- Token forgery
  - Mitigation: Use strong secret key, validate signature

## Implementation

### Files Affected
- `/src/auth/login/domain/authService.ts` - Token generation
- `/src/auth/middleware/authMiddleware.ts` - Token validation
- `/src/platform/api/client.ts` - Token interceptor

### Steps
1. Install jsonwebtoken library
2. Implement token generation in login
3. Implement token validation middleware
4. Add refresh token endpoint
5. Update API client to include token in requests

### Timeline
- Week 1: Core implementation (generation, validation)
- Week 2: Refresh tokens, testing, documentation

## Monitoring & Validation

### Success Metrics
- Authentication latency: <100ms p95
- Login success rate: >99%
- Zero security incidents

### Monitoring
- Track authentication failures
- Monitor token refresh patterns
- Alert on unusual activity (brute force, token reuse)

## Related Documents

- Security Baseline: `/.repo/policy/SECURITY_BASELINE.md`
- Task: TASK-089
- PR: #234

## Notes

- Secret key stored in environment variable (never committed)
- Token expiration: 15 minutes (short-lived)
- Refresh token expiration: 7 days
- Algorithm: HS256 (symmetric signing)
- Future: Consider RS256 (asymmetric) for microservices
