# TIER 5.2: Performance Index Audit & Recommendations

**Date:** December 25, 2025
**Purpose:** Audit and optimize database indexes for production scale

---

## Strategy

### Index Types

1. **Firm Scoping Indexes** - Most critical for multi-tenant performance
   - Pattern: `(firm, <filter_field>, -created_at)`
   - Supports: Firm-scoped lists with sorting

2. **Date Range Indexes**
   - Pattern: `(firm, date_field)`
   - Supports: Time-based queries (invoices, time entries)

3. **Status Filter Indexes**
   - Pattern: `(firm, status, -created_at)`
   - Supports: Filtered lists (active clients, pending invoices)

4. **Foreign Key Indexes**
   - Django creates these automatically
   - Review for composite opportunities

---

## Recommended Indexes by Module

### Finance Module

**Invoice:**
```python
indexes = [
    # Existing
    models.Index(fields=['firm', 'status']),

    # Add for performance
    models.Index(fields=['firm', 'client', '-issue_date']),
    models.Index(fields=['firm', '-due_date']),
    models.Index(fields=['engagement', '-issue_date']),
    models.Index(fields=['client', 'status', '-issue_date']),
]
```

**PaymentFailure:**
```python
indexes = [
    models.Index(fields=['firm', 'resolved', '-failed_at']),  # Existing
    models.Index(fields=['client', 'resolved', '-failed_at']),  # Add
]
```

**CreditLedgerEntry:**
```python
indexes = [
    models.Index(fields=['firm', 'client', '-created_at']),
    models.Index(fields=['firm', 'credit_type', '-created_at']),
]
```

### Projects Module

**Project:**
```python
indexes = [
    # Already good coverage
    models.Index(fields=['firm', 'status']),
    models.Index(fields=['firm', 'client', 'status']),
]
```

**TimeEntry:**
```python
indexes = [
    models.Index(fields=['project', 'user', 'date']),  # Existing

    # Add for billing queries
    models.Index(fields=['project', 'approved', 'invoiced']),
    models.Index(fields=['user', 'date', 'approved']),
]
```

### CRM Module

**Lead:**
```python
indexes = [
    models.Index(fields=['firm', 'status', '-created_at']),
    models.Index(fields=['firm', 'assigned_to', 'status']),
]
```

**Proposal:**
```python
indexes = [
    models.Index(fields=['firm', 'status', '-sent_date']),
    models.Index(fields=['firm', 'prospect', '-created_at']),
]
```

### Clients Module

**Client:**
```python
indexes = [
    models.Index(fields=['firm', 'status']),

    # Add for portal queries
    models.Index(fields=['firm', 'organization', 'status']),
]
```

**ClientEngagement:**
```python
indexes = [
    models.Index(fields=['firm', 'status']),  # Existing
    models.Index(fields=['firm', '-start_date']),  # Existing

    # Add for billing
    models.Index(fields=['client', 'status', '-start_date']),
]
```

### Documents Module

**Document:**
```python
indexes = [
    models.Index(fields=['firm', 'folder', '-uploaded_at']),
    models.Index(fields=['firm', 'uploaded_by', '-uploaded_at']),
]
```

---

## Implementation Plan

### Phase 1: Critical Indexes (Immediate)
- Finance: Invoice date queries
- Projects: TimeEntry billing queries
- CRM: Lead/Proposal status filters

### Phase 2: Optimization Indexes (Week 2)
- Documents: Folder navigation
- Clients: Organization filtering
- Audit: Event category queries

### Phase 3: Monitoring & Tuning (Ongoing)
- Use Django Debug Toolbar in dev
- Monitor slow query logs in production
- Add indexes based on real usage patterns

---

## Index Size Considerations

**Estimated Index Overhead:**
- Each composite index: ~50-100 MB per 10K rows
- Total additional storage: ~500 MB for 100K total records
- Trade-off: Storage cost vs. query performance (worth it)

**When NOT to add indexes:**
- Tables with < 1000 rows
- Fields rarely queried
- Write-heavy tables (indexes slow INSERTs)

---

## Performance Gains (Estimated)

| Query Type | Before | After | Improvement |
|------------|--------|-------|-------------|
| Firm-scoped invoice list | 200ms | 15ms | **13x faster** |
| Client engagement history | 150ms | 10ms | **15x faster** |
| TimeEntry billing queries | 300ms | 20ms | **15x faster** |
| Lead status filtering | 180ms | 12ms | **15x faster** |

---

## Migration Strategy

1. Create migration with all new indexes
2. Test in development with representative data
3. Deploy to staging with production data snapshot
4. Monitor query performance before/after
5. Deploy to production during low-traffic window

---

## Monitoring Queries

```python
# Django shell commands to identify slow queries

from django.db import connection
from django.db import reset_queries

# Enable query logging
settings.DEBUG = True

# Run your queries
Invoice.objects.filter(firm=firm, status='sent').order_by('-issue_date')[:20]

# Check query count and time
print(len(connection.queries))
print(connection.queries[-1]['time'])
```

---

## Validation

After adding indexes:

```bash
# Check index usage (PostgreSQL)
EXPLAIN ANALYZE SELECT * FROM finance_invoice
WHERE firm_id = 1 AND status = 'sent'
ORDER BY issue_date DESC
LIMIT 20;

# Should show "Index Scan" not "Seq Scan"
```

---

## Next Steps

1. ✅ Document recommendations (this file)
2. ⏳ Create migration with new indexes
3. ⏳ Test with sample data
4. ⏳ Benchmark before/after performance
5. ⏳ Deploy to production
