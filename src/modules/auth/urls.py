"""
Authentication URL routes.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    login_view,
    logout_view,
    user_profile_view,
    ChangePasswordView
)

urlpatterns = [
    # User authentication
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', login_view, name='auth_login'),
    path('logout/', logout_view, name='auth_logout'),
    path('profile/', user_profile_view, name='auth_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='auth_change_password'),

    # JWT token refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
