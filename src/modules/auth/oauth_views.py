"""
Sprint 1.2-1.5: OAuth Authentication Views (Google/Microsoft)

Implements SSO authentication flows with automatic user account linking/creation.
All OAuth endpoints are rate-limited to prevent abuse.

Meta-commentary:
- Current Status: OAuth callback hardened with CSRF state validation (T-135).
- Mapping: Mirrors SAML RelayState protection in saml_views.py for parity.
- Reasoning: Prevent forged OAuth callbacks by binding state to user session.
- Assumption: Frontend requests state token before initiating OAuth flow.
- Limitation: State tokens stored in session; keep session size bounded.
"""

import hmac
import logging
import secrets
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from allauth.socialaccount.models import SocialAccount, SocialApp

from modules.auth.cookies import set_auth_cookies

User = get_user_model()
logger = logging.getLogger(__name__)

OAUTH_STATE_SESSION_KEY = "oauth_state_entries"
OAUTH_STATE_TTL = timedelta(minutes=10)
OAUTH_STATE_MAX_ENTRIES = 5


def _store_oauth_state(request, state_token):
    """
    Store OAuth state token in session for CSRF protection.

    Inline commentary:
    - Mapping: Similar to SAML RelayState storage in saml_views.py.
    - Reasoning: Bind OAuth callback to the browser session that initiated it.
    """
    entries = list(request.session.get(OAUTH_STATE_SESSION_KEY, []))
    entries.append(
        {
            "token": state_token,
            "created_at": timezone.now().timestamp(),
        }
    )
    request.session[OAUTH_STATE_SESSION_KEY] = entries[-OAUTH_STATE_MAX_ENTRIES:]
    request.session.modified = True


def _clear_oauth_state(request, state_token=None):
    """Remove stored OAuth state after validation to prevent replay."""
    if state_token is None:
        request.session.pop(OAUTH_STATE_SESSION_KEY, None)
        request.session.modified = True
        return

    entries = [
        entry
        for entry in request.session.get(OAUTH_STATE_SESSION_KEY, [])
        if entry.get("token") != state_token
    ]
    if entries:
        request.session[OAUTH_STATE_SESSION_KEY] = entries
    else:
        request.session.pop(OAUTH_STATE_SESSION_KEY, None)
    request.session.modified = True


def _validate_oauth_state(request, provided_state):
    """
    Validate provided state token against session.

    Inline commentary:
    - Security: Use constant-time comparison to prevent timing attacks.
    - Security: Enforce TTL to reduce replay window.
    """
    entries = list(request.session.get(OAUTH_STATE_SESSION_KEY, []))

    def is_expired(timestamp):
        if not isinstance(timestamp, (int, float)):
            return True
        return timezone.now() - datetime.fromtimestamp(timestamp, tz=timezone.utc) > OAUTH_STATE_TTL

    entries = [entry for entry in entries if not is_expired(entry.get("created_at"))]
    if entries:
        request.session[OAUTH_STATE_SESSION_KEY] = entries
    else:
        request.session.pop(OAUTH_STATE_SESSION_KEY, None)
    request.session.modified = True

    if not provided_state or not entries:
        logger.warning(
            "OAuth CSRF validation failed: missing state",
            extra={
                "has_provided_state": bool(provided_state),
                "has_session_state": bool(entries),
                "ip_address": request.META.get("REMOTE_ADDR"),
            },
        )
        return False

    match = next(
        (
            entry
            for entry in entries
            if hmac.compare_digest(str(provided_state), str(entry.get("token")))
        ),
        None,
    )

    if not match:
        logger.warning(
            "OAuth CSRF validation failed: state mismatch",
            extra={"ip_address": request.META.get("REMOTE_ADDR")},
        )
        return False

    return True


@api_view(["GET"])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="20/m", method="GET", block=True)
def oauth_state(request):
    """
    Sprint 1.4: OAuth state token generator.

    Returns a short-lived state token stored in session to protect OAuth callbacks.
    """
    state_token = secrets.token_urlsafe(32)
    _store_oauth_state(request, state_token)
    return Response(
        {
            "state": state_token,
            "expires_in_seconds": int(OAUTH_STATE_TTL.total_seconds()),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def oauth_callback(request):
    """
    Sprint 1.4: Generic OAuth callback handler.
    
    Handles account linking/creation logic for SSO users.
    Creates JWT tokens for successful authentication.
    
    POST /api/auth/oauth/callback/
    {
        "provider": "google|microsoft",
        "access_token": "oauth_access_token",
        "email": "user@example.com",
        "state": "csrf_state_token",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    state_token = request.data.get("state")
    provider = request.data.get("provider")
    access_token = request.data.get("access_token")
    email = request.data.get("email")

    # SECURITY: Validate OAuth state token before processing callback payload.
    if not _validate_oauth_state(request, state_token):
        return Response(
            {"error": "Invalid OAuth state"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not all([provider, access_token, email]):
        _clear_oauth_state(request, state_token)
        return Response(
            {"error": "provider, access_token, and email are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Check if social account already exists
        social_account = SocialAccount.objects.filter(
            provider=provider,
            uid=email
        ).first()
        
        if social_account:
            # Existing SSO user - use linked account
            user = social_account.user
        else:
            # New SSO user - create or link to existing email
            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "username": email,
                        "first_name": request.data.get("first_name", ""),
                        "last_name": request.data.get("last_name", ""),
                    }
                )
                
                # Create social account link
                SocialAccount.objects.create(
                    user=user,
                    provider=provider,
                    uid=email,
                    extra_data={
                        "email": email,
                        "first_name": request.data.get("first_name", ""),
                        "last_name": request.data.get("last_name", ""),
                    }
                )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        response = Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                },
                "message": "OAuth login successful",
            },
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, access_token=str(refresh.access_token), refresh_token=str(refresh))
        _clear_oauth_state(request, state_token)
        return response
        
    except Exception as e:
        _clear_oauth_state(request, state_token)
        return Response(
            {"error": f"OAuth authentication failed: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET", "POST", "PUT", "DELETE"])
@permission_classes([IsAdminUser])
def oauth_provider_config(request):
    """
    Sprint 1.5: Admin UI for OAuth provider configuration.
    
    Allows administrators to configure OAuth provider credentials
    (Google, Microsoft) without modifying code.
    
    GET /api/auth/oauth/config/ - List all providers
    POST /api/auth/oauth/config/ - Add new provider
    PUT /api/auth/oauth/config/ - Update provider
    DELETE /api/auth/oauth/config/ - Remove provider
    """
    if request.method == "GET":
        # List all configured OAuth providers
        providers = SocialApp.objects.all()
        data = []
        for provider in providers:
            data.append({
                "id": provider.id,
                "provider": provider.provider,
                "name": provider.name,
                "client_id": provider.client_id,
                # Don't expose secret in responses
                "has_secret": bool(provider.secret),
            })
        return Response(data, status=status.HTTP_200_OK)
    
    elif request.method == "POST":
        # Add new OAuth provider configuration
        provider = request.data.get("provider")  # "google" or "microsoft"
        name = request.data.get("name")
        client_id = request.data.get("client_id")
        client_secret = request.data.get("client_secret")
        
        if not all([provider, name, client_id, client_secret]):
            return Response(
                {"error": "provider, name, client_id, and client_secret are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        social_app = SocialApp.objects.create(
            provider=provider,
            name=name,
            client_id=client_id,
            secret=client_secret,
        )
        
        return Response({
            "id": social_app.id,
            "provider": social_app.provider,
            "name": social_app.name,
            "message": "OAuth provider configured successfully"
        }, status=status.HTTP_201_CREATED)
    
    elif request.method == "PUT":
        # Update OAuth provider configuration
        provider_id = request.data.get("id")
        if not provider_id:
            return Response(
                {"error": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            social_app = SocialApp.objects.get(id=provider_id)
            social_app.name = request.data.get("name", social_app.name)
            social_app.client_id = request.data.get("client_id", social_app.client_id)
            if request.data.get("client_secret"):
                social_app.secret = request.data["client_secret"]
            social_app.save()
            
            return Response({
                "id": social_app.id,
                "provider": social_app.provider,
                "name": social_app.name,
                "message": "OAuth provider updated successfully"
            }, status=status.HTTP_200_OK)
        except SocialApp.DoesNotExist:
            return Response(
                {"error": "OAuth provider not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    elif request.method == "DELETE":
        # Remove OAuth provider configuration
        provider_id = request.data.get("id")
        if not provider_id:
            return Response(
                {"error": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            social_app = SocialApp.objects.get(id=provider_id)
            social_app.delete()
            return Response({
                "message": "OAuth provider removed successfully"
            }, status=status.HTTP_200_OK)
        except SocialApp.DoesNotExist:
            return Response(
                {"error": "OAuth provider not found"},
                status=status.HTTP_404_NOT_FOUND
            )
