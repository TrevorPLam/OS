# Intake Form System with Qualification Logic

**Feature:** 3.4 - Complex Task  
**Module:** CRM (Pre-Sale)  
**Status:** ✅ Completed  
**Created:** January 1, 2026

---

## Overview

The Intake Form System provides customizable web forms for lead qualification. Forms can be embedded on websites or sent as links to collect prospect information and automatically score/qualify leads based on predefined rules.

**Key Features:**
- Dynamic form builder with multiple field types
- Automatic lead qualification scoring
- Auto-create Lead records from submissions
- Configurable qualification thresholds
- Email notifications on submission
- Admin review workflow

---

## Architecture

### Models

#### IntakeForm
Customizable form definition with qualification settings.

**Key Fields:**
- `name`, `title`, `description`: Form identification
- `status`: draft, active, inactive, archived
- `qualification_enabled`: Enable automatic scoring
- `qualification_threshold`: Minimum score (0-100) to qualify
- `auto_create_lead`: Automatically create Lead from submission
- `default_owner`: Default owner for created leads
- `submission_count`, `qualified_count`: Statistics

#### IntakeFormField
Individual field definition with scoring rules.

**Field Types:**
- text, textarea, email, phone, url, number
- select, multiselect, checkbox, date, file

**Key Fields:**
- `label`, `field_type`, `placeholder`, `help_text`
- `required`, `order`: Field configuration
- `options`: Options for select fields (JSON array)
- `scoring_enabled`: Enable qualification scoring
- `scoring_rules`: Scoring logic (JSON object)

**Scoring Rules Format:**
```json
{
  "value1": 10,
  "value2": 20,
  "ranges": [
    {"min": 0, "max": 100, "points": 5},
    {"min": 101, "max": 1000, "points": 10}
  ]
}
```

#### IntakeFormSubmission
Submission with responses and qualification score.

**Key Fields:**
- `responses`: Field responses (JSON: {field_id: value})
- `qualification_score`: Calculated score (0-100)
- `is_qualified`: Meets threshold?
- `status`: pending, qualified, disqualified, converted, spam
- `submitter_email`, `submitter_name`, `submitter_phone`, `submitter_company`
- `lead`, `prospect`: Created records (if applicable)
- `ip_address`, `user_agent`, `referrer`: Metadata

**Methods:**
- `calculate_qualification_score()`: Calculate score from responses
- `create_lead()`: Create Lead record from submission

---

## API Endpoints

### Base URLs
- Forms: `/api/crm/intake-forms/`
- Fields: `/api/crm/intake-form-fields/`
- Submissions: `/api/crm/intake-form-submissions/`

### Intake Forms

**List Forms:**
```http
GET /api/crm/intake-forms/
?status=active&search=consulting
```

**Create Form:**
```http
POST /api/crm/intake-forms/
{
  "name": "Consulting Inquiry",
  "title": "Tell us about your needs",
  "status": "active",
  "qualification_enabled": true,
  "qualification_threshold": 50,
  "auto_create_lead": true
}
```

### Intake Form Submissions

**Submit Form:**
```http
POST /api/crm/intake-form-submissions/
{
  "form": 1,
  "responses": {
    "1": "john@example.com",
    "2": "John Doe",
    "3": "Acme Corp"
  },
  "submitter_email": "john@example.com",
  "submitter_name": "John Doe",
  "submitter_company": "Acme Corp"
}
```

**Calculate Score:**
```http
POST /api/crm/intake-form-submissions/{id}/calculate_score/
```

**Create Lead:**
```http
POST /api/crm/intake-form-submissions/{id}/create_lead/
```

---

## Admin Interface

### IntakeFormAdmin
- List display: name, status, submission/qualified counts
- Inline field editing
- Filter by status, qualification enabled
- Actions: none (CRUD via form)

### IntakeFormSubmissionAdmin
- List display: form, email, company, score, status
- Filter by form, status, is_qualified
- Actions:
  - Calculate qualification scores
  - Create leads from submissions
  - Mark as spam

---

## Usage Examples

### Create Form with Fields

```python
from modules.crm.models import IntakeForm, IntakeFormField

# Create form
form = IntakeForm.objects.create(
    firm=firm,
    name="Consulting Inquiry",
    title="Tell us about your project",
    qualification_enabled=True,
    qualification_threshold=60,
    auto_create_lead=True
)

# Add fields
IntakeFormField.objects.create(
    form=form,
    label="Email",
    field_type="email",
    required=True,
    order=1
)

IntakeFormField.objects.create(
    form=form,
    label="Company Size",
    field_type="select",
    options=["1-10", "11-50", "51-200", "201+"],
    required=True,
    scoring_enabled=True,
    scoring_rules={
        "1-10": 5,
        "11-50": 10,
        "51-200": 15,
        "201+": 20
    },
    order=2
)
```

### Process Submission

```python
from modules.crm.models import IntakeFormSubmission

# Create submission
submission = IntakeFormSubmission.objects.create(
    form=form,
    responses={
        "1": "john@example.com",
        "2": "51-200"
    },
    submitter_email="john@example.com",
    submitter_name="John Doe",
    submitter_company="Acme Corp"
)

# Calculate score
score = submission.calculate_qualification_score()
# Returns: 75 (normalized score)
# is_qualified = True (>= threshold of 60)

# Auto-create lead if qualified
if submission.is_qualified and form.auto_create_lead:
    lead = submission.create_lead()
```

---

## Security & Permissions

- **Tenant Isolation:** Forms scoped to Firm via FirmScopedMixin
- **Access Control:** DenyPortalAccess - staff only
- **Data Validation:** JSON responses validated in serializer
- **Spam Prevention:** IP tracking, manual review, spam status

---

## Integration Points

- **Lead Management:** Auto-create Lead records
- **Email Notifications:** Notify on submission
- **CRM Workflow:** Feed into sales pipeline
- **Analytics:** Track conversion rates

---

## Migration

**File:** `0005_intake_forms.py`

**Models Created:**
- IntakeForm
- IntakeFormField  
- IntakeFormSubmission

---

## References

- **Related Features:** Lead Management, Qualification Logic
- **API Docs:** `/api/docs/` (Swagger)
- **Admin:** `/admin/crm/intakeform/`
