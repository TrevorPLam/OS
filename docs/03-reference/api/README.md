# API Reference

## OpenAPI Schema (CONST-6)

### Current Status: ⚠️ BLOCKED

The OpenAPI schema generation is currently blocked by the following Django system check errors that must be resolved first:

### Blocking Issues

1. **Admin Configuration Errors (40+ issues)**
   - Multiple admin classes reference non-existent fields
   - Examples:
     - `OnboardingProcessAdmin` references non-existent `kickoff_meeting` field
     - `OnboardingTaskAdmin` references non-existent `assigned_to`, `title`, `is_blocker` fields
     - `OnboardingTemplateAdmin` references non-existent `is_active`, `estimated_days` fields
     - And many more across multiple modules

2. **Index Name Conflicts (30+ issues)**
   - Multiple models share the same index name
   - Examples:
     - `calendar_fir_sta_idx` used by 5 different models
     - `jobs_ide_idx`, `jobs_cor_idx` shared across JobQueue and JobDLQ
     - `pricing_fir_sta_idx` shared across Quote, QuoteVersion, RuleSet
     - And many more

### Resolution Plan

**Phase 1: Fix Admin Configuration (2-3 hours)**
- Review each admin class and remove references to non-existent fields
- Either add missing fields to models or remove from admin configuration
- Priority modules:
  - `modules/onboarding/admin.py`
  - `modules/support/admin.py`
  - `modules/meeting/admin.py`
  - `modules/sms/admin.py`

**Phase 2: Fix Index Name Conflicts (2-3 hours)**
- Rename conflicting index names to be unique
- Use pattern: `{app}_{model}_{fields}_{type}_idx`
- Create migration for index renames
- Priority modules:
  - `modules/calendar/models.py`
  - `modules/jobs/models.py`
  - `modules/pricing/models.py`

**Phase 3: Generate and Commit Schema (30 minutes)**
```bash
make openapi
git add docs/03-reference/api/openapi.yaml
git commit -m "feat(api): Generate and commit OpenAPI schema (CONST-6)"
```

**Phase 4: Add CI Drift Check (30 minutes)**
- Uncomment OpenAPI drift check in `.github/workflows/ci.yml`
- Verify schema generation is deterministic
- Ensure drift check fails if schema changes without update

### Command to Generate Schema

Once blocking issues are resolved:

```bash
cd /home/runner/work/OS/OS
make openapi
```

This will:
1. Create `docs/03-reference/api/openapi.yaml`
2. Generate schema from all DRF ViewSets and Spectacular configuration
3. Include endpoint documentation, request/response schemas, and authentication

### CI Integration

Add to `.github/workflows/ci.yml` after schema is committed:

```yaml
- name: Check OpenAPI schema drift
  run: |
    make openapi
    git diff --exit-code docs/03-reference/api/openapi.yaml || \
      (echo "OpenAPI schema has drifted. Run 'make openapi' and commit changes." && exit 1)
```

## Pagination defaults

API list responses use DRF pagination defaults configured in settings:

- `DEFAULT_PAGINATION_CLASS` points to `config.pagination.BoundedPageNumberPagination`.
- `API_PAGINATION_MAX_PAGE_SIZE` caps `page_size` requests (guardrail set to 100).

**Evidence:** `src/config/settings.py:225-260`, `src/config/pagination.py:1-24`

### Constitution Compliance

Per Constitution Section 7.1:
> "Contracts are the Source of Truth: API schemas (OpenAPI/GraphQL) define the contract."

This schema will serve as:
- Contract definition for all API endpoints
- Source of truth for client SDKs
- Documentation for API consumers
- Drift detection for breaking changes

---

**Last Updated:** December 30, 2025  
**Status:** Blocked by system check errors  
**Tracked in:** P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md CONST-6  
**Related:** IMPLEMENTATION_ASSESSMENT.md (documents admin/model issues)
