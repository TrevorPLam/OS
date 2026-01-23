# API Guide

Guide for using the UBOS API.

## Getting Started

1. **Get API Access** - Obtain API credentials
2. **Read API Reference** - See [API Reference](../../reference/api/README.md)
3. **Authenticate** - Set up authentication
4. **Make Requests** - Start using the API

## Authentication

### JWT Tokens
```bash
# Login to get token
curl -X POST https://api.ubos.example.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token in requests
curl -H "Authorization: Bearer <token>" \
  https://api.ubos.example.com/api/clients/
```

### OAuth 2.0
- Standard OAuth 2.0 flow
- Client credentials grant
- Authorization code flow

## Common Operations

### Creating Resources
```bash
POST /api/clients/
Content-Type: application/json

{
  "name": "Client Name",
  "email": "client@example.com"
}
```

### Listing Resources
```bash
GET /api/clients/?page=1&page_size=20
```

### Updating Resources
```bash
PATCH /api/clients/{id}/
Content-Type: application/json

{
  "name": "Updated Name"
}
```

## Best Practices

1. **Use Pagination** - Always paginate list endpoints
2. **Handle Errors** - Check status codes
3. **Rate Limiting** - Respect rate limits
4. **Versioning** - Use API versioning
5. **Security** - Keep credentials secure

## Related Documentation

- [API Reference](../../reference/api/README.md) - Complete API docs
- [Integrations](../../integrations/README.md) - Integration examples
- [Security](../../security/README.md) - Security best practices
