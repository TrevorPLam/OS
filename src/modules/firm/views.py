"""
Firm Module API Views.

Provides endpoints for firm-level operations and break-glass session management.
"""

import logging

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from modules.firm.audit import audit
from modules.firm.export import (
    DEFAULT_PURGE_GRACE_DAYS,
    DEFAULT_RETENTION_DAYS,
    export_firm_data,
)
from modules.firm.models import FirmOffboardingRecord
from modules.firm.permissions import IsFirmOwnerOrAdmin
from modules.firm.utils import get_active_break_glass_session, get_firm_or_403

logger = logging.getLogger(__name__)


class BreakGlassStatusViewSet(viewsets.ViewSet):
    """
    API endpoint for checking break-glass impersonation status.

    This provides a dedicated endpoint for frontend UI components to:
    1. Check if the current request is in break-glass mode
    2. Get impersonation session details for displaying banners
    3. Monitor session expiration

    TIER 0.6: Impersonation mode indicator requirement.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="status")
    def get_status(self, request):
        """
        Get current break-glass impersonation status.

        Returns:
            {
                "is_impersonating": bool,
                "session": {
                    "id": int,
                    "impersonated_user": str,
                    "operator": str,
                    "reason": str,
                    "activated_at": str,
                    "expires_at": str,
                    "time_remaining_seconds": int
                } | null
            }
        """
        # Check if user is a platform operator
        if not hasattr(request.user, "platform_profile"):
            return Response({"is_impersonating": False, "session": None})

        # Check if user has an active break-glass session
        if not hasattr(request, "firm") or request.firm is None:
            return Response({"is_impersonating": False, "session": None})

        session = get_active_break_glass_session(request.firm)

        if not session or session.operator_id != request.user.id:
            return Response({"is_impersonating": False, "session": None})

        # Calculate time remaining
        now = timezone.now()
        time_remaining = (session.expires_at - now).total_seconds()

        impersonated_user = session.impersonated_user
        session_data = {
            "id": session.id,
            "impersonated_user": (
                impersonated_user.get_full_name() or impersonated_user.email or impersonated_user.username
                if impersonated_user
                else None
            ),
            "operator": request.user.email,
            "reason": session.reason,
            "activated_at": session.activated_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "time_remaining_seconds": max(0, int(time_remaining)),
        }

        return Response({"is_impersonating": True, "session": session_data})

    @action(detail=False, methods=["post"], url_path="end-session")
    def end_session(self, request):
        """
        End the current break-glass session early.

        Requires:
            reason: str - Reason for ending the session

        Returns:
            {"success": true, "message": str}
        """
        reason = request.data.get("reason", "")
        if not reason:
            return Response(
                {"error": "Reason is required to end break-glass session"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check for active session
        if not hasattr(request, "firm") or request.firm is None:
            return Response({"error": "No firm context found"}, status=status.HTTP_400_BAD_REQUEST)

        session = get_active_break_glass_session(request.firm)

        if not session or session.operator_id != request.user.id:
            return Response({"error": "No active break-glass session found"}, status=status.HTTP_404_NOT_FOUND)

        # Revoke the session
        session.revoke(reason)
        session.save()

        return Response({"success": True, "message": "Break-glass session ended successfully"})


class FirmOffboardingViewSet(viewsets.ViewSet):
    """Endpoints for firm offboarding exports and purge sequencing."""

    permission_classes = [IsAuthenticated, IsFirmOwnerOrAdmin]

    @action(detail=False, methods=["post"], url_path="export")
    def export(self, request):
        firm = get_firm_or_403(request)
        retention_days = int(request.data.get("retention_days", DEFAULT_RETENTION_DAYS))
        purge_grace_days = int(request.data.get("purge_grace_days", DEFAULT_PURGE_GRACE_DAYS))

        record = FirmOffboardingRecord.objects.create(
            firm=firm,
            requested_by=request.user,
            retention_days=retention_days,
            purge_grace_days=purge_grace_days,
            status=FirmOffboardingRecord.STATUS_EXPORTING,
        )

        payload = export_firm_data(
            firm=firm,
            requested_by=request.user,
            retention_days=retention_days,
            purge_grace_days=purge_grace_days,
        )

        retention = payload["retention"]
        record.export_completed_at = payload["generated_at"]
        record.retention_expires_at = retention["retention_expires_at"]
        record.purge_scheduled_at = retention["purge_scheduled_at"]
        record.export_manifest = payload["manifest"]
        record.integrity_report = payload["integrity"]
        record.export_checksum = payload["checksum"]
        record.status = (
            FirmOffboardingRecord.STATUS_EXPORTED
            if payload["integrity"]["status"] == "ok"
            else FirmOffboardingRecord.STATUS_FAILED
        )
        record.save()

        return Response(
            {
                "record_id": record.id,
                "status": record.status,
                "export": payload,
            }
        )

    @action(detail=False, methods=["get"], url_path="status")
    def status(self, request):
        firm = get_firm_or_403(request)
        record = FirmOffboardingRecord.objects.filter(firm=firm).first()
        if not record:
            return Response({"status": "no_exports"})
        return Response(
            {
                "record_id": record.id,
                "status": record.status,
                "export_started_at": record.export_started_at,
                "export_completed_at": record.export_completed_at,
                "retention_expires_at": record.retention_expires_at,
                "purge_scheduled_at": record.purge_scheduled_at,
                "purge_completed_at": record.purge_completed_at,
                "export_manifest": record.export_manifest,
                "integrity_report": record.integrity_report,
                "export_checksum": record.export_checksum,
            }
        )

    @action(detail=False, methods=["post"], url_path="purge")
    def purge(self, request):
        firm = get_firm_or_403(request)
        record_id = request.data.get("record_id")
        reason = request.data.get("reason", "").strip()

        if not reason:
            return Response(
                {"error": "Reason is required to purge firm data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record = FirmOffboardingRecord.objects.filter(firm=firm)
        if record_id:
            record = record.filter(id=record_id)
        record = record.first()

        if not record:
            return Response(
                {"error": "No offboarding record found for this firm"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if record.status not in [
            FirmOffboardingRecord.STATUS_EXPORTED,
            FirmOffboardingRecord.STATUS_PURGE_PENDING,
        ]:
            return Response(
                {"error": "Offboarding record is not ready for purge"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if record.retention_expires_at and timezone.now() < record.retention_expires_at:
            return Response(
                {
                    "error": "Retention window has not expired",
                    "retention_expires_at": record.retention_expires_at,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        record.status = FirmOffboardingRecord.STATUS_PURGED
        record.purge_completed_at = timezone.now()
        record.save()

        firm.status = "canceled"
        firm.save(update_fields=["status"])

        try:
            audit.log_purge_event(
                firm=firm,
                action="firm_offboarding_purge",
                actor=request.user,
                target_model="firm.Firm",
                target_id=str(firm.id),
                reason=reason,
                metadata={"offboarding_record_id": record.id},
            )
        except Exception as e:
            logger.warning(f"Failed to log export completion: {e}")

        return Response(
            {
                "status": "purged",
                "record_id": record.id,
                "purge_completed_at": record.purge_completed_at,
            }
        )
