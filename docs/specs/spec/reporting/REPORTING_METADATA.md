# Reporting Metadata and Disclaimer Rules

## Required metadata fields
Every report must include the following metadata:
- `source_modules`: list of modules used to generate the report
- `generated_at`: timestamp when the report was generated
- `freshness_window`: time window describing data recency
- `join_keys_used`: identifiers used to join cross-module data
- `coverage_notes`: notes about inclusion/exclusion coverage
- `non_authoritative`: **true** (reports are derived and non-authoritative)
- `provenance_pointers`: references to the source records read

## Disclaimer (must appear on cross-module reports)
```
This report is derived from multiple modules and is provided for informational purposes only.
It is non-authoritative and does not supersede the underlying source records.
Refer to the source systems for official values.
```
