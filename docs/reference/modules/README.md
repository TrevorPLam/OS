# Module Reference

Module-by-module reference documentation.

## Module Overview

This section provides detailed reference documentation for each UBOS module.

## Module Documentation

Each module documentation includes:
- **Purpose** - What the module does
- **Models** - Database models
- **API Endpoints** - Available endpoints
- **Business Logic** - Key business rules
- **Configuration** - Configuration options
- **Integration Points** - How it integrates with other modules

## Modules

### Core Infrastructure
- [core](core.md) - Shared infrastructure
- [firm](firm.md) - Multi-tenant foundation
- [auth](auth.md) - Authentication and authorization

### Business Modules
- [clients](clients.md) - Client management
- [crm](crm.md) - CRM functionality
- [projects](projects.md) - Project management
- [finance](finance.md) - Financial operations
- [documents](documents.md) - Document management
- [communications](communications.md) - Communications
- [calendar](calendar.md) - Calendar and scheduling
- [automation](automation.md) - Automation workflows
- And more...

## Module Structure

Each module follows a consistent structure:
- `models.py` - Database models
- `views.py` - API endpoints
- `serializers.py` - API serialization
- `urls.py` - URL routing
- `admin.py` - Admin configuration

## Related Documentation

- [Architecture - Modules](../architecture/modules/README.md) - Module overview
- [API Reference](../api/README.md) - API documentation
- [Development Guide](../../development/README.md) - Development practices
