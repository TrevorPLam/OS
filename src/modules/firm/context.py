from dataclasses import dataclass

from django.conf import settings
from django.http import HttpRequest
from rest_framework_simplejwt.backends import TokenBackend

from .models import Firm


@dataclass(frozen=True)
class FirmContext:
    firm: Firm
    source: str


def _get_host_subdomain(request: HttpRequest) -> str | None:
    host = request.get_host().split(":")[0]
    if host in {"localhost", "127.0.0.1"} or host.replace(".", "").isdigit():
        return None
    parts = host.split(".")
    if len(parts) < 3:
        return None
    subdomain = parts[0].lower()
    if subdomain in {"www"}:
        return None
    return subdomain


def _resolve_firm_from_subdomain(request: HttpRequest) -> Firm | None:
    subdomain = _get_host_subdomain(request)
    if not subdomain:
        return None
    return Firm.objects.filter(slug=subdomain).first()


def _resolve_firm_from_session(request: HttpRequest) -> Firm | None:
    firm_id = request.session.get("firm_id")
    if not firm_id:
        return None
    return Firm.objects.filter(id=firm_id).first()


def _resolve_firm_from_token(request: HttpRequest) -> Firm | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None
    token_backend = TokenBackend(
        algorithm=settings.SIMPLE_JWT["ALGORITHM"],
        signing_key=settings.SIMPLE_JWT["SIGNING_KEY"],
        verifying_key=settings.SIMPLE_JWT.get("VERIFYING_KEY"),
    )
    try:
        payload = token_backend.decode(token, verify=True)
    except Exception:
        return None
    firm_id = payload.get("firm_id")
    if firm_id:
        return Firm.objects.filter(id=firm_id).first()
    firm_slug = payload.get("firm_slug")
    if firm_slug:
        return Firm.objects.filter(slug=firm_slug).first()
    return None


def resolve_firm_context(request: HttpRequest) -> FirmContext | None:
    firm = _resolve_firm_from_subdomain(request)
    if firm:
        return FirmContext(firm=firm, source="subdomain")

    firm = _resolve_firm_from_session(request)
    if firm:
        return FirmContext(firm=firm, source="session")

    firm = _resolve_firm_from_token(request)
    if firm:
        return FirmContext(firm=firm, source="token")

    return None
