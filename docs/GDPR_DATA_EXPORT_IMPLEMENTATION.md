# GDPR Data Export Implementation (ASSESS-L19.3)

**Status:** Implemented  
**Last Updated:** December 2025

## Overview

This document describes the implementation of GDPR Right to Access (Article 15) and Right to Data Portability (Article 20) compliance features.

## Features

### Data Export Command

Management command to export all user/client data in JSON and CSV formats.

**Usage:**
```bash
python manage.py export_user_data --client-id 123 --format both --output-dir ./exports
python manage.py export_user_data --email user@example.com --format json
```

**Options:**
- `--client-id`: Client ID to export data for
- `--email`: Email address (alternative to client-id)
- `--format`: Export format (`json`, `csv`, or `both`)
- `--output-dir`: Output directory (default: `./exports`)

### Exported Data

The export includes all data associated with a client:

1. **Client Information**
   - Company details
   - Contact information
   - Consent tracking (marketing_opt_in, consent_timestamp, consent_source)
   - Terms of Service acceptance
   - Financial data (lifetime value, retainer balance)

2. **Projects**
   - Project details
   - Status and timeline
   - Budget information

3. **Invoices**
   - Invoice numbers and amounts
   - Payment status
   - Dates (issue, due, paid)

4. **Payments**
   - Payment amounts and methods
   - Payment dates

5. **Documents**
   - Document titles and status
   - Creation/update timestamps

6. **Time Entries**
   - Hours logged
   - Billable status
   - Dates

7. **Tasks**
   - Task titles and status
   - Completion dates

8. **Leads/Prospects**
   - Lead/prospect information
   - Contact details
   - Status and source

## Export Formats

### JSON Format

Structured JSON with nested objects:
```json
{
  "client": {
    "id": 123,
    "company_name": "Acme Corp",
    "primary_contact_email": "contact@acme.com",
    "marketing_opt_in": true,
    "consent_timestamp": "2025-01-15T10:00:00Z",
    ...
  },
  "projects": [...],
  "invoices": [...],
  ...
}
```

### CSV Format

Flattened CSV with section/field/value structure:
```csv
Section,Field,Value
Client,company_name,Acme Corp
Client,primary_contact_email,contact@acme.com
Project,Project Alpha.name,Project Alpha
Invoice,INV-001.total_amount,1000.00
```

## Security & Privacy

### Access Control

- Only authorized staff can run export command
- Exports are scoped to firm (tenant isolation)
- Exports include only data belonging to the specified client

### Data Handling

- Exports stored in secure directory
- Files should be encrypted in transit
- Files should be deleted after delivery to user
- Audit logs track all export operations

## Integration with Erasure Workflow

The export functionality integrates with the erasure workflow (`modules.core.erasure`):

1. **Before Erasure:** Export can be run to provide user with their data
2. **After Erasure:** Export will show anonymized data (if anonymization was chosen)

## Future Enhancements

- Automated export scheduling
- Email delivery of exports
- Encrypted export files
- Export history tracking
- API endpoint for programmatic exports

## See Also

- [Data Retention Implementation](./DATA_RETENTION_IMPLEMENTATION.md) - Automated data retention policies
- [Erasure Implementation](./ERASURE_ANONYMIZATION_IMPLEMENTATION.md) - Data anonymization and deletion
- [Hidden Assumptions](./HIDDEN_ASSUMPTIONS.md) - GDPR compliance assumptions

## References

- **ASSESS-L19.3:** Right-to-delete/export implementation
- **GDPR Article 15:** Right of access
- **GDPR Article 20:** Right to data portability