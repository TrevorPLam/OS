"""
Authentication URL routes.
"""

from django.urls import path

from .views import (
    ChangePasswordView,
    CookieTokenRefreshView,
    RegisterView,
    login_view,
    logout_view,
    provision_firm_view,
    user_profile_view,
)
from .oauth_views import oauth_callback, oauth_provider_config, oauth_state
from .saml_views import (
    SAMLLoginView,
    SAMLACSView,
    SAMLSLOView,
    saml_metadata,
    saml_idp_config,
    saml_attribute_mapping,
)
from .mfa_views import (
    mfa_enroll_totp,
    mfa_verify_totp,
    mfa_disable_totp,
    mfa_enroll_sms,
    mfa_verify_sms,
    mfa_request_sms_login,
    mfa_disable_sms,
    mfa_status,
)

urlpatterns = [
    # User authentication
    path("register/", RegisterView.as_view(), name="auth_register"),
    path("provision-firm/", provision_firm_view, name="auth_provision_firm"),
    path("login/", login_view, name="auth_login"),
    path("logout/", logout_view, name="auth_logout"),
    path("profile/", user_profile_view, name="auth_profile"),
    path("change-password/", ChangePasswordView.as_view(), name="auth_change_password"),
    # JWT token refresh
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    
    # Sprint 1.2-1.5: OAuth Authentication
    path("oauth/state/", oauth_state, name="oauth_state"),
    path("oauth/callback/", oauth_callback, name="oauth_callback"),
    path("oauth/config/", oauth_provider_config, name="oauth_provider_config"),
    
    # Sprint 1.6-1.9: SAML Authentication
    path("saml/login/", SAMLLoginView.as_view(), name="saml_login"),
    path("saml/acs/", SAMLACSView.as_view(), name="saml_acs"),
    path("saml/slo/", SAMLSLOView.as_view(), name="saml_slo"),
    path("saml/metadata/", saml_metadata, name="saml_metadata"),
    path("saml/config/", saml_idp_config, name="saml_idp_config"),
    path("saml/attribute-mapping/", saml_attribute_mapping, name="saml_attribute_mapping"),
    
    # Sprint 1.10-1.13: MFA Authentication
    path("mfa/enroll/totp/", mfa_enroll_totp, name="mfa_enroll_totp"),
    path("mfa/verify/totp/", mfa_verify_totp, name="mfa_verify_totp"),
    path("mfa/disable/totp/", mfa_disable_totp, name="mfa_disable_totp"),
    path("mfa/enroll/sms/", mfa_enroll_sms, name="mfa_enroll_sms"),
    path("mfa/verify/sms/", mfa_verify_sms, name="mfa_verify_sms"),
    path("mfa/request/sms/", mfa_request_sms_login, name="mfa_request_sms"),
    path("mfa/disable/sms/", mfa_disable_sms, name="mfa_disable_sms"),
    path("mfa/status/", mfa_status, name="mfa_status"),
]
