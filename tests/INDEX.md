# Tests Directory Index

**File**: `tests/INDEX.md`

This file catalogs the test structure in the `tests/` directory. See [root `INDEX.md`](../INDEX.md) for repository overview.

## Test Organization

### Core Test Files
- `conftest.py` - Pytest configuration and fixtures
- `contract_tests.py` - Contract/integration tests
- `__init__.py` - Package initialization

### Module-Specific Tests
Tests organized by backend module (mirrors `backend/modules/` structure):

**Foundation Modules:**
- `core/` - Core utilities tests
- `firm/` - Firm/tenant tests

**Business Modules:**
- `accounting_integrations/` - Accounting integration tests
- `ad_sync/` - Active Directory sync tests
- `assets/` - Asset management tests
- `auth/` - Authentication tests (auth flows, cookie auth, SAML views)
- `automation/` - Automation workflow tests (actions, executor, models, views)
- `calendar/` - Calendar functionality tests
- `clients/` - Client management tests (models, serializers, geographic segmentation)
- `communications/` - Messaging tests
- `config/` - Configuration tests (query monitoring)
- `crm/` - CRM tests (contact graph, deal assignment, deal models, deal rotting, deal stage automation, deal views, serializers)
- `delivery/` - Delivery tests
- `documents/` - Document management tests
- `email_ingestion/` - Email ingestion tests
- `finance/` - Finance and billing tests
- `integrations/` - Integration tests
- `jobs/` - Job queue tests
- `knowledge/` - Knowledge system tests
- `marketing/` - Marketing tests
- `onboarding/` - Onboarding tests
- `orchestration/` - Orchestration tests
- `pricing/` - Pricing tests
- `projects/` - Project management tests
- `recurrence/` - Recurrence engine tests
- `sms/` - SMS tests
- `snippets/` - Snippet tests
- `support/` - Support/ticketing tests
- `tracking/` - Tracking tests
- `webhooks/` - Webhook tests

### Special Test Categories
- `e2e/` - End-to-end system tests
- `edge_cases/` - Edge case tests
- `performance/` - Performance tests
- `safety/` - Safety tests
- `security/` - Security tests

### Test Utilities
- `utils/` - Test utility functions
- `stubs/` - Test stubs and mocks
- `modules/` - Module-level test utilities

## Navigation

- [Root `INDEX.md`](../INDEX.md) - Repository master index
- [`backend/INDEX.md`](../backend/INDEX.md) - Backend directory index

## See Also

- `tests/TESTS.md` - What agents may do in this directory
- `pytest.ini` - Pytest configuration
- [`.repo/policy/QUALITY_GATES.md`](../.repo/policy/QUALITY_GATES.md) - Test requirements
