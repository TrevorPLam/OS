from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


def _create_user(username: str = "cookieuser", password: str = "Str0ngPass!"):
    user_model = get_user_model()
    return user_model.objects.create_user(username=username, email=f"{username}@example.com", password=password)


class TestCookieAuthentication(TestCase):
    def test_login_sets_secure_http_only_cookies(self):
        user = _create_user()
        client = APIClient()

        response = client.post(
            "/api/v1/auth/login/",
            {"username": user.username, "password": "Str0ngPass!"},
            format="json",
        )

        assert response.status_code == 200
        access_cookie = response.cookies[settings.ACCESS_TOKEN_COOKIE_NAME]
        refresh_cookie = response.cookies[settings.REFRESH_TOKEN_COOKIE_NAME]

        assert access_cookie["httponly"]
        assert access_cookie["secure"]
        assert str(access_cookie["samesite"]).lower() == settings.AUTH_COOKIE_SAMESITE.lower()

        assert refresh_cookie["httponly"]
        assert refresh_cookie["secure"]
        assert str(refresh_cookie["samesite"]).lower() == settings.AUTH_COOKIE_SAMESITE.lower()

    def test_refresh_rotates_tokens_and_updates_cookies(self):
        user = _create_user(username="rotatinguser")
        client = APIClient()

        login_response = client.post(
            "/api/v1/auth/login/",
            {"username": user.username, "password": "Str0ngPass!"},
            format="json",
        )
        client.cookies.update(login_response.cookies)
        original_refresh_token = login_response.cookies[settings.REFRESH_TOKEN_COOKIE_NAME].value

        refresh_response = client.post("/api/v1/auth/token/refresh/")

        assert refresh_response.status_code == 200
        rotated_refresh_token = refresh_response.cookies[settings.REFRESH_TOKEN_COOKIE_NAME].value
        assert rotated_refresh_token != original_refresh_token
        assert settings.ACCESS_TOKEN_COOKIE_NAME in refresh_response.cookies

    def test_logout_clears_cookies_and_invalidates_refresh(self):
        user = _create_user(username="logoutuser")
        client = APIClient()

        login_response = client.post(
            "/api/v1/auth/login/",
            {"username": user.username, "password": "Str0ngPass!"},
            format="json",
        )
        client.cookies.update(login_response.cookies)
        previous_refresh = login_response.cookies[settings.REFRESH_TOKEN_COOKIE_NAME].value

        logout_response = client.post("/api/v1/auth/logout/")
        access_cookie = logout_response.cookies[settings.ACCESS_TOKEN_COOKIE_NAME]
        refresh_cookie = logout_response.cookies[settings.REFRESH_TOKEN_COOKIE_NAME]

        assert logout_response.status_code == 200
        assert access_cookie.value == ""
        assert refresh_cookie.value == ""
        assert int(access_cookie["max-age"]) == 0
        assert int(refresh_cookie["max-age"]) == 0

        client.cookies[settings.REFRESH_TOKEN_COOKIE_NAME] = previous_refresh
        failed_refresh = client.post("/api/v1/auth/token/refresh/")
        assert failed_refresh.status_code == 401
