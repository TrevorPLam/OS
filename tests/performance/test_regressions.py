import pytest


@pytest.mark.performance
@pytest.mark.django_db
class TestRegressionPerformance:
    """Guardrails for query shapes and pagination once implemented."""

    @pytest.mark.xfail(reason="Tenant index auditing not implemented")
    def test_tenant_scoped_indexes_present(self):
        pytest.xfail("Pending tenant-aware index validation and query plan checks")

    @pytest.mark.xfail(reason="Pagination performance tests not implemented")
    def test_paginated_list_efficiency(self):
        pytest.xfail("Pending pagination regression benchmarks")

    @pytest.mark.xfail(reason="Relation loading efficiency tests not implemented")
    def test_relation_prefetching_efficiency(self):
        pytest.xfail("Pending relation loading performance checks")
