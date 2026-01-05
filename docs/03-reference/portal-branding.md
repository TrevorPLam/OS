# Portal Branding & Custom Domains

Document Type: Reference  
Version: 1.0.0  
Last Updated: 2026-01-05  
Owner: Clients Module  
Status: Active  

## Overview

Portal branding allows firms to white-label the client portal with:
- Custom domain + DNS verification
- SSL certificate provisioning
- Branded email sender configuration

## API Endpoints

`PortalBrandingViewSet` in `src/modules/clients/portal_views.py` provides:

- `POST /api/v1/clients/portal-branding/verify-domain/`
- `POST /api/v1/clients/portal-branding/check-domain-status/`
- `POST /api/v1/clients/portal-branding/provision-ssl/`
- `POST /api/v1/clients/portal-branding/verify-email/`

## DNS Verification

1. Set `custom_domain` on the branding record.
2. Call **verify-domain** to receive TXT + CNAME instructions.
3. Call **check-domain-status** to validate DNS records.

Records:
- TXT: `_consultantpro-verify.<domain>` = `dns_verification_token`
- CNAME: `<domain>` → `<firm>.consultantpro.app` (or `dns_cname_target`)

## SSL Provisioning

SSL certificates are requested via AWS ACM using `boto3`.  
Set AWS credentials and region via:
- `AWS_REGION` (or `AWS_DEFAULT_REGION`)
- Standard AWS credential environment variables

## Email Sender Verification

Sender verification uses AWS SES (`verify_email_identity`).  
Set AWS credentials and region as above. After SES confirms the email identity,
toggle `email_from_address_verified` once verified.

## Admin Monitoring

Admin views are available for:
- `PortalBranding` status (custom domain, SSL, email)
- `DomainVerificationRecord` history
