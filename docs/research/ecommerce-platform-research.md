# E-commerce Platform Research (Shopify, WooCommerce, BigCommerce)

**Status:** Research Complete  
**Last Updated:** January 5, 2026  
**Owner:** Integrations Team  
**Canonical Status:** Supporting  
**Related Tasks:** ECOM-1 (Research e-commerce platforms), ECOM-2 through ECOM-6  
**Priority:** LOW

## Goals

- Identify the best initial e-commerce platform target and shared abstractions for orders, customers, carts, and products.  
- Outline authentication, rate limits, and webhooks to inform connector design.

## Platform Comparison

### Shopify (Recommended Starting Point)
- **Auth:** OAuth 2.0 with offline + online tokens; HMAC validation on webhooks.  
- **Data Model Fit:** Strong support for orders, line items, customers, fulfillment events; mature GraphQL Admin API.  
- **Webhooks:** Orders/create, orders/updated, carts/update, customers/create, app/uninstalled.  
- **Rate Limits:** Leaky bucket (GraphQL cost-based); requires throttling middleware.  
- **App Store:** Distribution path for firm-owned apps; requires branding and billing compliance.

### WooCommerce
- **Auth:** OAuth 1.0a or Application Passwords; self-hosted variability increases support overhead.  
- **Data Model Fit:** Orders, customers, coupons available; plugins may alter schemas.  
- **Webhooks:** Order and product events; reliability varies by host.  
- **Rate Limits:** None by default; must self-impose throttling.  
- **Support Risks:** Wide plugin ecosystem causes schema drift; higher QA cost.

### BigCommerce
- **Auth:** OAuth 2.0 with signed payloads; uses store hash for scoping.  
- **Data Model Fit:** Orders, products, customers, catalog features; good webhook coverage.  
- **Rate Limits:** Requests per hour; backoff headers provided.  
- **Distribution:** Marketplace app requirements similar to Shopify.

## Cross-Platform Abstractions

- **Entities:** `Order`, `OrderItem`, `Customer`, `Product`, `Cart`, `Fulfillment`, `Refund`.  
- **Sync Flows:** inbound webhooks → queue → normalizer → persistence layer → automation triggers.  
- **Webhooks Security:** Validate signatures/HMAC for all providers; store signing secrets per firm.  
- **Rate Limiting:** Provider-specific throttling with retry/backoff; central metrics on 429s and retry budgets.

## Recommended Phased Approach

1. **Phase 1 (Shopify Beta):** Build Shopify connector first; focus on orders/customers webhooks and manual backfill endpoint.  
2. **Phase 2 (Harden):** Add storefront webhook coverage (carts, checkouts), implement DLQ + replay.  
3. **Phase 3 (Expand):** Add BigCommerce connector using same abstractions; evaluate WooCommerce only for high-demand firms.  
4. **Phase 4 (Automation):** Expose events to automation engine (triggers for order created, fulfillment updated, refund issued).

## Acceptance Criteria (ECOM-1)

- Comparative analysis completed with recommended initial platform (Shopify).  
- Cross-platform abstractions identified for orders/customers/products.  
- Phased rollout captured to inform connector implementation.
