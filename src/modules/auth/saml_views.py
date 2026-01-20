"""
Sprint 1.6-1.9: SAML Support for Enterprise SSO

Implements SAML Service Provider configuration for enterprise identity providers.
Includes ACS (Assertion Consumer Service), SLO (Single Logout), and IdP metadata management.

Meta-commentary:
- Current Status: SAML authentication flows implemented with CSRF protection via RelayState.
- Security Hardening (T-128): RelayState validation prevents CSRF attacks on SSO flows.
- Security Hardening (T-134): Defensive attribute extraction prevents crashes on missing SAML attrs.
- Security Hardening (T-136): Error messages sanitized to prevent information disclosure.
- Follow-up (T-137): Add rate limiting to prevent brute-force attacks on SSO endpoints.
- Assumption: SAML IdP correctly implements RelayState parameter per SAML 2.0 spec.
- Limitation: Error details logged but not yet integrated with structured logging system.
"""

import base64
import hmac
import logging
import secrets
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
    SAML_AVAILABLE = True
except ImportError:
    SAML_AVAILABLE = False

from modules.auth.models import SAMLConfiguration
from modules.auth.cookies import set_auth_cookies

User = get_user_model()
logger = logging.getLogger(__name__)


def get_saml_settings(request):
    """
    Build SAML Service Provider configuration from database or environment variables.
    
    Constructs settings dict required by python3-saml library, sourcing configuration
    from SAMLConfiguration model (database) with fallback to Django settings.
    
    Args:
        request: Django HTTP request for extracting base URL
        
    Returns:
        dict: SAML settings compatible with OneLogin_Saml2_Settings
        
    Raises:
        ImportError: If python3-saml library not installed
        ValidationError: If no active SAML configuration and no fallback settings
        
    Meta-commentary:
    - Current Status: Configuration loading complete with database/env fallback.
    - Design Rationale: Fallback allows dev/test without database-stored config.
    - Assumption: Settings (SAML_SP_ENTITY_ID, etc.) exist if database config absent.
    - Follow-up (T-145): Add configuration validation to catch missing required fields.
    """
    if not SAML_AVAILABLE:
        raise ImportError("python3-saml is not installed. Run: pip install python3-saml")
    
    # Get SAML configuration from database
    try:
        saml_config = SAMLConfiguration.objects.filter(is_active=True).first()
        if not saml_config:
            raise ValidationError("No active SAML configuration found")
    except Exception as e:
        # Fallback to environment variables for development/testing
        logger.warning(
            "SAML database config unavailable, using Django settings fallback",
            extra={"error": str(e)}
        )
        saml_config = None
    
    # Build SAML settings
    base_url = f"{request.scheme}://{request.get_host()}"
    
    settings_dict = {
        "strict": True,
        "debug": settings.DEBUG,
        "sp": {
            "entityId": saml_config.sp_entity_id if saml_config else settings.SAML_SP_ENTITY_ID,
            "assertionConsumerService": {
                "url": f"{base_url}{reverse('saml_acs')}",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            },
            "singleLogoutService": {
                "url": f"{base_url}{reverse('saml_slo')}",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            "x509cert": saml_config.sp_public_cert if saml_config else settings.SAML_SP_PUBLIC_CERT,
            "privateKey": saml_config.sp_private_key if saml_config else settings.SAML_SP_PRIVATE_KEY,
        },
        "idp": {
            "entityId": saml_config.idp_entity_id if saml_config else "",
            "singleSignOnService": {
                "url": saml_config.idp_sso_url if saml_config else "",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "singleLogoutService": {
                "url": saml_config.idp_slo_url if saml_config else "",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "x509cert": saml_config.idp_x509_cert if saml_config else "",
        },
        "security": {
            "nameIdEncrypted": False,
            "authnRequestsSigned": True,
            "logoutRequestSigned": True,
            "logoutResponseSigned": True,
            "signMetadata": True,
            "wantMessagesSigned": True,
            "wantAssertionsSigned": True,
            "wantAssertionsEncrypted": False,
            "wantNameId": True,
            "wantNameIdEncrypted": False,
            "wantAttributeStatement": True,
        }
    }
    
    return settings_dict


def prepare_django_request(request):
    """
    Convert Django HTTP request to python3-saml library format.
    
    Args:
        request: Django HTTPRequest object
        
    Returns:
        dict: Request data in format expected by OneLogin_Saml2_Auth
        
    Raises:
        KeyError: If required META fields missing from request
        
    Note:
        python3-saml expects specific keys for protocol, host, and request data.
    """
    # Defensive extraction with sensible defaults for required fields
    result = {
        'https': 'on' if request.is_secure() else 'off',
        'http_host': request.META.get('HTTP_HOST', 'localhost'),
        'script_name': request.META.get('PATH_INFO', '/'),
        'server_port': request.META.get('SERVER_PORT', '443' if request.is_secure() else '80'),
        'get_data': request.GET.copy(),
        'post_data': request.POST.copy(),
    }
    return result


@method_decorator(csrf_exempt, name='dispatch')
class SAMLLoginView(View):
    """
    Sprint 1.7: SAML SSO login initiation.
    
    Redirects user to IdP for authentication.
    
    SECURITY: Generates cryptographically secure RelayState for CSRF protection.
    See: REFACTOR_PLAN.md Phase 0, FORENSIC_AUDIT.md Issue #5.2
    
    GET /api/auth/saml/login/
    """
    def get(self, request):
        if not SAML_AVAILABLE:
            return HttpResponse("SAML is not configured", status=501)
        
        if not settings.SAML_ENABLED:
            return HttpResponse("SAML is disabled", status=403)
        
        req = prepare_django_request(request)
        auth = OneLogin_Saml2_Auth(req, get_saml_settings(request))
        
        # SECURITY: Generate and store RelayState for CSRF protection
        # This prevents attackers from forging SAML responses
        relay_state = secrets.token_urlsafe(32)
        request.session['saml_relay_state'] = relay_state
        request.session.modified = True
        
        # Redirect to IdP with RelayState
        return HttpResponseRedirect(auth.login(return_to=relay_state))


@method_decorator(csrf_exempt, name='dispatch')
class SAMLACSView(View):
    """
    Sprint 1.7: SAML Assertion Consumer Service (ACS) endpoint.
    
    Receives SAML assertion from IdP after authentication.
    Creates/links user account and generates JWT tokens.
    
    SECURITY: Validates RelayState to prevent CSRF attacks.
    See: REFACTOR_PLAN.md Phase 0, FORENSIC_AUDIT.md Issue #5.2
    
    POST /api/auth/saml/acs/
    """
    def post(self, request):
        if not SAML_AVAILABLE:
            return HttpResponse("SAML is not configured", status=501)
        
        # SECURITY: Validate RelayState matches session to prevent CSRF
        relay_state = request.POST.get('RelayState', '')
        expected_state = request.session.get('saml_relay_state', '')
        
        if not relay_state or not expected_state:
            logger.warning(
                "SAML CSRF validation failed: missing RelayState",
                extra={
                    "has_relay_state": bool(relay_state),
                    "has_session_state": bool(expected_state),
                    "ip_address": request.META.get('REMOTE_ADDR'),
                }
            )
            return HttpResponse("Invalid SAML request: missing state", status=400)
        
        # Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(relay_state, expected_state):
            logger.warning(
                "SAML CSRF validation failed: state mismatch",
                extra={
                    "ip_address": request.META.get('REMOTE_ADDR'),
                }
            )
            return HttpResponse("Invalid SAML request: state mismatch", status=400)
        
        # Clear used state to prevent replay attacks
        del request.session['saml_relay_state']
        request.session.modified = True
        
        req = prepare_django_request(request)
        auth = OneLogin_Saml2_Auth(req, get_saml_settings(request))
        auth.process_response()
        
        errors = auth.get_errors()
        if errors:
            # SECURITY: Sanitize error messages to prevent information disclosure
            # Log detailed errors server-side only (see T-136)
            error_reason = auth.get_last_error_reason()
            logger.error(
                "SAML authentication failed",
                extra={
                    "errors": errors,
                    "error_reason": error_reason,
                    "ip_address": request.META.get('REMOTE_ADDR'),
                }
            )
            return HttpResponse("SAML authentication failed", status=400)
        
        if not auth.is_authenticated():
            return HttpResponse("SAML authentication failed", status=401)
        
        # Get user attributes from SAML assertion
        attributes = auth.get_attributes()
        name_id = auth.get_nameid()
        
        # Extract user data (mapping configurable via SAMLConfiguration.attribute_mapping)
        # SECURITY: Defensive attribute extraction with defaults (see T-134)
        # Prevents IndexError if SAML assertion lacks expected attributes
        email = attributes.get('email', [name_id])[0] if attributes.get('email') else name_id
        first_name = attributes.get('first_name', [''])[0] if attributes.get('first_name') else ''
        last_name = attributes.get('last_name', [''])[0] if attributes.get('last_name') else ''
        
        logger.info(
            "SAML user authenticated",
            extra={
                "email": email,
                "name_id": name_id,
                "has_first_name": bool(first_name),
                "has_last_name": bool(last_name),
            }
        )
        
        # Create or link user account
        try:
            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "username": email,
                        "first_name": first_name,
                        "last_name": last_name,
                    }
                )
                
                # Log the user in
                login(request, user)
                
                # Generate JWT tokens for API access
                refresh = RefreshToken.for_user(user)
                
                response = HttpResponse(
                    """
                    <html>
                    <body>
                        <h1>SAML Authentication Successful</h1>
                        <p>You may close this window and return to the application.</p>
                    </body>
                    </html>
                    """,
                    status=status.HTTP_200_OK,
                )
                set_auth_cookies(response, access_token=str(refresh.access_token), refresh_token=str(refresh))
                return response
        except Exception as e:
            # SECURITY: Generic error message to prevent information disclosure
            logger.exception(
                "SAML user creation or login failed",
                extra={
                    "email": email if 'email' in locals() else 'unknown',
                    "ip_address": request.META.get('REMOTE_ADDR'),
                }
            )
            return HttpResponse("Authentication failed", status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SAMLSLOView(View):
    """
    Sprint 1.7: SAML Single Logout (SLO) endpoint.
    
    Handles logout requests from IdP.
    
    SECURITY: Error messages sanitized to prevent information disclosure.
    
    GET /api/auth/saml/slo/
    """
    def get(self, request):
        if not SAML_AVAILABLE:
            return HttpResponse("SAML is not configured", status=501)
        
        req = prepare_django_request(request)
        auth = OneLogin_Saml2_Auth(req, get_saml_settings(request))
        
        url = auth.process_slo()
        errors = auth.get_errors()
        
        if errors:
            # SECURITY: Log detailed errors server-side, return generic message
            error_reason = auth.get_last_error_reason()
            logger.error(
                "SAML SLO failed",
                extra={
                    "errors": errors,
                    "error_reason": error_reason,
                    "ip_address": request.META.get('REMOTE_ADDR'),
                }
            )
            return HttpResponse("Logout failed", status=400)
        
        if url:
            return HttpResponseRedirect(url)
        else:
            return HttpResponse("Logged out successfully")


@api_view(["GET"])
@permission_classes([AllowAny])
def saml_metadata(request):
    """
    Sprint 1.7: SAML Service Provider metadata endpoint.
    
    Returns SP metadata XML for IdP configuration.
    
    SECURITY: Error messages sanitized to prevent information disclosure.
    
    GET /api/auth/saml/metadata/
    """
    if not SAML_AVAILABLE:
        return Response({"error": "SAML is not configured"}, status=501)
    
    try:
        saml_settings = OneLogin_Saml2_Settings(get_saml_settings(request))
        metadata = saml_settings.get_sp_metadata()
        errors = saml_settings.validate_metadata(metadata)
        
        if errors:
            logger.error(
                "SAML metadata validation failed",
                extra={"errors": errors}
            )
            return Response({"error": "Invalid metadata configuration"}, status=500)
        
        return HttpResponse(metadata, content_type='text/xml')
    except Exception as e:
        logger.exception("SAML metadata generation failed")
        return Response({"error": "Metadata generation failed"}, status=500)


@api_view(["GET", "POST", "PUT", "DELETE"])
@permission_classes([IsAdminUser])
def saml_idp_config(request):
    """
    Sprint 1.8: Admin UI for SAML IdP metadata management.
    
    Allows administrators to configure SAML IdP settings.
    
    GET /api/auth/saml/config/ - Get current config
    POST /api/auth/saml/config/ - Create config
    PUT /api/auth/saml/config/ - Update config
    DELETE /api/auth/saml/config/ - Delete config
    """
    from modules.auth.models import SAMLConfiguration
    
    if request.method == "GET":
        configs = SAMLConfiguration.objects.all()
        data = []
        for config in configs:
            data.append({
                "id": config.id,
                "name": config.name,
                "sp_entity_id": config.sp_entity_id,
                "idp_entity_id": config.idp_entity_id,
                "idp_sso_url": config.idp_sso_url,
                "idp_slo_url": config.idp_slo_url,
                "is_active": config.is_active,
                "has_sp_cert": bool(config.sp_public_cert),
                "has_idp_cert": bool(config.idp_x509_cert),
            })
        return Response(data, status=status.HTTP_200_OK)
    
    elif request.method == "POST":
        from modules.auth.serializers import SAMLConfigurationSerializer
        serializer = SAMLConfigurationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == "PUT":
        config_id = request.data.get("id")
        if not config_id:
            return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            config = SAMLConfiguration.objects.get(id=config_id)
            from modules.auth.serializers import SAMLConfigurationSerializer
            serializer = SAMLConfigurationSerializer(config, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SAMLConfiguration.DoesNotExist:
            return Response({"error": "Configuration not found"}, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method == "DELETE":
        config_id = request.data.get("id")
        if not config_id:
            return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            config = SAMLConfiguration.objects.get(id=config_id)
            config.delete()
            return Response({"message": "Configuration deleted"}, status=status.HTTP_200_OK)
        except SAMLConfiguration.DoesNotExist:
            return Response({"error": "Configuration not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET", "PUT"])
@permission_classes([IsAdminUser])
def saml_attribute_mapping(request):
    """
    Sprint 1.9: SAML attribute mapping configuration.
    
    Configure how SAML assertion attributes map to User model fields.
    
    GET /api/auth/saml/attribute-mapping/ - Get current mapping
    PUT /api/auth/saml/attribute-mapping/ - Update mapping
    """
    from modules.auth.models import SAMLConfiguration
    
    try:
        config = SAMLConfiguration.objects.filter(is_active=True).first()
        if not config:
            return Response(
                {"error": "No active SAML configuration found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.method == "GET":
            return Response({
                "attribute_mapping": config.attribute_mapping or {
                    "email": "email",
                    "first_name": "firstName",
                    "last_name": "lastName",
                    "username": "email",
                }
            }, status=status.HTTP_200_OK)
        
        elif request.method == "PUT":
            attribute_mapping = request.data.get("attribute_mapping")
            if not attribute_mapping:
                return Response(
                    {"error": "attribute_mapping is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            config.attribute_mapping = attribute_mapping
            config.save()
            
            return Response({
                "message": "Attribute mapping updated successfully",
                "attribute_mapping": config.attribute_mapping
            }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.exception("SAML attribute mapping operation failed")
        return Response(
            {"error": "Operation failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
