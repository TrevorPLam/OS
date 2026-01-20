# AGENTS.md — Auth Module (Authentication & Authorization)

Last Updated: 2026-01-06
Applies To: `src/modules/auth/`

## Purpose

Handles all authentication flows: OAuth, SAML SSO, MFA, and session management.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | `SAMLConfiguration`, `UserMFAProfile` |
| `views.py` | Login, logout, password reset |
| `oauth_views.py` | Google/Microsoft OAuth callbacks |
| `saml_views.py` | SAML SSO assertion handling |
| `mfa_views.py` | MFA enrollment, verification |
| `role_permissions.py` | Role-based permission definitions |
| `serializers.py` | Auth-related serializers |
| `urls.py` | `/api/v1/auth/` routes |

## Authentication Flows

### 1. JWT Token Flow (Primary)

```
POST /api/v1/auth/login/
→ Returns: { access_token, refresh_token }

All API requests include:
Authorization: Bearer <access_token>
```

### 2. OAuth Flow (Google/Microsoft)

```
GET  /api/v1/auth/oauth/state/
→ Returns state token for CSRF protection

POST /api/v1/auth/oauth/callback/
→ Creates/links user, returns JWT
```

### 3. SAML SSO Flow

```
GET /api/v1/auth/saml/login/
→ Redirects to IdP
→ POST /api/v1/auth/saml/acs/ (Assertion Consumer Service)
→ Validates SAML response, creates session
```

### 4. MFA Flow

```
POST /api/v1/auth/mfa/setup/
→ Returns QR code for TOTP app

POST /api/v1/auth/mfa/verify/
→ Validates TOTP code
```

## Models

### SAMLConfiguration

Stores SAML IdP settings per firm:

```python
class SAMLConfiguration(models.Model):
    name: str                    # Friendly name
    sp_entity_id: str            # Service Provider Entity ID
    idp_entity_id: str           # Identity Provider Entity ID
    idp_sso_url: str             # IdP SSO URL
    idp_x509_cert: str           # IdP certificate
    attribute_mapping: dict      # SAML → User field mapping
    is_active: bool              # Only one active per firm
```

### UserMFAProfile

Extends User with MFA settings:

```python
class UserMFAProfile(models.Model):
    user: OneToOne[User]
    phone_number: str            # For SMS MFA
    sms_mfa_enabled: bool
```

## Role Permissions

Defined in `role_permissions.py`:

| Role | Description |
|------|-------------|
| `master_admin` | Full platform access |
| `firm_admin` | Firm-level admin |
| `staff` | Standard firm user |
| `portal_user` | Client portal access only |

## Security Invariants

1. **Token Expiry**: Access tokens expire in 15 minutes
2. **Refresh Rotation**: Refresh tokens are single-use
3. **MFA Required**: For sensitive operations (configurable)
4. **SAML Signature**: All SAML assertions MUST be signed

## Dependencies

- **Depends on**: `firm/` (for firm context)
- **Used by**: All authenticated endpoints
- **External**: django-allauth, django-otp, python3-saml

## URLs

All routes under `/api/v1/auth/`:

```
POST   /login/                  # JWT login
POST   /logout/                 # Blacklist token
POST   /refresh/                # Refresh token
GET    /oauth/state/            # Generate OAuth state token
POST   /oauth/callback/         # OAuth callback handler
GET    /saml/login/             # Start SAML SSO
POST   /saml/acs/               # SAML assertion endpoint
POST   /mfa/setup/              # Setup TOTP
POST   /mfa/verify/             # Verify TOTP code
```
