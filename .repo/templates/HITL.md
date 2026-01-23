# HITL: [Short Description]

**HITL ID**: HITL-YYYY-MM-DD-description  
**Created**: YYYY-MM-DD  
**Author**: [Agent or Person]  
**Category**: External Integration | Clarification | Risk | Security | Architecture | Compliance  
**Priority**: Critical | High | Medium | Low  
**Status**: Pending | In Progress | Blocked | Completed | Superseded

## Summary

[One-sentence description of what requires human decision]

Example: Approval needed for Stripe payment integration to process customer payments.

## Context

### What Needs Human Decision
[Clear description of the decision or approval needed]

### Why HITL Was Triggered
[Automatic trigger or manual reason]

Example:
**Trigger**: External system integration detected (Stripe payment API)
**Policy**: Article 8 - All external systems require HITL approval
**Risk**: Payment processing, PII data, compliance

### Current State
[What has been done so far]

Example:
- Evaluated 3 payment processors (Stripe, PayPal, Square)
- Selected Stripe based on requirements
- Reviewed API documentation
- Created proof-of-concept integration
- Need approval to proceed with full implementation

## Options

### Option 1: [Name]
**Description**: [What this option entails]

**Pros**:
- Pro 1
- Pro 2

**Cons**:
- Con 1
- Con 2

**Cost**: [If applicable]  
**Timeline**: [If applicable]  
**Risk**: 🟢 Low | 🟡 Medium | 🔴 High

### Option 2: [Name]
[Same structure as Option 1]

### Recommended Option
[Agent's recommendation if confident, or "UNKNOWN - Human decision required"]

## Questions for Human

[Specific questions that need human judgment]

1. Question 1?
2. Question 2?
3. Question 3?

Example:
1. Approve Stripe integration for payment processing?
2. Acceptable to share customer email, name with Stripe?
3. Approve $50/month base + 2.9% + $0.30 per transaction cost?
4. Timeline: 2 weeks for implementation - acceptable?

## Impact Analysis

### Scope
[What parts of the system are affected]

Example:
- Checkout flow (frontend + backend)
- Order processing
- Invoice generation
- Customer billing records

### Users Affected
[Percentage or description]

Example: All users making purchases (100% of paying customers)

### Risk Level
**Overall Risk**: 🔴 High | 🟡 Medium | 🟢 Low

**Risk Breakdown**:
- Security: [Level and details]
- Privacy: [Level and details]
- Financial: [Level and details]
- Technical: [Level and details]

Example:
**Overall Risk**: 🟡 Medium

**Risk Breakdown**:
- Security: 🟢 Low - Stripe is PCI DSS Level 1 certified
- Privacy: 🟡 Medium - Share name, email, amount with Stripe
- Financial: 🟡 Medium - Payment failures could lose sales
- Technical: 🟢 Low - Well-documented API, many integrations exist

### Rollback Complexity
**Rollback**: Easy | Medium | Hard

**Rollback Plan**: [How to undo]

Example:
**Rollback**: Easy  
**Rollback Plan**: 
1. Feature flag: Set ENABLE_STRIPE=false
2. Revert to manual payment processing (phone/invoice)
3. Stripe account can be deactivated anytime
4. No data loss (orders stored locally)

## Security Considerations

[Any security implications]

**Data Shared**:
- Data item 1
- Data item 2

**Data Stored**:
- What Stripe stores
- What we store

**Credentials**:
- How stored
- Who has access

**Compliance**:
- GDPR considerations
- PCI DSS requirements
- Other regulations

Example:
**Data Shared with Stripe**:
- Customer name
- Customer email
- Amount to charge
- Currency
- Order ID (for tracking)

**Data Stored**:
- Stripe: Card details (tokenized, we never see full card)
- Our DB: Stripe customer ID, transaction ID, amount, status

**Credentials**:
- Stripe API keys stored in environment variables
- Never committed to code
- Access: Only backend servers + DevOps team

**Compliance**:
- GDPR: Stripe is GDPR compliant, DPA signed
- PCI DSS: Stripe handles card data (we're PCI DSS exempt)
- Privacy policy: Must update to mention Stripe

## Compliance Considerations

[GDPR, CCPA, SOC2, etc.]

Example:
- **GDPR**: Stripe has signed Data Processing Agreement (DPA)
- **CCPA**: California users can request deletion (via Stripe)
- **Privacy Policy**: Must be updated to disclose Stripe usage
- **Terms of Service**: Must include Stripe's terms

## Technical Details

**Integration Approach**: [How it will work]

**API Endpoints**: [What endpoints will be used]

**Libraries/SDKs**: [What libraries needed]

**Testing**: [How it will be tested]

Example:
**Integration Approach**:
1. Frontend: Collect card via Stripe Elements (PCI compliant)
2. Frontend: Create payment intent via our API
3. Backend: Call Stripe API to process payment
4. Backend: Handle webhooks for payment status

**API Endpoints**:
- POST /payments/create - Create payment intent
- POST /payments/confirm - Confirm payment
- POST /webhooks/stripe - Receive payment status

**Libraries/SDKs**:
- @stripe/stripe-js (frontend)
- stripe (backend Node SDK)

**Testing**:
- Unit tests with Stripe test mode
- Integration tests with Stripe test cards
- Manual testing in Stripe dashboard

## Recommendation

[Agent's recommendation with reasoning, or state UNKNOWN]

Example:
**Recommendation**: Approve Stripe integration

**Reasoning**:
- Industry standard (trusted by millions)
- Best pricing for our volume
- Excellent documentation and support
- PCI DSS compliant (reduces our compliance burden)
- Easy integration (2-3 days)
- Low risk with feature flag rollback

## Cost Analysis

[If applicable]

Example:
**Monthly Cost**: $50 base + 2.9% + $0.30 per transaction

**Projected Costs** (based on 1,000 transactions/month averaging $50):
- Base: $50/month
- Transaction fees: $1,750/month (2.9% + $0.30 × 1,000)
- Total: ~$1,800/month

**Alternatives**:
- PayPal: 3.49% + $0.49 = ~$2,200/month (22% more expensive)
- Square: 2.9% + $0.30 = Same as Stripe
- Custom: Dev cost $50k + maintenance + PCI compliance

## Dependencies

[What must be in place first]

- [ ] Stripe account created
- [ ] API keys obtained
- [ ] DPA signed
- [ ] Privacy policy updated
- [ ] Terms of service updated

## Decision

**Date**: YYYY-MM-DD  
**Decided By**: [Name/Email]  
**Decision**: Approved | Rejected | Needs More Info

### Rationale
[Why this decision was made]

### Conditions (if approved)
- [ ] Condition 1
- [ ] Condition 2

Example:
**Conditions**:
- [ ] Privacy policy must be updated before launch
- [ ] Security team reviews webhook implementation
- [ ] Rate limiting added to payment endpoints
- [ ] Monitoring and alerting set up for payment failures

### Follow-Up Actions
- [ ] Action 1
- [ ] Action 2

Example:
**Follow-Up Actions**:
- [ ] Create TASK-XXX: Implement Stripe integration
- [ ] Schedule security review
- [ ] Update privacy policy
- [ ] Set up monitoring dashboard

## Resolution

**Resolved Date**: YYYY-MM-DD  
**Resolution**: [Summary of how this was resolved]

**PR Status**: Merged | Closed | Pending

**Archived**: YYYY-MM-DD

Example:
**Resolved Date**: 2024-01-20  
**Resolution**: Stripe integration approved with security conditions. Implementation completed and deployed to production.

**PR Status**: Merged (#456, #457, #458)

**Archived**: 2024-01-25

## Lessons Learned

[What was learned from this HITL item]

Example:
- External integrations benefit from early HITL (avoided rework)
- Cost analysis helped justify decision
- Security review upfront prevented issues later
- Feature flag enabled safe rollout

## Related Documents

- PR: #456
- ADR: ADR-067 (Use Stripe for payments)
- Task: TASK-234
- Security Review: /docs/security/stripe-review.md
- Privacy Policy: /docs/legal/privacy-policy.md

---

## Example HITL

[See filled example above]
