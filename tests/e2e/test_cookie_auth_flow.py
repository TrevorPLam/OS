import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


pytestmark = [pytest.mark.e2e]


class TestCookieAuthFlow(TestCase):
    def test_cookie_auth_flow_supports_profile_and_logout(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="cookiee2e",
            email="cookiee2e@example.com",
            password="E2eStrongPass!",
        )

        client = APIClient()

        login_response = client.post(
            "/api/v1/auth/login/",
            {"username": user.username, "password": "E2eStrongPass!"},
            format="json",
        )
        assert login_response.status_code == 200
        client.cookies.update(login_response.cookies)

        profile_response = client.get("/api/v1/auth/profile/")
        assert profile_response.status_code == 200
        assert profile_response.data["email"] == user.email

        refresh_response = client.post("/api/v1/auth/token/refresh/")
        assert refresh_response.status_code == 200
        client.cookies.update(refresh_response.cookies)

        logout_response = client.post("/api/v1/auth/logout/")
        assert logout_response.status_code == 200

        profile_after_logout = client.get("/api/v1/auth/profile/")
        assert profile_after_logout.status_code == 401
