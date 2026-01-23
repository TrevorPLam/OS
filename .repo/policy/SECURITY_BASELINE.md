# Security Baseline Configuration

This document defines the security baseline for the repository. Security is non-negotiable and non-waiverable.

## Dependency Vulnerability Checks

**Policy**: `always_hitl`

### Description
All dependency vulnerabilities require Human-In-The-Loop (HITL) review and approval before proceeding.

### Process
1. Automated dependency scanning runs on every PR
2. Any vulnerability detected triggers HITL item creation
3. Security team reviews vulnerability severity and impact
4. Decision made: accept risk, update dependency, or find alternative
5. HITL item must be resolved before PR can merge

### Tools
- npm audit (frontend)
- pip safety check (backend)
- Dependabot alerts
- Snyk or similar scanning

### Severity Levels
- **Critical**: Immediate HITL, blocks all work
- **High**: HITL within 24 hours, blocks merge
- **Medium**: HITL within 1 week, waiver allowed with plan
- **Low**: Tracked, addressed in regular maintenance

---

## Secrets Handling

**Policy**: `absolute_prohibition`

### Description
Secrets MUST NEVER be committed to the repository. No exceptions, no waivers.

### What Are Secrets
- API keys
- Passwords
- Private keys
- Access tokens
- Database credentials
- SSL certificates
- OAuth secrets
- Any credential or authentication material

### Prevention
1. **Pre-commit hooks**: Scan for patterns matching secrets
2. **CI/CD scanning**: git-secrets, truffleHog, detect-secrets
3. **Code review**: Manual verification
4. **Training**: Regular security awareness

### If Secret Is Committed
1. **STOP**: Immediately halt all operations
2. **Revoke**: Rotate/revoke the exposed secret immediately
3. **Remove**: Rewrite git history to remove secret
4. **Document**: Create incident report
5. **Review**: Audit for any unauthorized access
6. **Improve**: Update prevention mechanisms

### Proper Secret Management
- Use environment variables
- Use secret management services (AWS Secrets Manager, HashiCorp Vault)
- Use .env files (never committed, in .gitignore)
- Use .env.example templates (with placeholder values)
- Document required secrets in README

---

## Security Review Triggers

**Triggers**: [1, 2, 4, 5, 6, 8, 9, 10]

### When Security Review Is Required

These changes automatically trigger mandatory security review:

**1. Authentication/Authorization Changes**
- Login/logout functionality
- Permission checks
- Role-based access control (RBAC)
- Token generation/validation
- Session management

**2. Data Privacy/PII Handling**
- Collection of personal information
- Storage of sensitive data
- Data encryption/decryption
- Data export/deletion
- Compliance requirements (GDPR, CCPA)

**4. External API Integration**
- Third-party service integration
- Webhook handlers
- API client implementations
- Cross-origin requests
- External data ingestion

**5. Database Schema Changes**
- Table creation/modification
- Index changes
- Migration scripts
- Constraint modifications
- Data model changes

**6. File Upload/Download**
- File upload endpoints
- File storage logic
- File serving/download
- File type validation
- Size limit enforcement

**8. Payment/Financial Operations**
- Payment processing
- Transaction handling
- Refund logic
- Billing calculations
- Financial reporting

**9. Cryptographic Operations**
- Hashing algorithms
- Encryption/decryption
- Key generation
- Certificate handling
- Random number generation

**10. Configuration/Environment Changes**
- Environment variable changes
- Configuration file modifications
- Feature flag changes
- Infrastructure changes
- Deployment configuration

### Review Process
1. PR author flags security trigger in description
2. HITL item created automatically
3. Security reviewer assigned
4. Security checklist completed
5. Approval required before merge

---

## Forbidden Patterns

**Patterns**: [A, B, C, D, E, F, G, H]

### Patterns That Must Never Appear in Code

These patterns are forbidden and automatically block merge:

**A. Hardcoded Credentials**
```javascript
// FORBIDDEN
const apiKey = "sk_live_1234567890abcdef";
const password = "admin123";
```

**B. SQL Injection Vulnerabilities**
```python
# FORBIDDEN
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")
```
Use parameterized queries instead.

**C. Command Injection Vulnerabilities**
```javascript
// FORBIDDEN
exec(`git clone ${userInput}`);
eval(userInput);
```

**D. Cross-Site Scripting (XSS) Vulnerabilities**
```javascript
// FORBIDDEN
element.innerHTML = userInput;
document.write(untrustedData);
```
Use proper escaping and sanitization.

**E. Path Traversal Vulnerabilities**
```python
# FORBIDDEN
file_path = os.path.join(base_dir, user_input)
open(f"/var/data/{filename}")
```
Validate and sanitize file paths.

**F. Insecure Randomness**
```javascript
// FORBIDDEN for security purposes
Math.random(); // OK for UI, NOT for crypto
```
Use crypto.randomBytes() for security-critical randomness.

**G. Insecure Deserialization**
```python
# FORBIDDEN
pickle.loads(untrusted_data)
eval(json_string)
```

**H. Debugging/Logging Sensitive Data**
```javascript
// FORBIDDEN
console.log("User password:", password);
logger.info("Credit card:", creditCardNumber);
```

### Detection
- Static analysis tools scan for these patterns
- Pre-commit hooks catch common violations
- Code review checklist includes pattern verification
- CI/CD blocks merge on detection

### Remediation
If forbidden pattern detected:
1. Block merge immediately
2. Create HITL security review
3. Author must rewrite code
4. Security team verifies fix
5. Document lesson learned

---

## Security Check Frequency

**Frequency**: `every_pr`

### What Is Checked
Security scans run on every Pull Request:

1. **Dependency Vulnerabilities**: npm audit, pip safety
2. **Secret Scanning**: git-secrets, detect-secrets
3. **Static Analysis**: Semgrep, Bandit, ESLint security plugins
4. **License Compliance**: Check for prohibited licenses
5. **Forbidden Patterns**: Custom regex patterns
6. **Code Quality**: Security-focused linting rules

### Continuous Monitoring
In addition to PR checks:
- Daily dependency scans on main branch
- Weekly full security audit
- Monthly penetration testing
- Quarterly security review

### Check Results
- **Pass**: Green checkmark, proceed
- **Warning**: Yellow flag, review recommended
- **Fail**: Red X, blocks merge
- **Critical**: Immediate alert, stop all work

---

## Evidence Requirements

**Standard**: `standard`

### What Evidence Is Required

For security-related changes, provide:

1. **Threat Model**: What threats does this address?
2. **Security Analysis**: How is this secure?
3. **Test Evidence**: Security tests pass
4. **Code Review**: Security-trained reviewer approved
5. **Documentation**: Security considerations documented

### Evidence Format
Include in PR description:
```markdown
## Security Evidence

**Threat Model**: [Describe threats addressed]

**Security Analysis**: [Explain security measures]

**Tests**: 
- [ ] Authentication tests pass
- [ ] Authorization tests pass
- [ ] Input validation tests pass
- [ ] Security regression tests pass

**Review**: Security reviewer: @username

**Documentation**: Updated in [file path]
```

---

## Mandatory HITL Actions

**Actions**: [1, 2, 3, 4, 5, 6, 7, 8]

### These Actions Always Require HITL Approval

**1. Production Deployment**
- Any deployment to production environment
- Approval from on-call engineer
- Rollback plan verified

**2. Database Migration**
- Schema changes
- Data migrations
- Approval from database administrator
- Rollback tested

**3. Security Configuration Changes**
- Firewall rules
- Access control policies
- SSL/TLS configuration
- Approval from security team

**4. Dependency Major Version Upgrade**
- Breaking changes in dependencies
- Compatibility verified
- Tests pass with new version
- Approval from tech lead

**5. External System Integration**
- New third-party service
- Vendor contract reviewed
- Security assessment completed
- Approval from security and legal

**6. PII Data Collection**
- New personal information collected
- Privacy policy updated
- Compliance verified
- Legal approval obtained

**7. Payment Processing Changes**
- Payment flow modifications
- Financial testing completed
- Fraud prevention verified
- Finance team approval

**8. Infrastructure Changes**
- Server provisioning
- Network configuration
- Resource scaling
- DevOps approval

### HITL Process
1. PR author creates HITL item
2. Appropriate reviewer assigned based on action type
3. Reviewer evaluates request
4. Decision: Approve, Request Changes, or Reject
5. HITL item closed with decision
6. If approved, PR can proceed

### HITL Response SLA
- Critical: 1 hour
- High: 4 hours
- Medium: 24 hours
- Low: 3 days

---

## Security Incident Response

### If Security Issue Is Discovered

1. **Report**: Immediately report to security team
2. **Assess**: Evaluate severity and impact
3. **Contain**: Limit exposure if active incident
4. **Fix**: Develop and test patch
5. **Deploy**: Emergency deployment if critical
6. **Document**: Create incident report
7. **Review**: Post-mortem and lessons learned
8. **Improve**: Update security measures

### Severity Classification
- **Critical**: Active exploitation, data breach
- **High**: Exploitable vulnerability, limited exposure
- **Medium**: Vulnerability requires specific conditions
- **Low**: Theoretical or difficult to exploit

---

## Security Training

### Required Training
All developers must complete:
- OWASP Top 10 awareness
- Secure coding practices
- Secrets management
- Incident response procedures

### Ongoing Education
- Monthly security tips
- Quarterly security workshops
- Annual security certification
- Security champions program

---

## Compliance

### Standards Followed
- OWASP Top 10
- CWE Top 25
- NIST Cybersecurity Framework
- Industry-specific regulations (HIPAA, PCI-DSS, SOC 2)

### Audit Trail
- All security decisions documented
- HITL items archived
- Security reviews recorded
- Incidents logged

---

## Related Documents

- **Governance**: `/.repo/GOVERNANCE.md`
- **Principles**: `/.repo/policy/PRINCIPLES.md`
- **Quality Gates**: `/.repo/policy/QUALITY_GATES.md`
- **HITL System**: `/.repo/policy/HITL.md`
- **Incident Response**: `/.repo/docs/security/incident-response.md`
