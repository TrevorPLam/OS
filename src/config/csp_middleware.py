"""
Content Security Policy (CSP) Middleware

Implements CSP header for production environments to prevent XSS attacks.
See SECURITY.md for configuration details.

Security Task: SEC-4 - Add Content-Security-Policy header
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    """
    Adds Content-Security-Policy header to all responses in production.
    
    CSP configuration is defined in settings.py via CSP_* variables.
    Only active when DEBUG=False.
    """
    
    def process_response(self, request, response):
        """Add CSP header to response if in production mode."""
        if not settings.DEBUG:
            csp_directives = self._build_csp_directives()
            if csp_directives:
                response["Content-Security-Policy"] = csp_directives
        return response
    
    def _build_csp_directives(self):
        """Build CSP directive string from settings."""
        directives = []
        
        # Map of CSP directive names to their settings
        directive_map = {
            "default-src": "CSP_DEFAULT_SRC",
            "script-src": "CSP_SCRIPT_SRC",
            "style-src": "CSP_STYLE_SRC",
            "img-src": "CSP_IMG_SRC",
            "font-src": "CSP_FONT_SRC",
            "connect-src": "CSP_CONNECT_SRC",
            "frame-ancestors": "CSP_FRAME_ANCESTORS",
            "base-uri": "CSP_BASE_URI",
            "form-action": "CSP_FORM_ACTION",
            "object-src": "CSP_OBJECT_SRC",
        }
        
        for directive_name, setting_name in directive_map.items():
            sources = getattr(settings, setting_name, None)
            if sources:
                # Join sources with spaces
                sources_str = " ".join(sources)
                directives.append(f"{directive_name} {sources_str}")
        
        # Add report-uri if configured
        report_uri = getattr(settings, "CSP_REPORT_URI", None)
        if report_uri:
            directives.append(f"report-uri {report_uri}")
        
        return "; ".join(directives) if directives else ""
