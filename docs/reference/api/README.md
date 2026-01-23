# API Reference

Complete API documentation for UBOS.

## API Overview

UBOS provides a RESTful API built with Django REST Framework.

### Base URL
- **Development:** `http://localhost:8000/api/`
- **Production:** `https://api.ubos.example.com/api/`

### Authentication
- JWT tokens
- OAuth 2.0
- API keys (for integrations)

## API Documentation

### Interactive Documentation
- **Swagger UI:** `/api/docs/`
- **ReDoc:** `/api/redoc/`
- **OpenAPI Spec:** `/api/schema/`

### API Endpoints by Module

#### Authentication
- `/api/auth/login/` - User login
- `/api/auth/logout/` - User logout
- `/api/auth/register/` - User registration
- `/api/auth/mfa/` - Multi-factor authentication

#### Clients
- `/api/clients/` - Client management
- `/api/clients/{id}/` - Client details

#### Projects
- `/api/projects/` - Project management
- `/api/projects/{id}/` - Project details

#### Finance
- `/api/finance/invoices/` - Invoice management
- `/api/finance/payments/` - Payment processing

#### Documents
- `/api/documents/` - Document management
- `/api/documents/{id}/` - Document operations

### API Versioning
- Current version: v1
- Version policy: See `docs/API_VERSIONING_POLICY.md` (if exists)

## API Standards

- RESTful design
- JSON request/response
- Standard HTTP status codes
- Pagination for list endpoints
- Filtering and sorting support

## Related Documentation

- [API Guide](../guides/api/README.md) - API usage guide
- [Integrations](../integrations/README.md) - Integration examples
- [Development](../development/README.md) - Development practices
