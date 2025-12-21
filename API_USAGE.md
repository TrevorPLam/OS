# ConsultantPro API Usage Guide

Complete guide to using the ConsultantPro REST API.

---

## Table of Contents

1. [Authentication](#authentication)
2. [API Overview](#api-overview)
3. [CRM Module](#crm-module)
4. [Projects Module](#projects-module)
5. [Finance Module](#finance-module)
6. [Documents Module](#documents-module)
7. [Assets Module](#assets-module)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)

---

## Authentication

### Obtain JWT Token

```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Use Access Token

Include the access token in all API requests:

```http
GET /api/crm/clients/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Refresh Token

When your access token expires (default: 1 hour):

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "new_access_token_here"
}
```

---

## API Overview

### Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

### Available Endpoints

| Module | Endpoint Base | Description |
|--------|--------------|-------------|
| CRM | `/api/crm/` | Clients, Proposals, Contracts |
| Projects | `/api/projects/` | Projects, Tasks, Time Entries |
| Finance | `/api/finance/` | Invoices, Bills, Ledger Entries |
| Documents | `/api/documents/` | Folders, Documents, Versions |
| Assets | `/api/assets/` | Assets, Maintenance Logs |

### API Documentation

Interactive API documentation available at:
- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/

---

## CRM Module

### Clients

#### List All Clients

```http
GET /api/crm/clients/
Authorization: Bearer {token}
```

**Query Parameters:**
- `status` - Filter by status (active, inactive, lead, archived)
- `industry` - Filter by industry
- `search` - Search company name, contact name, email
- `ordering` - Sort by field (e.g., `-created_at`, `company_name`)
- `page` - Page number for pagination

**Example:**
```http
GET /api/crm/clients/?status=active&search=tech&ordering=-created_at
```

**Response:**
```json
{
  "count": 42,
  "next": "http://localhost:8000/api/crm/clients/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "company_name": "Tech Innovations Inc",
      "primary_contact_name": "John Smith",
      "primary_contact_email": "john@techinnovations.com",
      "primary_contact_phone": "+1-555-0100",
      "website": "https://techinnovations.com",
      "industry": "Technology",
      "status": "active",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

#### Create Client

```http
POST /api/crm/clients/
Authorization: Bearer {token}
Content-Type: application/json

{
  "company_name": "Acme Corporation",
  "primary_contact_name": "Jane Doe",
  "primary_contact_email": "jane@acme.com",
  "primary_contact_phone": "+1-555-0200",
  "website": "https://acme.com",
  "address": "123 Main St",
  "city": "San Francisco",
  "state": "CA",
  "postal_code": "94105",
  "country": "USA",
  "industry": "Manufacturing",
  "status": "lead",
  "lead_source": "referral",
  "notes": "Interested in Q2 engagement"
}
```

#### Update Client

```http
PATCH /api/crm/clients/1/
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "active",
  "notes": "Signed contract on 2025-01-20"
}
```

#### Get Client Detail

```http
GET /api/crm/clients/1/
Authorization: Bearer {token}
```

### Proposals

#### Create Proposal

```http
POST /api/crm/proposals/
Authorization: Bearer {token}
Content-Type: application/json

{
  "client": 1,
  "title": "Digital Transformation Strategy",
  "description": "6-month engagement for digital transformation assessment and implementation roadmap",
  "estimated_value": "75000.00",
  "currency": "USD",
  "valid_until": "2025-03-31",
  "status": "draft"
}
```

**Response:**
```json
{
  "id": 1,
  "proposal_number": "PROP-2025-001",
  "client": 1,
  "client_name": "Acme Corporation",
  "title": "Digital Transformation Strategy",
  "estimated_value": "75000.00",
  "status": "draft",
  "is_expired": false,
  "created_at": "2025-01-20T14:00:00Z"
}
```

#### Send Proposal to Client

```http
PATCH /api/crm/proposals/1/
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "sent"
}
```

*Note: Changing status to "sent" automatically sets `sent_at` timestamp via Django signals.*

### Contracts

#### Create Contract from Proposal

```http
POST /api/crm/contracts/
Authorization: Bearer {token}
Content-Type: application/json

{
  "client": 1,
  "proposal": 1,
  "title": "Digital Transformation Engagement",
  "contract_value": "75000.00",
  "payment_terms": "Net 30, 50% upfront",
  "start_date": "2025-02-01",
  "end_date": "2025-07-31",
  "status": "draft"
}
```

**Response:**
```json
{
  "id": 1,
  "contract_number": "CTR-2025-001",
  "client": 1,
  "client_name": "Acme Corporation",
  "proposal": 1,
  "proposal_number": "PROP-2025-001",
  "title": "Digital Transformation Engagement",
  "contract_value": "75000.00",
  "status": "draft",
  "is_active": false
}
```

---

## Projects Module

### Projects

#### Create Project

```http
POST /api/projects/projects/
Authorization: Bearer {token}
Content-Type: application/json

{
  "client": 1,
  "contract": 1,
  "project_manager": 2,
  "project_code": "DT-2025-01",
  "name": "Digital Transformation Phase 1",
  "description": "Initial assessment and roadmap development",
  "status": "planning",
  "billing_type": "hourly",
  "hourly_rate": "200.00",
  "start_date": "2025-02-01",
  "end_date": "2025-04-30"
}
```

#### List Projects with Filters

```http
GET /api/projects/projects/?status=in_progress&client=1
Authorization: Bearer {token}
```

### Tasks

#### Create Task

```http
POST /api/projects/tasks/
Authorization: Bearer {token}
Content-Type: application/json

{
  "project": 1,
  "assigned_to": 3,
  "title": "Stakeholder Interviews",
  "description": "Conduct interviews with key stakeholders to understand current state",
  "status": "todo",
  "priority": "high",
  "estimated_hours": "16.0",
  "due_date": "2025-02-15"
}
```

#### Update Task Status

```http
PATCH /api/projects/tasks/1/
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "done"
}
```

*Note: Changing status to "done" automatically sets `completed_at` timestamp via Django signals.*

### Time Entries

#### Log Time

```http
POST /api/projects/time-entries/
Authorization: Bearer {token}
Content-Type: application/json

{
  "project": 1,
  "task": 1,
  "date": "2025-02-10",
  "hours": "8.0",
  "description": "Completed stakeholder interviews with C-suite executives",
  "is_billable": true
}
```

**Response:**
```json
{
  "id": 1,
  "project": 1,
  "task": 1,
  "user": 2,
  "user_name": "johndoe",
  "date": "2025-02-10",
  "hours": "8.00",
  "description": "Completed stakeholder interviews with C-suite executives",
  "is_billable": true,
  "hourly_rate": "200.00",
  "billed_amount": "1600.00",
  "invoiced": false
}
```

#### Query Time Entries

```http
GET /api/projects/time-entries/?project=1&date_after=2025-02-01&date_before=2025-02-28
Authorization: Bearer {token}
```

---

## Finance Module

### Invoices

#### Create Invoice

```http
POST /api/finance/invoices/
Authorization: Bearer {token}
Content-Type: application/json

{
  "client": 1,
  "project": 1,
  "subtotal": "10000.00",
  "tax_amount": "1000.00",
  "total_amount": "11000.00",
  "issue_date": "2025-02-28",
  "due_date": "2025-03-30",
  "payment_terms": "Net 30",
  "line_items": [
    {
      "description": "Consulting Services - February 2025",
      "quantity": 50,
      "rate": 200,
      "amount": 10000
    }
  ],
  "notes": "Thank you for your business!"
}
```

**Response:**
```json
{
  "id": 1,
  "invoice_number": "INV-2025-001",
  "client": 1,
  "client_name": "Acme Corporation",
  "status": "draft",
  "total_amount": "11000.00",
  "amount_paid": "0.00",
  "balance_due": "11000.00",
  "is_overdue": false,
  "issue_date": "2025-02-28",
  "due_date": "2025-03-30"
}
```

#### Send Invoice to Client

```http
PATCH /api/finance/invoices/1/
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "sent"
}
```

#### Record Payment

```http
PATCH /api/finance/invoices/1/
Authorization: Bearer {token}
Content-Type: application/json

{
  "amount_paid": "11000.00",
  "status": "paid",
  "paid_date": "2025-03-15"
}
```

#### Process Payment via Stripe

```http
POST /api/finance/invoices/1/create-payment-intent/
Authorization: Bearer {token}
Content-Type: application/json

{
  "amount": 11000.00,
  "currency": "usd"
}
```

**Response:**
```json
{
  "client_secret": "pi_3abc123_secret_xyz",
  "payment_intent_id": "pi_3abc123def456"
}
```

*Use the `client_secret` with Stripe.js on the frontend to complete payment.*

### Bills (Accounts Payable)

#### Create Bill

```http
POST /api/finance/bills/
Authorization: Bearer {token}
Content-Type: application/json

{
  "vendor_name": "AWS",
  "vendor_email": "billing@aws.amazon.com",
  "bill_number": "AWS-202502",
  "reference_number": "BILL-2025-001",
  "subtotal": "450.00",
  "tax_amount": "0.00",
  "total_amount": "450.00",
  "bill_date": "2025-02-28",
  "due_date": "2025-03-15",
  "expense_category": "Software",
  "description": "S3 storage and bandwidth - February 2025"
}
```

---

## Documents Module

### Folders

#### Create Folder

```http
POST /api/documents/folders/
Authorization: Bearer {token}
Content-Type: application/json

{
  "client": 1,
  "name": "Contracts",
  "description": "Signed contracts and legal documents",
  "visibility": "internal"
}
```

#### Create Nested Folder

```http
POST /api/documents/folders/
Authorization: Bearer {token}
Content-Type: application/json

{
  "client": 1,
  "parent": 1,
  "name": "2025",
  "visibility": "internal"
}
```

### Documents

#### Upload Document

```http
POST /api/documents/documents/upload/
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: (binary file data)
folder: 1
client: 1
name: Signed_Contract_Acme.pdf
description: Executed contract dated 2025-01-20
visibility: internal
```

**Response:**
```json
{
  "id": 1,
  "folder": 1,
  "folder_name": "Contracts",
  "client": 1,
  "client_name": "Acme Corporation",
  "name": "Signed_Contract_Acme.pdf",
  "file_type": "application/pdf",
  "file_size_bytes": 524288,
  "s3_key": "client-1/documents/abc123.pdf",
  "s3_bucket": "consultantpro-docs",
  "current_version": 1,
  "visibility": "internal",
  "created_at": "2025-01-20T16:45:00Z"
}
```

#### Download Document

```http
GET /api/documents/documents/1/download/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "download_url": "https://consultantpro-docs.s3.amazonaws.com/client-1/documents/abc123.pdf?X-Amz-Algorithm=..."
}
```

*The `download_url` is a presigned S3 URL valid for 1 hour.*

#### List Documents by Client

```http
GET /api/documents/documents/?client=1&folder=1
Authorization: Bearer {token}
```

---

## Assets Module

### Assets

#### Create Asset

```http
POST /api/assets/assets/
Authorization: Bearer {token}
Content-Type: application/json

{
  "asset_tag": "LAPTOP-001",
  "name": "MacBook Pro 16\" M3 Max",
  "description": "Development machine for senior consultant",
  "category": "computer",
  "status": "active",
  "assigned_to": 3,
  "purchase_price": "3499.00",
  "purchase_date": "2025-01-15",
  "vendor": "Apple Inc",
  "manufacturer": "Apple",
  "model_number": "MRW13LL/A",
  "serial_number": "C02XY123456",
  "useful_life_years": 3,
  "warranty_expiration": "2028-01-15",
  "location": "San Francisco Office"
}
```

#### Update Asset Assignment

```http
PATCH /api/assets/assets/1/
Authorization: Bearer {token}
Content-Type: application/json

{
  "assigned_to": 4,
  "location": "New York Office"
}
```

### Maintenance Logs

#### Schedule Maintenance

```http
POST /api/assets/maintenance-logs/
Authorization: Bearer {token}
Content-Type: application/json

{
  "asset": 1,
  "maintenance_type": "preventive",
  "status": "scheduled",
  "description": "Annual hardware checkup and software updates",
  "scheduled_date": "2025-06-15",
  "performed_by": "IT Support Team",
  "vendor": "Internal",
  "cost": "0.00"
}
```

#### Complete Maintenance

```http
PATCH /api/assets/maintenance-logs/1/
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "completed",
  "completed_date": "2025-06-15",
  "cost": "0.00"
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Validation failed",
    "details": {
      "email": ["Invalid email format"],
      "due_date": ["End date must be after start date"]
    },
    "code": "VALIDATION_ERROR"
  }
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Validation error or malformed request |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Authenticated but not authorized for this resource |
| 404 | Not Found | Resource does not exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Unexpected server error |

---

## Rate Limiting

API endpoints are protected by rate limiting:

| Endpoint Type | Limit |
|--------------|-------|
| Standard API | 100 requests/minute (burst), 1000 requests/hour (sustained) |
| Payment endpoints | 10 requests/minute |
| File uploads | 30 requests/hour |
| Anonymous users | 20 requests/hour |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1738425600
```

### Rate Limit Exceeded

```json
{
  "error": {
    "type": "Throttled",
    "message": "Request was throttled. Expected available in 45 seconds.",
    "code": "TOO_MANY_REQUESTS"
  }
}
```

---

## Pagination

All list endpoints support pagination:

```http
GET /api/crm/clients/?page=2&page_size=50
```

**Response:**
```json
{
  "count": 250,
  "next": "http://localhost:8000/api/crm/clients/?page=3&page_size=50",
  "previous": "http://localhost:8000/api/crm/clients/?page=1&page_size=50",
  "results": [...]
}
```

Default page size: 100
Max page size: 1000

---

## Filtering and Searching

### Django Filter Backend

```http
GET /api/crm/clients/?status=active&industry=Technology
GET /api/projects/tasks/?status=in_progress&priority=high
GET /api/finance/invoices/?status=overdue&client=1
```

### Search

```http
GET /api/crm/clients/?search=acme
GET /api/projects/projects/?search=digital+transformation
```

### Ordering

```http
GET /api/crm/clients/?ordering=company_name
GET /api/finance/invoices/?ordering=-created_at
GET /api/projects/tasks/?ordering=due_date,-priority
```

Prefix with `-` for descending order.

---

## Best Practices

1. **Always use HTTPS in production**
2. **Store JWT tokens securely** (e.g., httpOnly cookies, secure storage)
3. **Refresh tokens before expiration** to avoid interrupting user sessions
4. **Handle errors gracefully** with proper user feedback
5. **Respect rate limits** by implementing exponential backoff
6. **Use pagination** for large datasets
7. **Filter server-side** rather than fetching all data
8. **Validate data on both client and server**
9. **Use presigned URLs** for direct S3 uploads/downloads when possible
10. **Monitor Stripe webhooks** for payment confirmations

---

## Need Help?

- **API Documentation:** http://localhost:8000/api/docs/
- **GitHub Issues:** https://github.com/your-org/consultantpro/issues
- **Email Support:** support@consultantpro.com
