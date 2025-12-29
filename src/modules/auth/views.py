"""
Authentication Views.

SECURITY: All public authentication endpoints are rate-limited to prevent
brute force attacks. See django-ratelimit documentation for configuration.
"""

from django.contrib.auth import authenticate, get_user_model
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import ChangePasswordSerializer, LoginSerializer, RegisterSerializer, UserSerializer

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

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "message": "User created successfully",
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

    return Response(
        {
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "message": "Login successful",
        },
        status=status.HTTP_200_OK,
    )


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
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
