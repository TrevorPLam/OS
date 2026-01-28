from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.http import HttpResponseBase
from rest_framework.response import Response


def _cookie_params(max_age: timedelta | int | None) -> dict:
    """
    Shared cookie parameters for auth cookies.
    """
    params: dict = {
        "httponly": True,
        "secure": True,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "path": settings.AUTH_COOKIE_PATH,
    }

    if isinstance(max_age, timedelta):
        params["max_age"] = int(max_age.total_seconds())
    elif isinstance(max_age, int):
        params["max_age"] = max_age

    if settings.AUTH_COOKIE_DOMAIN:
        params["domain"] = settings.AUTH_COOKIE_DOMAIN

    return params


def set_auth_cookies(
    response: HttpResponseBase | Response,
    *,
    access_token: str,
    refresh_token: Optional[str],
) -> None:
    """
    Attach access and refresh cookies with secure attributes.
    """
    response.set_cookie(
        settings.ACCESS_TOKEN_COOKIE_NAME,
        access_token,
        **_cookie_params(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]),
    )

    if refresh_token:
        response.set_cookie(
            settings.REFRESH_TOKEN_COOKIE_NAME,
            refresh_token,
            **_cookie_params(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]),
        )


def clear_auth_cookies(response: HttpResponseBase | Response) -> None:
    """
    Remove auth cookies.
    """
    response.delete_cookie(
        settings.ACCESS_TOKEN_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.REFRESH_TOKEN_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
