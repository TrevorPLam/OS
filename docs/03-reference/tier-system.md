# Tier System Reference

Document Type: Reference
Last Updated: 2026-01-06

This document describes the subscription tier system for ConsultantPro.

## Overview

ConsultantPro offers three subscription tiers to accommodate different firm sizes and requirements. Each tier includes specific resource limits, features, and pricing.

## Subscription Tiers

### Starter
**Target**: Solo practitioners and small consulting firms

**Limits**:
- **Max Users**: 5
- **Max Clients**: 25
- **Storage**: 10 GB
- **Trial Period**: 14 days

**Features**:
- Core CRM functionality
- Basic document management
- Email ingestion
- Invoice generation
- Time tracking
- Client portal access

**Restrictions**:
- No Active Directory integration
- No custom branding
- Standard email support only

### Professional
**Target**: Growing consulting firms

**Limits**:
- **Max Users**: 25
- **Max Clients**: 250
- **Storage**: 100 GB
- **Trial Period**: 14 days

**Features**:
- All Starter features
- Pipeline deal management
- Calendar sync integrations
- Advanced reporting
- E-signature integration (DocuSign)
- SMS notifications (Twilio)
- Custom branding (logo, colors)
- Priority email support

**Restrictions**:
- No Active Directory integration
- No dedicated account manager

### Enterprise
**Target**: Large consulting organizations

**Limits**:
- **Max Users**: Unlimited
- **Max Clients**: Unlimited
- **Storage**: 1 TB (expandable)
- **Trial Period**: 30 days (negotiable)

**Features**:
- All Professional features
- Active Directory / LDAP integration
- Single Sign-On (SAML 2.0)
- Advanced security controls
- Custom retention policies
- API access with higher rate limits
- Dedicated account manager
- SLA guarantees
- Custom training sessions

**Additional Options**:
- White-label deployment
- On-premise installation
- Custom integrations

## Tier-Specific Configurations

### Database Schema
Tiers are stored in the `Firm` model:

```python
SUBSCRIPTION_TIER_CHOICES = [
    ("starter", "Starter"),
    ("professional", "Professional"),
    ("enterprise", "Enterprise"),
]
```

Reference: [src/modules/firm/models.py](../../src/modules/firm/models.py#L40-L44)

### Quota Enforcement
Quotas are enforced in the following locations:
- **User Creation**: [src/modules/firm/services.py](../../src/modules/firm/services.py) - Validates against `max_users`
- **Client Creation**: [src/modules/clients/services.py](../../src/modules/clients/services.py) - Validates against `max_clients`
- **Document Upload**: [src/modules/documents/services.py](../../src/modules/documents/services.py) - Validates against `max_storage_gb`

### Feature Availability
Feature availability by tier is controlled through:
1. **Firm Model**: Boolean flags for tier-specific features
2. **Permission System**: Role-based permissions tied to tier
3. **View Decorators**: `@requires_tier` decorator for view-level enforcement
4. **Frontend**: Feature toggles based on firm tier

## Trial Management

### Trial Period
All new firms start with a trial period:
- **Starter**: 14 days
- **Professional**: 14 days
- **Enterprise**: 30 days (negotiable)

### Trial Expiration
When `trial_ends_at` is reached:
- Firm status changes from `trial` to `suspended` if no payment method
- Read-only access to data
- Cannot create new records
- Email notifications sent 7 days, 3 days, and 1 day before expiration

### Trial Extension
Admins can extend trials via Django admin or management command:
```bash
python manage.py extend_trial --firm-id 123 --days 14
```

## Tier Upgrades & Downgrades

### Upgrade Process
1. User selects new tier from billing page
2. Prorated charge calculated for remaining billing period
3. Limits updated immediately upon payment confirmation
4. Features enabled immediately

### Downgrade Process
1. User selects lower tier (only at end of billing period)
2. System validates that current usage fits within new tier limits
3. If validation fails, user must reduce usage first:
   - Archive or delete excess users
   - Archive or delete excess clients
   - Remove or archive documents to fit storage limit
4. Downgrade takes effect at next billing cycle

### Quota Validation
Before downgrade:
- Check `current_users_count` ≤ new `max_users`
- Check `current_clients_count` ≤ new `max_clients`
- Check `current_storage_gb` ≤ new `max_storage_gb`

## Pricing

Pricing information is managed separately and not hard-coded in the application.

**Internal Reference**: See pricing module for current rates
- [src/modules/pricing/](../../src/modules/pricing/)
- Prices configured per tier and billing period (monthly/yearly)
- Discounts available for annual billing

## Tier-Specific Feature Flags

### Active Directory Integration
- **Enabled for**: Enterprise only
- **Check**: `firm.subscription_tier == 'enterprise'`

### Custom Branding
- **Enabled for**: Professional and Enterprise
- **Check**: `firm.subscription_tier in ['professional', 'enterprise']`

### API Rate Limits
- **Starter**: 100 requests/minute
- **Professional**: 300 requests/minute
- **Enterprise**: 1000 requests/minute

### SAML SSO
- **Enabled for**: Enterprise only
- **Check**: `firm.subscription_tier == 'enterprise'`

## Monitoring & Analytics

### Usage Tracking
Current usage metrics tracked in `Firm` model:
- `current_users_count`: Updated when users are created/deactivated
- `current_clients_count`: Updated when clients are created/archived
- `current_storage_gb`: Updated after document uploads/deletions

### Overage Alerts
Firms are notified when approaching limits:
- **80%**: Warning notification
- **90%**: Alert notification
- **100%**: Blocking notification with upgrade prompt

## Administration

### Changing Tier Manually
Via Django admin or management command:
```bash
python manage.py update_firm_tier --firm-id 123 --tier professional
```

### Viewing Tier Distribution
Analytics dashboard shows:
- Firms per tier
- Revenue per tier
- Usage patterns by tier
- Upgrade/downgrade trends

## See Also
- [Firm Model](../../src/modules/firm/models.py) - Tier implementation
- [Pricing Module](../../src/modules/pricing/) - Pricing logic
- [ARCHITECTURE.md](../ARCHITECTURE.md#multi-tenancy) - Multi-tenancy design
- [PERMISSIONS.md](../PERMISSIONS.md) - Permission system
