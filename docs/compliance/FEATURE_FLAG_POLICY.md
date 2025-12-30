# Feature Flag Policy (CONST-12)

**Constitution Requirement**: Section 11.6 - Feature flags must have owners, cleanup dates, and removal plans.

**Date Documented**: December 30, 2025  
**Status**: ✅ **COMPLIANT** (No feature flags currently in use)

## Current State

**Feature Flags in Codebase**: 0

As of December 30, 2025, the ConsultantPro codebase does not use feature flags. All features are deployed directly without toggle mechanisms.

## Feature Flag Policy

When feature flags are introduced in the future, they MUST follow these requirements to maintain Constitution compliance:

### 1. Required Metadata

Every feature flag MUST include:

```python
FEATURE_FLAGS = {
    "feature_name": {
        "owner": "team-or-person@example.com",  # REQUIRED
        "created_date": "2025-01-15",            # REQUIRED
        "cleanup_date": "2025-04-15",            # REQUIRED (max 90 days from creation)
        "removal_plan": "...",                   # REQUIRED
        "description": "...",                    # REQUIRED
        "enabled": False,                        # Default state
        "environments": ["dev", "staging"],      # Optional scope
    }
}
```

### 2. Ownership Requirements

- **Owner**: Must be a specific person or team with email contact
- **Responsibility**: Owner is accountable for flag cleanup
- **Handoff**: If owner changes, update the metadata immediately

### 3. Cleanup Date Requirements

- **Maximum Lifetime**: 90 days from creation date
- **Extension**: Requires explicit approval and documentation
- **Enforcement**: Automated checks warn when cleanup date approaches
- **Overdue**: Flags past cleanup date trigger build warnings

### 4. Removal Plan Requirements

Each flag must document:

1. **Purpose**: Why the flag exists
2. **Success Criteria**: When to remove the flag
3. **Rollback Plan**: How to disable if issues arise
4. **Cleanup Steps**: Specific code removal tasks
5. **Testing Requirements**: How to verify removal is safe

### Example Removal Plan

```markdown
## Removal Plan: new_billing_engine

**Purpose**: Gradual rollout of refactored billing calculation engine

**Success Criteria**:
- Feature enabled for 100% of tenants for 14+ days
- No P0/P1 incidents related to billing calculations
- All regression tests passing
- Customer satisfaction metrics stable

**Rollback Plan**:
1. Set flag to False in settings
2. Deploy immediately
3. Monitor for 24 hours
4. Incident response team notified

**Cleanup Steps**:
1. Remove flag check from `src/modules/finance/billing.py` (lines 45-52)
2. Delete old billing calculation code (lines 120-245)
3. Remove flag from settings.py
4. Update tests to remove flag-conditional logic
5. Update documentation to remove feature flag references

**Testing Requirements**:
- Run full billing test suite
- Manual smoke test on staging environment
- Verify no references to flag name in codebase
```

## Implementation Guidelines

### Adding a Feature Flag

1. **Document First**: Create removal plan before implementing flag
2. **Set Cleanup Date**: Max 90 days from today
3. **Add to Registry**: Update FEATURE_FLAGS dictionary
4. **Code Review**: Flag metadata reviewed in PR
5. **Monitor Usage**: Track flag evaluation metrics

### Flag Lifecycle

```
Created → Enabled (Gradually) → Fully Rolled Out → Cleanup Date Reached → Removed
   ↓                ↓                  ↓                    ↓               ↓
Day 0           Days 1-30         Days 30-60          Day 90         Day 90+
```

### Flag Hygiene

**Weekly Review**:
- Check flags approaching cleanup date
- Verify owners are still responsible
- Update plans if circumstances change

**Monthly Audit**:
- List all active flags
- Report overdue flags
- Plan removal sprints

**Automated Checks**:
- CI fails if flag missing required metadata
- CI warns if flag approaching cleanup date (7 days)
- CI fails if flag is past cleanup date

## Flag Registry

### Active Feature Flags

| Flag Name | Owner | Created | Cleanup Date | Status | Purpose |
|-----------|-------|---------|--------------|--------|---------|
| _(none)_ | - | - | - | - | - |

### Recently Removed Flags

| Flag Name | Removed Date | Duration | Final Owner | Removal Notes |
|-----------|--------------|----------|-------------|---------------|
| _(none)_ | - | - | - | - |

## Monitoring and Enforcement

### CI Integration

Add to `.github/workflows/ci.yml`:

```yaml
- name: Feature Flag Compliance Check
  run: |
    python scripts/check_feature_flags.py --strict
```

### Compliance Script

Create `scripts/check_feature_flags.py`:

```python
#!/usr/bin/env python3
"""
Feature flag compliance checker.
Validates all flags have required metadata and cleanup dates.
"""
import sys
from datetime import datetime, timedelta
from config.settings import FEATURE_FLAGS

def check_compliance():
    errors = []
    warnings = []
    
    for flag_name, flag_data in FEATURE_FLAGS.items():
        # Check required fields
        required = ["owner", "created_date", "cleanup_date", "removal_plan", "description"]
        for field in required:
            if field not in flag_data:
                errors.append(f"Flag '{flag_name}' missing required field: {field}")
        
        # Check cleanup date
        if "cleanup_date" in flag_data:
            cleanup = datetime.strptime(flag_data["cleanup_date"], "%Y-%m-%d")
            created = datetime.strptime(flag_data["created_date"], "%Y-%m-%d")
            today = datetime.now()
            
            # Max 90 days
            if (cleanup - created).days > 90:
                errors.append(f"Flag '{flag_name}' cleanup date exceeds 90-day maximum")
            
            # Approaching cleanup
            if (cleanup - today).days <= 7 and (cleanup - today).days >= 0:
                warnings.append(f"Flag '{flag_name}' cleanup date in {(cleanup - today).days} days")
            
            # Overdue
            if cleanup < today:
                errors.append(f"Flag '{flag_name}' is past cleanup date (cleanup: {flag_data['cleanup_date']})")
    
    # Print results
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
    
    if errors:
        print("\n❌ ERRORS:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("✅ All feature flags compliant")
        sys.exit(0)

if __name__ == "__main__":
    check_compliance()
```

## Best Practices

### DO ✅

- Use feature flags for gradual rollouts of significant changes
- Set aggressive cleanup dates (30-60 days ideal)
- Remove flags as soon as fully rolled out
- Document removal plans thoroughly
- Use flags for A/B testing with clear end dates

### DON'T ❌

- Use feature flags for permanent configuration (use settings instead)
- Leave flags in place "just in case" after rollout
- Let flags accumulate without cleanup
- Use flags for environment-specific behavior (use settings)
- Create flags without clear removal criteria

## Future Enhancements

When feature flags are implemented, consider:

1. **Feature Flag Service**: LaunchDarkly, Split.io, or Unleash
2. **Dynamic Flags**: Database-backed flags for runtime control
3. **Gradual Rollouts**: Percentage-based or tenant-based rollouts
4. **A/B Testing**: Statistical analysis of flag variations
5. **Kill Switches**: Emergency disable capabilities

## Related Documentation

- Constitution Section 11.6: Feature Flags ✅ Policy Documented
- [Deployment Runbook](../runbooks/DEPLOYMENT.md)
- [Rollback Procedures](../runbooks/ROLLBACK.md)

## Compliance Checklist

- [x] Feature flag policy documented
- [x] Required metadata defined
- [x] Cleanup date requirements established (max 90 days)
- [x] Removal plan template created
- [x] Flag registry structure defined
- [ ] Automated compliance checking (implement when first flag added)
- [ ] CI integration (implement when first flag added)
- [ ] Monitoring dashboards (implement when first flag added)

## Review Schedule

- **Next Review**: When first feature flag is added
- **Regular Reviews**: Weekly during active flag periods
- **Audit Frequency**: Monthly when flags are in use

---

**Note**: This policy is currently theoretical as no feature flags exist in the codebase. When the first feature flag is added, implement the automated compliance checking and CI integration described above.
