# AGENTS.md — Benchmarks Directory

Last Updated: 2026-01-21
Applies To: All agents working in `/benchmarks/`

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.

## Purpose

This directory contains performance benchmarking tools and results for the ConsultantPro platform.

## Structure

```
benchmarks/
├── locustfile.py          # Locust load testing configuration
├── results/               # Benchmark results (timestamped)
└── README.md              # Benchmarking guide
```

## Running Benchmarks

### Load Testing with Locust

```bash
# Basic load test
locust -f benchmarks/locustfile.py --host http://localhost:8000

# Headless mode
locust -f benchmarks/locustfile.py \
  --host http://localhost:8000 \
  --headless \
  --users 10 \
  --spawn-rate 2 \
  --run-time 60s
```

### Query Performance Tests

```bash
# Run performance regression tests
make test-performance

# Or directly with pytest
pytest tests/performance/ -v
```

## Best Practices

### Benchmark Design
- Test realistic user scenarios
- Include multi-tenant isolation in tests
- Measure query counts and response times
- Test both average and peak loads

### Result Storage
- Store results in `results/` with ISO timestamps
- Include environment details (CPU, memory, DB size)
- Compare against baseline results

### Query Budgets
- Use `tests/utils/query_budget.py` to enforce query limits
- Fail tests that exceed query budgets
- Document expected query counts

## Reference

- **Performance Tests**: `tests/performance/`
- **Query Budget Helper**: `tests/utils/query_budget.py`
- **Best Practices**: `/BESTPR.md`
