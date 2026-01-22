# CPQ (Configure-Price-Quote) Engine

**Feature:** 3.5 - Complex Task  
**Module:** CRM (Pre-Sale)  
**Status:** ✅ Completed  
**Created:** January 1, 2026

---

## Overview

The CPQ (Configure-Price-Quote) Engine provides a comprehensive system for managing product catalogs, configurable options, and automated quote generation. It enables sales teams to configure complex products, calculate accurate pricing, and generate professional quotes quickly.

**Key Features:**
- Product catalog with multiple product types (services, products, subscriptions, bundles)
- Configurable product options with pricing impacts
- Dependency rules for complex configurations
- Automatic price calculation with modifiers and multipliers
- Discount management
- Quote generation from configurations
- Validation and error tracking

---

## Architecture

### Models

#### Product
Represents a product or service that can be sold and configured.

**Key Fields:**
- `code`: Unique product code/SKU
- `name`, `description`: Product identification
- `product_type`: Type of product (service, product, subscription, bundle)
- `status`: Product status (active, inactive, archived)
- `base_price`, `currency`: Base pricing
- `is_configurable`: Whether product has configurable options
- `configuration_schema`: JSON schema defining configuration rules
- `category`, `tags`: Product organization and filtering
- `firm`: Firm this product belongs to (TIER 0)

**Product Types:**
- **Service**: Professional services or consulting
- **Product**: Physical or digital products
- **Subscription**: Recurring subscription services
- **Bundle**: Bundle of multiple products/services

#### ProductOption
Represents a configurable option for a product (e.g., size, color, features, service level).

**Key Fields:**
- `product`: Parent product
- `code`, `label`, `description`: Option identification
- `option_type`: Type of option (single_select, multi_select, text, number, boolean)
- `required`: Whether this option is mandatory
- `display_order`: Display order in UI
- `values`: Available values for select options (JSON array)
- `price_modifier`: Fixed amount to add to base price
- `price_multiplier`: Multiplier to apply to base price
- `dependency_rules`: Rules defining when this option is available

**Option Types:**
- **single_select**: Choose one value from list
- **multi_select**: Choose multiple values from list
- **text**: Free-form text input
- **number**: Numeric input
- **boolean**: Yes/No checkbox

**Values Format (for select options):**
```json
[
  {
    "value": "small",
    "label": "Small (1-10 users)",
    "price_modifier": 0
  },
  {
    "value": "medium",
    "label": "Medium (11-50 users)",
    "price_modifier": 500
  },
  {
    "value": "large",
    "label": "Large (51+ users)",
    "price_modifier": 2000
  }
]
```

**Dependency Rules Format:**
```json
{
  "requires": [
    {
      "option": "support_level",
      "value": "premium"
    }
  ]
}
```

#### ProductConfiguration
Represents a specific configuration of a product with selected options and calculated pricing.

**Key Fields:**
- `product`: Product being configured
- `configuration_name`: Optional name for this configuration
- `selected_options`: Selected options (JSON: {option_code: value})
- `base_price`: Base price at time of configuration
- `configuration_price`: Total calculated price
- `price_breakdown`: Detailed breakdown of pricing calculation
- `discount_percentage`, `discount_amount`: Discount information
- `status`: Configuration status (draft, validated, quoted)
- `validation_errors`: List of validation errors
- `quote`: Quote created from this configuration (if applicable)

**Methods:**
- `calculate_price()`: Calculate total price based on options
- `validate_configuration()`: Validate against product rules
- `_evaluate_dependencies()`: Check dependency rules

**Price Calculation Logic:**
1. Start with base price
2. Add fixed price modifiers from options
3. Apply price multipliers from options
4. Add value-specific pricing (from select option values)
5. Calculate subtotal
6. Apply discount percentage
7. Calculate final total

---

## API Endpoints

### Base URLs
- Products: `/api/crm/products/`
- Options: `/api/crm/product-options/`
- Configurations: `/api/crm/product-configurations/`

### Products

**List Products:**
```http
GET /api/crm/products/
?product_type=service&status=active&is_configurable=true
```

**Create Product:**
```http
POST /api/crm/products/
Content-Type: application/json

{
  "code": "CONSULTING-001",
  "name": "Enterprise Consulting Package",
  "description": "Comprehensive consulting services",
  "product_type": "service",
  "status": "active",
  "base_price": "10000.00",
  "currency": "USD",
  "is_configurable": true,
  "category": "Consulting",
  "tags": ["enterprise", "consulting"]
}
```

**Get Product:**
```http
GET /api/crm/products/{id}/
```

**Update Product:**
```http
PUT /api/crm/products/{id}/
PATCH /api/crm/products/{id}/
```

**Get Product Options:**
```http
GET /api/crm/products/{id}/options/
```

**Get Product Configurations:**
```http
GET /api/crm/products/{id}/configurations/
```

### Product Options

**List Options:**
```http
GET /api/crm/product-options/
?product={product_id}&required=true
```

**Create Option:**
```http
POST /api/crm/product-options/
Content-Type: application/json

{
  "product": 1,
  "code": "team_size",
  "label": "Team Size",
  "description": "Number of consultants assigned",
  "option_type": "single_select",
  "required": true,
  "display_order": 1,
  "values": [
    {"value": "1", "label": "1 Consultant", "price_modifier": 0},
    {"value": "2", "label": "2 Consultants", "price_modifier": 8000},
    {"value": "3+", "label": "3+ Consultants", "price_modifier": 18000}
  ]
}
```

### Product Configurations

**List Configurations:**
```http
GET /api/crm/product-configurations/
?product={product_id}&status=validated
```

**Create Configuration:**
```http
POST /api/crm/product-configurations/
Content-Type: application/json

{
  "product": 1,
  "configuration_name": "Large Enterprise Package",
  "selected_options": {
    "team_size": "3+",
    "duration": "6months",
    "support_level": "premium"
  },
  "discount_percentage": "10.00"
}
```

**Response:**
```json
{
  "id": 1,
  "product": 1,
  "product_name": "Enterprise Consulting Package",
  "product_code": "CONSULTING-001",
  "configuration_name": "Large Enterprise Package",
  "selected_options": {
    "team_size": "3+",
    "duration": "6months",
    "support_level": "premium"
  },
  "base_price": "10000.00",
  "configuration_price": "32400.00",
  "price_breakdown": {
    "base_price": 10000.00,
    "options": [
      {
        "option": "team_size",
        "label": "Team Size: 3+ Consultants",
        "type": "value_modifier",
        "amount": 18000.00
      },
      {
        "option": "duration",
        "label": "Duration",
        "type": "multiplier",
        "amount": 1.2
      }
    ],
    "subtotal": 36000.00,
    "discount_percentage": 10.00,
    "discount_amount": 3600.00,
    "total": 32400.00
  },
  "discount_percentage": "10.00",
  "discount_amount": "3600.00",
  "status": "validated",
  "validation_errors": [],
  "created_at": "2026-01-01T12:00:00Z"
}
```

**Validate Configuration:**
```http
POST /api/crm/product-configurations/{id}/validate/
```

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "status": "validated",
  "validation_errors": []
}
```

**Recalculate Price:**
```http
POST /api/crm/product-configurations/{id}/recalculate_price/
Content-Type: application/json

{
  "discount_percentage": "15.00"
}
```

**Create Quote from Configuration:**
```http
POST /api/crm/product-configurations/{id}/create_quote/
Content-Type: application/json

{
  "client_id": 123,
  "quote_number": "Q-2026-001",
  "valid_until": "2026-02-01"
}
```

**Response:**
```json
{
  "message": "Quote created successfully",
  "quote_id": 456,
  "quote_number": "Q-2026-001"
}
```

---

## Usage Examples

### Creating a Product with Options

```python
from modules.crm.models import Product, ProductOption

# Create product
product = Product.objects.create(
    firm=firm,
    code="CONSULTING-001",
    name="Enterprise Consulting Package",
    description="Comprehensive consulting services",
    product_type="service",
    status="active",
    base_price=10000.00,
    currency="USD",
    is_configurable=True,
    category="Consulting",
    created_by=user,
)

# Add team size option
team_size_option = ProductOption.objects.create(
    product=product,
    code="team_size",
    label="Team Size",
    option_type="single_select",
    required=True,
    display_order=1,
    values=[
        {"value": "1", "label": "1 Consultant", "price_modifier": 0},
        {"value": "2", "label": "2 Consultants", "price_modifier": 8000},
        {"value": "3+", "label": "3+ Consultants", "price_modifier": 18000},
    ],
)

# Add duration option (with multiplier)
duration_option = ProductOption.objects.create(
    product=product,
    code="duration",
    label="Project Duration",
    option_type="single_select",
    required=True,
    display_order=2,
    price_multiplier=1.0,
    values=[
        {"value": "3months", "label": "3 Months", "price_modifier": 0},
        {"value": "6months", "label": "6 Months (20% more)", "price_modifier": 0},
    ],
)
# For 6months, we'd set price_multiplier=1.2 on the option itself
```

### Configuring a Product

```python
from modules.crm.models import ProductConfiguration

# Create configuration
config = ProductConfiguration.objects.create(
    product=product,
    configuration_name="Large Enterprise - 6 Month",
    selected_options={
        "team_size": "3+",
        "duration": "6months",
        "support_level": "premium",
    },
    discount_percentage=10.00,
    created_by=user,
)

# Validate configuration
is_valid, errors = config.validate_configuration()
if is_valid:
    print(f"Configuration is valid. Price: ${config.configuration_price}")
else:
    print(f"Configuration errors: {errors}")

# Price is automatically calculated on save
print(f"Price breakdown: {config.price_breakdown}")
```

### Creating a Quote from Configuration

```python
from modules.pricing.models import Quote

# Validate first
is_valid, errors = config.validate_configuration()
if not is_valid:
    print(f"Cannot create quote: {errors}")
else:
    # Create quote
    quote = Quote.objects.create(
        firm=firm,
        quote_number="Q-2026-001",
        client=client,
        status="draft",
        created_by=user,
    )
    
    # Link configuration to quote
    config.quote = quote
    config.status = "quoted"
    config.save()
    
    print(f"Quote {quote.quote_number} created for ${config.configuration_price}")
```

---

## Pricing Calculation Logic

The CPQ engine calculates prices using the following formula:

```
1. base_total = product.base_price
2. For each selected option:
   - Add option.price_modifier to base_total
   - Multiply base_total by option.price_multiplier
   - Add value-specific price_modifier (from values array)
3. subtotal = calculated base_total
4. discount_amount = subtotal * (discount_percentage / 100)
5. final_total = subtotal - discount_amount
```

### Example Calculation

Product: Base Price = $10,000
Options:
- Team Size: "3+" → Add $18,000
- Duration: "6months" → Multiply by 1.2
- Support: "premium" → Add $2,000

Calculation:
```
1. base_total = $10,000
2. Add team_size modifier: $10,000 + $18,000 = $28,000
3. Add support modifier: $28,000 + $2,000 = $30,000
4. Apply duration multiplier: $30,000 × 1.2 = $36,000
5. subtotal = $36,000
6. Apply 10% discount: $36,000 × 0.10 = $3,600
7. final_total = $36,000 - $3,600 = $32,400
```

---

## Validation Rules

### Required Options
All options marked as `required=True` must be present in `selected_options`.

### Dependency Rules
Options with dependency rules are only valid if their dependencies are met.

Example: "Premium support" option requires "Team size: 3+" to be selected.

```json
{
  "dependency_rules": {
    "requires": [
      {
        "option": "team_size",
        "value": "3+"
      }
    ]
  }
}
```

### Valid Option Values
For select options, the selected value must be in the `values` array.

---

## Integration with Pricing Module

The CPQ system integrates with the existing pricing module:

1. **ProductConfiguration → Quote**: Configurations can be converted to quotes
2. **Quote → QuoteVersion**: Quotes are versioned with the pricing engine
3. **QuoteVersion → Invoice**: Quotes can be converted to invoices (finance module)

**Workflow:**
```
Product → Configure → Validate → Quote → Accept → Invoice → Payment
```

---

## Admin Interface

### Product Admin
- List view with filters (type, status, configurable)
- Inline editing of product options
- Bulk actions for status changes
- Search by code, name, category

### ProductOption Admin
- List view with filters (type, required)
- Grouped by product
- Reordering by display_order

### ProductConfiguration Admin
- List view with filters (product, status, quote)
- Readonly fields for calculated prices
- Admin actions:
  - Validate configurations
  - Recalculate prices
- Display price breakdown in detail view

---

## Security & Tenant Isolation

**TIER 0 Compliance:**
- All products belong to exactly one Firm
- Queries are automatically scoped to request.firm
- Portal users are explicitly denied access (DenyPortalAccess permission)
- Product options inherit firm through product relationship
- Product configurations inherit firm through product relationship

**Access Control:**
- Staff users: Full CRUD access within their firm
- Portal users: No access (pre-sale function)
- Platform operators: Metadata-only access

---

## Performance Considerations

### Indexes
- `crm_prod_firm_status_idx`: (firm, status) - Fast filtering
- `crm_prod_firm_code_idx`: (firm, code) - Fast lookup by code
- `crm_prod_firm_type_idx`: (firm, product_type) - Fast filtering by type
- `crm_prod_opt_prod_ord_idx`: (product, display_order) - Fast option ordering
- `crm_prod_cfg_prod_cre_idx`: (product, -created_at) - Fast configuration listing

### Unique Constraints
- Product: (firm, code) - Prevents duplicate product codes
- ProductOption: (product, code) - Prevents duplicate option codes

---

## Future Enhancements

**Potential Future Features:**
- Advanced pricing rules engine (volume discounts, tiered pricing)
- Product bundles with cross-product discounts
- Approval workflows for discounts above threshold
- Configuration templates (save and reuse configurations)
- Product recommendations based on customer profile
- A/B testing for product pricing
- Integration with external pricing services
- Multi-currency support with exchange rates
- Subscription management and recurring billing
- Usage-based pricing for metered services

---

## Related Documentation

- [System Invariants](../../spec/SYSTEM_INVARIANTS.md)
- [Architecture Overview](../04-explanation/architecture-overview.md)
- [API Usage Guide](./api-usage.md)
- [Pricing Engine Specification](../../docs/03-reference/requirements/DOC-09.md)
- [CRM Module Documentation](./crm-module.md)

---

## Implementation Notes

### Task 3.5 Completion

Task 3.5 "Implement CPQ (Configure-Price-Quote) engine (CRM)" includes:

✅ **Product Model**: Product catalog with multiple types and configurability  
✅ **ProductOption Model**: Configurable options with pricing impacts  
✅ **ProductConfiguration Model**: Configuration with pricing calculation  
✅ **Admin Interface**: Full admin support for all three models  
✅ **Serializers**: REST API serializers with related data  
✅ **ViewSets**: CRUD operations with firm-scoped isolation  
✅ **URL Routing**: API endpoints registered  
✅ **Migration**: Database migration created (0006_add_cpq_models.py)  
✅ **Documentation**: This reference document  

**Features Implemented:**
- Product catalog management
- Configurable options with multiple types
- Dependency rules for complex configurations
- Automatic price calculation with modifiers and multipliers
- Discount management
- Validation and error tracking
- Quote creation from configurations
- Full REST API with filtering and search
- Comprehensive admin interface

**Testing Recommendations:**
- Unit tests for price calculation logic
- Integration tests for quote creation flow
- Validation tests for dependency rules
- API endpoint tests for CRUD operations
