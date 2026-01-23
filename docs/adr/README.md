# Architecture Decision Records (ADRs)

**Location:** `docs/adr/`

This directory contains Architecture Decision Records documenting significant architectural decisions made for this repository.

## Purpose

ADRs capture:
- **What** decision was made
- **Why** it was made (context, constraints, trade-offs)
- **Consequences** (positive and negative)
- **Alternatives** considered

## When to Create an ADR

ADRs are **required** when:
- Crossing module/feature boundaries (Principle 23)
- Changing API contracts
- Making database schema changes
- Introducing new architectural patterns
- Making decisions that affect multiple modules

**See:** `.repo/policy/BOUNDARIES.md` for boundary rules

## ADR Format

Each ADR follows the template: `.repo/templates/ADR_TEMPLATE.md`

**Naming:** `ADR-XXXX.md` where XXXX is a sequential number (e.g., `ADR-0001.md`, `ADR-0002.md`)

## Workflow

1. **Detect triggers:** Run `scripts/detect-adr-triggers.sh` to check if ADR is needed
2. **Create ADR:** Use `scripts/create-adr-from-trigger.sh` or manually create from template
3. **Store:** Save in `docs/adr/ADR-XXXX.md`
4. **Link:** Reference ADR in PR description

## ADR Status

- **Proposed** - Decision is being considered
- **Accepted** - Decision has been made and implemented
- **Deprecated** - Decision has been superseded
- **Superseded** - Replaced by another ADR

## Related Documentation

- `.repo/policy/BOUNDARIES.md` - Module boundary rules
- `.repo/policy/PRINCIPLES.md` - Principle 23: ADR Required When Triggered
- `.repo/templates/ADR_TEMPLATE.md` - ADR template
- `scripts/detect-adr-triggers.sh` - Detect if ADR needed
- `scripts/create-adr-from-trigger.sh` - Create ADR from trigger

---

**Note:** ADRs are living documents. Update them when decisions change or are superseded.
