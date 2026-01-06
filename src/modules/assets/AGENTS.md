# AGENTS.md — Assets Module

Last Updated: 2026-01-06
Applies To: `src/modules/assets/`

## Purpose

Asset management for firm equipment and resources.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | Asset, AssetCategory, AssetAssignment |

## Domain Model

```
AssetCategory (organization)
    └── Asset (equipment/resource)
            └── AssetAssignment (who has it)
```

## Key Models

### Asset

Firm asset:

```python
class Asset(models.Model):
    firm: FK[Firm]
    category: FK[AssetCategory]
    
    name: str
    serial_number: str
    
    status: str                       # available, assigned, maintenance, retired
    
    purchase_date: Date
    purchase_price: Decimal
    warranty_expires: Date
    
    # Current assignment
    assigned_to: FK[User]
    assigned_at: DateTime
```

## Dependencies

- **Depends on**: `firm/`

## URLs

All routes under `/api/v1/assets/`:

```
GET/POST   /categories/
GET/POST   /assets/
GET/PUT    /assets/{id}/
POST       /assets/{id}/assign/
POST       /assets/{id}/unassign/
```
