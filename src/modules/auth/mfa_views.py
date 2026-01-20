"""
Sprint 1.10-1.13: Multi-Factor Authentication (MFA)

Implements TOTP (Time-based OTP) and SMS-based OTP for two-factor authentication.
Integrates with existing SMS module for SMS delivery.
"""

import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django_otp import match_token
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.util import random_hex
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

import qrcode

import qrcode.image.svg
from io import BytesIO
import base64

User = get_user_model()


def get_or_create_mfa_profile(user):
    """Get or create MFA profile for user."""
    from modules.auth.models import UserMFAProfile
    profile, created = UserMFAProfile.objects.get_or_create(user=user)
    return profile



def generate_sms_otp():
    """Generate a random 6-digit OTP for SMS."""
    return ''.join(secrets.choice(string.digits) for _ in range(settings.SMS_OTP_LENGTH))


def send_sms_otp(user, otp_code):
    """
    Send OTP via SMS using existing Twilio integration.
    
    Leverages src/modules/sms/ infrastructure.
    """
    try:
        from modules.sms.models import SMSMessage
        from modules.sms.services import send_sms
        
        # SECURITY: Resolve phone number from MFA profile first, then fallback to user field.
        # This avoids silent OTP delivery failures when the number lives on UserMFAProfile.
        mfa_profile = getattr(user, "mfa_profile", None)
        phone_number = getattr(mfa_profile, "phone_number", None) or getattr(user, "phone_number", None)
        if not phone_number:
            return False, "No phone number configured for user"
        
        # Send SMS
        message = f"Your ConsultantPro verification code is: {otp_code}. Valid for {settings.SMS_OTP_VALIDITY_MINUTES} minutes."
        
        # Use existing SMS service
        success = send_sms(
            to_number=phone_number,
            message=message,
            firm=None,  # System message
        )
        
        return success, "OTP sent successfully" if success else "Failed to send SMS"
    
    except Exception as e:
        return False, f"SMS sending failed: {str(e)}"


# SECURITY: Rate limit enrollment to slow brute-force attempts (5/minute per IP).
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def mfa_enroll_totp(request):
    """
    Sprint 1.11: Enroll in TOTP (Time-based OTP) authentication.
    
    Generates QR code for authenticator app (Google Authenticator, Authy, etc.)
    
    POST /api/auth/mfa/enroll/totp/
    """
    user = request.user
    
    # Check if user already has TOTP device
    existing_device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
    if existing_device:
        return Response({
            "error": "TOTP already enrolled. Disable existing device first."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create new TOTP device
    device = TOTPDevice.objects.create(
        user=user,
        name=f"TOTP-{user.username}",
        confirmed=False,
    )
    
    # Generate QR code
    url = device.config_url
    
    # Create QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return Response({
        "device_id": device.id,
        "secret": device.key,
        "qr_code": f"data:image/png;base64,{qr_code_base64}",
        "config_url": url,
        "message": "Scan QR code with authenticator app and verify with a code"
    }, status=status.HTTP_201_CREATED)


# SECURITY: Rate limit verification to slow brute-force attempts (5/minute per IP).
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def mfa_verify_totp(request):
    """
    Sprint 1.11: Verify TOTP code to complete enrollment or during login.
    
    POST /api/auth/mfa/verify/totp/
    {
        "device_id": 123,
        "code": "123456"
    }
    """
    user = request.user
    device_id = request.data.get("device_id")
    code = request.data.get("code")
    
    if not code:
        return Response({"error": "code is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        if device_id:
            # Verifying during enrollment
            device = TOTPDevice.objects.get(id=device_id, user=user, confirmed=False)
        else:
            # Verifying during login
            device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
            if not device:
                return Response({
                    "error": "No TOTP device enrolled"
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify code
        if device.verify_token(code):
            if not device.confirmed:
                device.confirmed = True
                device.save()
                return Response({
                    "message": "TOTP enrollment successful"
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "TOTP verification successful"
                }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": "Invalid code"
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except TOTPDevice.DoesNotExist:
        return Response({
            "error": "Device not found"
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def mfa_disable_totp(request):
    """
    Sprint 1.11: Disable TOTP authentication.
    
    DELETE /api/auth/mfa/disable/totp/
    {
        "code": "123456"
    }
    """
    user = request.user
    code = request.data.get("code")
    
    if not code:
        return Response({"error": "code required for verification"}, status=status.HTTP_400_BAD_REQUEST)
    
    device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
    if not device:
        return Response({
            "error": "No TOTP device enrolled"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verify code before disabling
    if device.verify_token(code):
        device.delete()
        return Response({
            "message": "TOTP disabled successfully"
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "error": "Invalid code"
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="3/h", method="POST", block=True)
def mfa_enroll_sms(request):
    """
    Sprint 1.12: Enroll in SMS-based OTP authentication.
    
    Sends verification code to user's phone number.
    Leverages existing SMS infrastructure (see src/modules/sms/).
    
    POST /api/auth/mfa/enroll/sms/
    {
        "phone_number": "+1234567890"
    }
    """
    user = request.user
    phone_number = request.data.get("phone_number")
    
    if not phone_number:
        return Response({"error": "phone_number is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Save phone number to MFA profile for SMS delivery
    profile = get_or_create_mfa_profile(user)
    profile.phone_number = phone_number
    profile.save(update_fields=["phone_number"])
    
    # Generate OTP
    otp_code = generate_sms_otp()
    
    # Store OTP in cache with expiry
    cache_key = f"sms_otp_enroll_{user.id}"
    cache.set(cache_key, otp_code, timeout=settings.SMS_OTP_VALIDITY_MINUTES * 60)
    
    # Send SMS
    success, message = send_sms_otp(user, otp_code)
    
    if success:
        return Response({
            "message": "Verification code sent to your phone",
            "expires_in_minutes": settings.SMS_OTP_VALIDITY_MINUTES
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "error": message
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="5/h", method="POST", block=True)
def mfa_verify_sms(request):
    """
    Sprint 1.12: Verify SMS OTP code.
    
    POST /api/auth/mfa/verify/sms/
    {
        "code": "123456"
    }
    """
    user = request.user
    code = request.data.get("code")
    
    if not code:
        return Response({"error": "code is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check enrollment OTP
    cache_key_enroll = f"sms_otp_enroll_{user.id}"
    stored_code_enroll = cache.get(cache_key_enroll)
    
    # Check login OTP
    cache_key_login = f"sms_otp_login_{user.id}"
    stored_code_login = cache.get(cache_key_login)
    
    # SECURITY: Use constant-time comparison to prevent timing attacks
    # See: FORENSIC_AUDIT.md Issue #5.3
    import hmac
    
    if stored_code_enroll and hmac.compare_digest(str(code), str(stored_code_enroll)):
        # Enrollment verification successful
        cache.delete(cache_key_enroll)
        
        # Mark SMS MFA as enabled for user
        get_or_create_mfa_profile(user).sms_mfa_enabled = True
        user.save()
        
        return Response({
            "message": "SMS MFA enrollment successful"
        }, status=status.HTTP_200_OK)
    
    elif stored_code_login and hmac.compare_digest(str(code), str(stored_code_login)):
        # Login verification successful
        cache.delete(cache_key_login)
        return Response({
            "message": "SMS verification successful"
        }, status=status.HTTP_200_OK)
    
    else:
        return Response({
            "error": "Invalid or expired code"
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="5/h", method="POST", block=True)
def mfa_request_sms_login(request):
    """
    Sprint 1.12: Request SMS OTP for login (after password authentication).
    
    POST /api/auth/mfa/request/sms/
    {
        "username": "user@example.com"
    }
    """
    username = request.data.get("username")
    
    if not username:
        return Response({"error": "username is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(username=username)
        
        if not getattr(user, 'sms_mfa_enabled', False):
            return Response({
                "error": "SMS MFA not enabled for this user"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate OTP
        otp_code = generate_sms_otp()
        
        # Store OTP in cache
        cache_key = f"sms_otp_login_{user.id}"
        cache.set(cache_key, otp_code, timeout=settings.SMS_OTP_VALIDITY_MINUTES * 60)
        
        # Send SMS
        success, message = send_sms_otp(user, otp_code)
        
        if success:
            return Response({
                "message": "Verification code sent",
                "expires_in_minutes": settings.SMS_OTP_VALIDITY_MINUTES
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except User.DoesNotExist:
        # Don't reveal if user exists
        return Response({
            "message": "If the user exists and has SMS MFA enabled, a code has been sent"
        }, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def mfa_disable_sms(request):
    """
    Sprint 1.12: Disable SMS-based MFA.
    
    DELETE /api/auth/mfa/disable/sms/
    """
    user = request.user
    get_or_create_mfa_profile(user).sms_mfa_enabled = False
    user.save()
    
    return Response({
        "message": "SMS MFA disabled successfully"
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mfa_status(request):
    """
    Sprint 1.13: Get MFA enrollment status for current user.
    
    GET /api/auth/mfa/status/
    """
    user = request.user
    
    totp_enrolled = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
    sms_enrolled = getattr(user, 'sms_mfa_enabled', False)
    
    return Response({
        "totp_enabled": totp_enrolled,
        "sms_enabled": sms_enrolled,
        "any_mfa_enabled": totp_enrolled or sms_enrolled
    }, status=status.HTTP_200_OK)
