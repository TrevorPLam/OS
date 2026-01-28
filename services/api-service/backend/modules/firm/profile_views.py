"""
User Profile Views.

Provides API endpoints for user profile customization.
Allows staff to manage their profile photos, signatures, and preferences.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from config.query_guards import QueryTimeoutMixin
from modules.auth.role_permissions import IsStaffUser
from modules.firm.models import FirmMembership
from modules.firm.profile_extensions import UserProfile
from modules.firm.profile_serializers import (
    UserProfileSerializer,
    UserProfilePhotoUploadSerializer,
    EmailSignatureGenerateSerializer,
)


class UserProfileViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for UserProfile management.

    Allows staff users to manage their profile customization settings.
    """

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['firm_membership__firm', 'firm_membership__user']
    search_fields = [
        'job_title',
        'bio',
        'firm_membership__user__first_name',
        'firm_membership__user__last_name',
        'firm_membership__user__email',
    ]
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter by firm context.

        Users can see profiles for their firm only.
        """
        queryset = super().get_queryset()

        # Filter to profiles in user's firm
        queryset = queryset.filter(firm_membership__firm=self.request.firm)

        return queryset.select_related(
            'firm_membership',
            'firm_membership__user',
            'firm_membership__firm'
        )

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """
        Get current user's profile.

        Returns the profile for the currently authenticated user.

        Response:
            UserProfile object for current user
        """
        try:
            # Get user's firm membership
            firm_membership = FirmMembership.objects.get(
                user=request.user,
                firm=request.firm,
                is_active=True
            )

            # Get or create profile
            profile, created = UserProfile.objects.get_or_create(
                firm_membership=firm_membership
            )

            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except FirmMembership.DoesNotExist:
            return Response(
                {'error': 'No active firm membership found for current user'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def generate_signature(self, request, pk=None):
        """
        Generate email signature preview.

        Generates a default email signature based on profile information.

        Request body:
            {
                "html": true  # Optional, default: true
            }

        Response:
            {
                "signature": "...",
                "format": "html" or "plain"
            }
        """
        profile = self.get_object()
        serializer = EmailSignatureGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        html = serializer.validated_data.get('html', True)

        # Generate signature
        signature = profile.generate_default_signature(html=html)

        return Response({
            'signature': signature,
            'format': 'html' if html else 'plain',
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def upload_photo(self, request, pk=None):
        """
        Upload profile photo.

        Upload and replace profile photo for user.

        Request body (multipart/form-data):
            profile_photo: image file (max 2MB)

        Response:
            {
                "message": "Profile photo uploaded successfully",
                "profile_photo_url": "..."
            }
        """
        profile = self.get_object()
        serializer = UserProfilePhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save uploaded photo
        profile.profile_photo = serializer.validated_data['profile_photo']
        profile.save(update_fields=['profile_photo', 'updated_at'])

        return Response({
            'message': 'Profile photo uploaded successfully',
            'profile_photo_url': profile.get_profile_photo_url(),
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def delete_photo(self, request, pk=None):
        """
        Delete profile photo.

        Removes the profile photo and reverts to default avatar.

        Response:
            {
                "message": "Profile photo deleted",
                "profile_photo_url": "..."  # Default avatar URL
            }
        """
        profile = self.get_object()

        # Delete photo file if it exists
        if profile.profile_photo:
            profile.profile_photo.delete(save=False)
            profile.profile_photo = None
            profile.save(update_fields=['profile_photo', 'updated_at'])

        return Response({
            'message': 'Profile photo deleted',
            'profile_photo_url': profile.get_profile_photo_url(),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def team_directory(self, request):
        """
        Get team directory with public profile information.

        Returns profiles for all active team members in current firm,
        respecting visibility settings.

        Response: List of public profiles
        """
        queryset = self.get_queryset().filter(
            firm_membership__is_active=True
        )

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
