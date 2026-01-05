# AGENT_ROLES.md — Agent Specialization Matrix

Last Updated: 2026-01-02

Note: Regardless of role, agents must follow READMEAI.md and the output contract. Prefer repo.manifest.yaml for commands and docs/AI_COST_POLICY.md for guard rails.

---

## Agent Specifications

### claude-code-v4
- **Best for**: Architecture, multi-file refactors, security review, complex reasoning.
- **Inputs required**: Repo map, exact file paths, acceptance criteria, and explicit stop rules.
- **Verification expectation**: Must reference concrete evidence (paths/symbols/test output). If not verifiable, mark **UNKNOWN**.
- **Escalate/stop when**: Confidence <80%, requirements ambiguous, or changes touch auth/billing/data integrity without tests.

### github-copilot
- **Best for**: Known-pattern code completion, small scoped edits, boilerplate.
- **Inputs required**: Clear function signatures, enums, and local context in the active file.
- **Verification expectation**: Local build/test must still be run by the driver; copilot output is assumed unverified.
- **Escalate/stop when**: Logic crosses modules, adds new patterns, or involves security-sensitive code.

### perplexity
- **Best for**: Web research, API/docs lookup, comparing vendors/SDKs.
- **Inputs required**: Precise query + constraints (version, platform, dates).
- **Verification expectation**: Capture source links and dates; treat claims as tentative until primary docs confirm.
- **Escalate/stop when**: Sources conflict or information is time-sensitive/high-stakes.

### gemini
- **Best for**: Broad synthesis, product/platform mapping, summarizing large docs.
- **Inputs required**: Clean context dump and explicit output schema.
- **Verification expectation**: Same as research mode—confirm key facts with primary sources.
- **Escalate/stop when**: Output is used for implementation without doc-backed constraints.

## Usage Patterns (Based on Your Current Workflow)

### Complex Architecture & Planning
- **Agent**: Claude Code v4 (Sonnet)
- **Use Case**: High reasoning, multi-file context, architectural decisions
- **Cost Tier**: $$$ (high)
- **Confidence Range**: 85-95%

### Code Generation (Known Patterns)
- **Agent**: GitHub Copilot
- **Use Case**: Fast, low-cost, inline code completion
- **Cost Tier**: $ (low - flat monthly + usage)
- **Confidence Range**: 90-98%

### Research & API Investigation
- **Agent**: Perplexity → Gemini
- **Use Case**: Web access, documentation synthesis, API research
- **Cost Tier**: $$ (medium)
- **Confidence Range**: 80-90%

### Security Auditing
- **Agent**: Claude Code v4
- **Use Case**: Deep analysis, threat modeling, security review
- **Cost Tier**: $$$ (high)
- **Confidence Range**: 80-95%

### Task Execution & Refactoring
- **Agent**: Claude Code v4
- **Use Case**: Agentic capabilities, multi-step refactoring
- **Cost Tier**: $$ (medium)
- **Confidence Range**: 85-95%

## Decision Framework

| Task Complexity | Confidence Range | Primary Agent | Cost Tier | Fallback Agent |
|----------------|------------------|---------------|-----------|----------------|
| Trivial (1 file, <30min) | 90-98% | Copilot | $ (low) | Claude Code |
| Standard (3-5 files, 1-2h) | 85-95% | Claude Code | $$ (med) | Manual review |
| Complex (5+ files, new patterns) | 75-85% | Claude Code | $$$ (high) | Planner Mode |
| Security Critical | 80-90% | Claude Code | $$$ (high) | Human-only |

## Cost Tracking Integration

Each task in specs/project-tasks.md (non-binding notes) (optional, non-binding) should include:
- **agent_recommended**: Based on above matrix
- **budget_allocation**: Estimated tokens/cost
- **confidence_threshold**: Minimum confidence before escalation

### Example Cost Calculations
- Claude Sonnet: ~$3/million tokens
- GitHub Copilot: ~$10/month flat + usage-based
- Perplexity Pro: ~$20/month flat

### Budget Alert Thresholds
- **Green**: >20% budget remaining
- **Yellow**: 10-20% budget remaining (switch to cheaper agents)
- **Red**: <10% budget remaining (human-only, emergency mode)

## Governance Integration

This matrix becomes authoritative for:
- READMEAI.md §2.3: Confidence & Stop Rules
- PROJECT_STATUS.md: agent_last_used field
- Cost optimization decisions
- Agent switching logic

## Agent Selection Algorithm

```
function selectAgent(task, confidence):
    complexity = assessComplexity(task)
    budget = getRemainingBudget()

    if budget < 10%:
        return "human-only"

    if complexity == "trivial" and confidence > 90:
        return "copilot"

    if complexity == "security-critical":
        return "claude-code"

    if confidence < 80:
        return "planner-mode"

    return "claude-code"  # Default for most tasks
```

---

**Note**: This matrix is based on current 2026 agent capabilities and pricing. Review quarterly for updates.
