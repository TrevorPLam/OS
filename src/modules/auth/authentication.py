from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import Token


class CookieJWTAuthentication(JWTAuthentication):
    """
    JWT authentication that also accepts tokens from HttpOnly cookies.

    This preserves header-based auth for compatibility while enabling
    Secure + HttpOnly cookie delivery for the SPA.
    """

    def get_raw_token_from_request(self, request) -> str | None:
        """
        Try the Authorization header first, then fall back to cookie.
        """
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                return raw_token

        return request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME)

    def get_validated_token_from_request(self, request) -> Token | None:
        raw_token = self.get_raw_token_from_request(request)
        if raw_token is None:
            return None

        try:
            return self.get_validated_token(raw_token)
        except InvalidToken:
            return None

    def authenticate(self, request):
        raw_token = self.get_raw_token_from_request(request)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
