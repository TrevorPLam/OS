from django.conf import settings
from django.http import JsonResponse

from config.platform import resolve_platform_role
from .context import resolve_firm_context


class FirmContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exempt_paths = getattr(settings, "FIRM_CONTEXT_EXEMPT_PATHS", [])
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)

        context = resolve_firm_context(request)
        if not context:
            return JsonResponse(
                {"detail": "Firm context is required."},
                status=400,
            )

        request.firm = context.firm
        request.firm_id = context.firm.id
        request.firm_context_source = context.source
        request.platform_role = resolve_platform_role(request.user)
        return self.get_response(request)
