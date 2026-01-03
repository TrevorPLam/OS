"""
Tests for Content Security Policy (CSP) middleware

Security Task: SEC-4 - Add Content-Security-Policy header
"""

import pytest
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from config.csp_middleware import ContentSecurityPolicyMiddleware


def get_mock_response():
    """Mock response for middleware."""
    return HttpResponse("OK")


class TestContentSecurityPolicyMiddleware:
    """Test CSP middleware behavior in production and development modes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.middleware = ContentSecurityPolicyMiddleware(get_response=lambda r: get_mock_response())
    
    @override_settings(DEBUG=False)
    def test_csp_header_added_in_production(self):
        """CSP header should be present when DEBUG=False."""
        request = self.factory.get("/")
        response = self.middleware.process_response(request, get_mock_response())
        
        assert "Content-Security-Policy" in response
        csp_header = response["Content-Security-Policy"]
        
        # Verify key directives are present
        assert "default-src 'self'" in csp_header
        assert "script-src 'self'" in csp_header
        assert "frame-ancestors 'none'" in csp_header
        assert "object-src 'none'" in csp_header
    
    @override_settings(DEBUG=True)
    def test_csp_header_not_added_in_development(self):
        """CSP header should NOT be present when DEBUG=True."""
        request = self.factory.get("/")
        response = self.middleware.process_response(request, get_mock_response())
        
        assert "Content-Security-Policy" not in response
    
    @override_settings(
        DEBUG=False,
        CSP_DEFAULT_SRC=("'self'",),
        CSP_SCRIPT_SRC=("'self'", "https://example.com"),
        CSP_STYLE_SRC=("'self'", "'unsafe-inline'"),
    )
    def test_csp_directives_from_settings(self):
        """CSP directives should be built from settings."""
        request = self.factory.get("/")
        response = self.middleware.process_response(request, get_mock_response())
        
        csp_header = response["Content-Security-Policy"]
        
        # Verify configured directives
        assert "default-src 'self'" in csp_header
        assert "script-src 'self' https://example.com" in csp_header
        assert "style-src 'self' 'unsafe-inline'" in csp_header
    
    @override_settings(
        DEBUG=False,
        CSP_DEFAULT_SRC=("'self'",),
        CSP_REPORT_URI="https://csp-report.example.com/report"
    )
    def test_csp_report_uri(self):
        """CSP report-uri directive should be included if configured."""
        request = self.factory.get("/")
        response = self.middleware.process_response(request, get_mock_response())
        
        csp_header = response["Content-Security-Policy"]
        assert "report-uri https://csp-report.example.com/report" in csp_header
    
    @override_settings(DEBUG=False)
    def test_csp_prevents_inline_scripts(self):
        """CSP should not allow 'unsafe-inline' for scripts by default."""
        request = self.factory.get("/")
        response = self.middleware.process_response(request, get_mock_response())
        
        csp_header = response["Content-Security-Policy"]
        
        # Should not have unsafe-inline for scripts (XSS protection)
        script_directive = [d for d in csp_header.split(";") if "script-src" in d][0]
        assert "'unsafe-inline'" not in script_directive
    
    @override_settings(DEBUG=False)
    def test_csp_allows_inline_styles(self):
        """CSP should allow 'unsafe-inline' for styles (required for React)."""
        request = self.factory.get("/")
        response = self.middleware.process_response(request, get_mock_response())
        
        csp_header = response["Content-Security-Policy"]
        
        # Should have unsafe-inline for styles (React requirement)
        style_directive = [d for d in csp_header.split(";") if "style-src" in d][0]
        assert "'unsafe-inline'" in style_directive
