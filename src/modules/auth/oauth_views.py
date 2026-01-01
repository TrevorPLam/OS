"""
Sprint 1.2-1.5: OAuth Authentication Views (Google/Microsoft)

Implements SSO authentication flows with automatic user account linking/creation.
All OAuth endpoints are rate-limited to prevent abuse.
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from allauth.socialaccount.models import SocialAccount, SocialApp

from modules.firm.models import FirmMembership

User = get_user_model()


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
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    provider = request.data.get("provider")
    access_token = request.data.get("access_token")
    email = request.data.get("email")
    
    if not all([provider, access_token, email]):
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
        
        return Response({
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "message": "OAuth login successful"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
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
