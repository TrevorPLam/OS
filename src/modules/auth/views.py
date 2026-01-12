"""
Authentication Views.

SECURITY: All public authentication endpoints are rate-limited to prevent
brute force attacks. See django-ratelimit documentation for configuration.
"""

import hmac

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenViewBase

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    ProvisionFirmSerializer,
    RegisterSerializer,
    UserSerializer,
)
from modules.auth.cookies import clear_auth_cookies, set_auth_cookies
from modules.firm.provisioning import provision_firm

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.

    Rate limited to 5 requests per minute per IP to prevent abuse.

    POST /api/auth/register/
    {
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "SecurePass123!",
        "password2": "SecurePass123!"
    }
    """

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @ratelimit(key="ip", rate="5/m", method="POST", block=True)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "user": UserSerializer(user).data,
                "message": "User created successfully",
            },
            status=status.HTTP_201_CREATED,
        )
        set_auth_cookies(response, access_token=str(refresh.access_token), refresh_token=str(refresh))
        return response


@api_view(["POST"])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="2/m", method="POST", block=True)
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def provision_firm_view(request):
    """
    Debug-only endpoint to provision a firm for E2E testing.

    Requires:
    - DEBUG=True
    - X-E2E-Seed: <token>
    """
    seed_header = request.headers.get("X-E2E-Seed", "")
    expected_token = settings.E2E_PROVISION_TOKEN or ""

    if (
        not settings.DEBUG
        or not expected_token
        or not hmac.compare_digest(seed_header, expected_token)
    ):
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProvisionFirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    result = provision_firm(**data)

    admin_user = result["admin_user"]
    firm = result["firm"]

    return Response(
        {
            "firm_id": firm.id,
            "firm_slug": firm.slug,
            "admin_user_id": admin_user.id,
            "admin_username": admin_user.username,
            "admin_email": admin_user.email,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def login_view(request):
    """
    User login endpoint.

    Rate limited to 10 requests per minute per IP to prevent brute force attacks.

    POST /api/auth/login/
    {
        "username": "john_doe",
        "password": "SecurePass123!"
    }
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    user = authenticate(username=username, password=password)

    if user is None:
        return Response({"error": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    response = Response(
        {
            "user": UserSerializer(user).data,
            "message": "Login successful",
        },
        status=status.HTTP_200_OK,
    )
    set_auth_cookies(response, access_token=str(refresh.access_token), refresh_token=str(refresh))
    return response


@method_decorator(ratelimit(key="ip", rate="20/m", method="POST", block=True), name="post")
class CookieTokenRefreshView(TokenViewBase):
    serializer_class = TokenRefreshSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh") or request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
        if not refresh_token:
            return Response({"error": "Refresh token missing"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError):
            return Response({"error": "Refresh token invalid"}, status=status.HTTP_401_UNAUTHORIZED)

        access = str(serializer.validated_data["access"])
        rotated_refresh = serializer.validated_data.get("refresh")
        refresh_value = str(rotated_refresh) if rotated_refresh else refresh_token
        response = Response({"message": "Token refreshed"}, status=status.HTTP_200_OK)
        set_auth_cookies(
            response,
            access_token=access,
            refresh_token=refresh_value,
        )
        return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    User logout endpoint.

    POST /api/auth/logout/
    {
        "refresh": "refresh_token_here"
    }
    """
    refresh_token = request.data.get("refresh") or request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)

    response = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    if refresh_token:
        try:
            RefreshToken(refresh_token).blacklist()
        except Exception:
            # If the token is already invalid/expired, proceed with cookie clearing
            response.data = {"message": "Logout successful (token already invalidated)"}

    clear_auth_cookies(response)
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """
    Get current user profile.

    GET /api/auth/profile/
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(generics.UpdateAPIView):
    """
    Change password endpoint.

    PUT /api/auth/change-password/
    {
        "old_password": "OldPass123!",
        "new_password": "NewPass456!"
    }
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        # Check old password
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        # Set new password
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
