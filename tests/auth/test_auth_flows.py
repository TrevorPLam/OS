from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


def _create_user(username: str = "authuser", password: str = "Str0ngPass!"):
    """
    Create a user for auth flow tests.

    Keeping this helper central avoids duplicating setup logic across tests.
    """
    user_model = get_user_model()
    return user_model.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
    )


def _login(client: APIClient, username: str, password: str):
    """
    Login helper to keep tests focused on assertions instead of request boilerplate.
    """
    return client.post(
        "/api/v1/auth/login/",
        {"username": username, "password": password},
        format="json",
    )


class TestAuthFlowUnitTests(TestCase):
    def test_login_happy_path_returns_user_payload(self):
        """
        Ensure successful login returns user payload for immediate UI hydration.
        """
        user = _create_user()
        client = APIClient()

        response = _login(client, user.username, "Str0ngPass!")

        assert response.status_code == 200
        assert response.data["user"]["username"] == user.username

    def test_login_empty_password_returns_400(self):
        """
        Empty input should fail fast to prevent ambiguous auth errors.
        """
        client = APIClient()

        response = client.post(
            "/api/v1/auth/login/",
            {"username": "missing-pass"},
            format="json",
        )

        assert response.status_code == 400
        assert "password" in response.data

    def test_login_invalid_password_returns_401(self):
        """
        Invalid credentials should return 401 without revealing which field failed.
        """
        user = _create_user(username="wrongpass-user")
        client = APIClient()

        response = _login(client, user.username, "WrongPass!")

        assert response.status_code == 401
        assert response.data["error"] == "Invalid username or password"

    def test_refresh_happy_path_sets_new_access_cookie(self):
        """
        Valid refresh token should yield a fresh access cookie for continued sessions.
        """
        user = _create_user(username="refresh-user")
        client = APIClient()

        login_response = _login(client, user.username, "Str0ngPass!")
        client.cookies.update(login_response.cookies)

        response = client.post("/api/v1/auth/token/refresh/")

        assert response.status_code == 200
        assert settings.ACCESS_TOKEN_COOKIE_NAME in response.cookies

    def test_refresh_empty_request_returns_400(self):
        """
        Missing refresh token is an explicit error to prevent silent session drift.
        """
        client = APIClient()

        response = client.post("/api/v1/auth/token/refresh/")

        assert response.status_code == 400
        assert response.data["error"] == "Refresh token missing"

    def test_refresh_invalid_token_returns_401(self):
        """
        Invalid refresh tokens should fail cleanly for predictable client handling.
        """
        client = APIClient()

        response = client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": "not-a-token"},
            format="json",
        )

        assert response.status_code == 401
        assert response.data["error"] == "Refresh token invalid"

    def test_logout_missing_refresh_still_clears_cookies(self):
        """
        Even without a refresh token, logout should clear cookies to end the session.
        """
        user = _create_user(username="logout-missing-refresh")
        client = APIClient()

        login_response = _login(client, user.username, "Str0ngPass!")
        client.cookies.update(login_response.cookies)

        # Drop the refresh cookie to simulate a partial/missing token scenario.
        client.cookies.pop(settings.REFRESH_TOKEN_COOKIE_NAME, None)

        response = client.post("/api/v1/auth/logout/")

        assert response.status_code == 200
        assert response.data["message"] == "Logout successful"
        assert response.cookies[settings.ACCESS_TOKEN_COOKIE_NAME].value == ""
        assert response.cookies[settings.REFRESH_TOKEN_COOKIE_NAME].value == ""

    def test_logout_invalid_refresh_returns_safe_message(self):
        """
        Invalid refresh tokens should not crash logout, only return a safe message.
        """
        user = _create_user(username="logout-invalid-refresh")
        client = APIClient()

        login_response = _login(client, user.username, "Str0ngPass!")
        client.cookies.update(login_response.cookies)
        client.cookies[settings.REFRESH_TOKEN_COOKIE_NAME] = "not-a-token"

        response = client.post("/api/v1/auth/logout/")

        assert response.status_code == 200
        assert response.data["message"] == "Logout successful (token already invalidated)"
