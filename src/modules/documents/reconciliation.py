"""
S3 Reconciliation Service (ASSESS-G18.5b).

Verifies document Version records match S3 objects; detects missing files.
"""

import logging
from typing import List, Dict, Any

from django.utils import timezone

from modules.documents.models import Document, Version
from modules.documents.services import S3Service
from modules.firm.audit import AuditEvent
from modules.firm.models import Firm

logger = logging.getLogger(__name__)


class S3ReconciliationService:
    """
    Service for reconciling Document Version records with S3 objects.

    ASSESS-G18.5b: Verify document Version records match S3 objects; detect missing files.
    """

    def __init__(self, firm: Firm = None):
        """
        Initialize reconciliation service.

        Args:
            firm: Optional firm to reconcile (if None, reconciles all firms)
        """
        self.firm = firm
        self.s3_service = S3Service()
        self.mismatches = []

    def reconcile_all_firms(self) -> Dict[str, Any]:
        """
        Reconcile document versions for all active firms.

        Returns:
            Dict with reconciliation summary
        """
        firms = Firm.objects.filter(status__in=["active", "trial"])
        if self.firm:
            firms = firms.filter(id=self.firm.id)

        total_versions = 0
        total_mismatches = 0
        firm_results = []

        for firm in firms:
            result = self.reconcile_firm(firm)
            total_versions += result["total_versions"]
            total_mismatches += result["mismatches_count"]
            firm_results.append(result)

        return {
            "reconciliation_date": timezone.now().isoformat(),
            "firms_processed": len(firm_results),
            "total_versions": total_versions,
            "total_mismatches": total_mismatches,
            "firm_results": firm_results,
        }

    def reconcile_firm(self, firm: Firm) -> Dict[str, Any]:
        """
        Reconcile document versions for a specific firm.

        Args:
            firm: Firm to reconcile

        Returns:
            Dict with reconciliation results
        """
        logger.info(f"Starting S3 reconciliation for firm {firm.id} ({firm.name})")

        # Get all document versions with S3 keys
        versions = Version.objects.filter(
            document__firm=firm,
        ).exclude(
            s3_key=""
        ).exclude(
            s3_key__isnull=True
        ).select_related("document")

        mismatches = []
        reconciled = 0
        errors = []

        for version in versions:
            try:
                mismatch = self._reconcile_version(version)
                if mismatch:
                    mismatches.append(mismatch)
                else:
                    reconciled += 1
            except Exception as e:
                logger.error(f"Error reconciling version {version.id}: {str(e)}")
                errors.append({
                    "version_id": version.id,
                    "document_id": version.document_id,
                    "s3_key": version.s3_key,
                    "error": str(e),
                })

        # Create audit event for reconciliation run
        AuditEvent.objects.create(
            firm=firm,
            category=AuditEvent.CATEGORY_SYSTEM,
            action="s3_reconciliation_run",
            severity=AuditEvent.SEVERITY_INFO,
            resource_type="Version",
            metadata={
                "total_versions": versions.count(),
                "reconciled": reconciled,
                "mismatches": len(mismatches),
                "errors": len(errors),
            },
        )

        return {
            "firm_id": firm.id,
            "firm_name": firm.name,
            "total_versions": versions.count(),
            "reconciled": reconciled,
            "mismatches_count": len(mismatches),
            "mismatches": mismatches,
            "errors": errors,
        }

    def _reconcile_version(self, version: Version) -> Dict[str, Any] | None:
        """
        Reconcile a single version with S3.

        Args:
            version: Version to reconcile

        Returns:
            Mismatch dict if found, None otherwise
        """
        # Check if S3 object exists
        try:
            s3_exists = self.s3_service.object_exists(
                bucket=version.document.s3_bucket,
                key=version.s3_key,
            )
        except Exception as e:
            # S3 error - treat as mismatch
            AuditEvent.objects.create(
                firm=version.document.firm,
                category=AuditEvent.CATEGORY_SYSTEM,
                action="s3_reconciliation_error",
                severity=AuditEvent.SEVERITY_WARNING,
                resource_type="Version",
                resource_id=str(version.id),
                metadata={
                    "version_id": version.id,
                    "document_id": version.document_id,
                    "s3_key": version.s3_key,
                    "s3_bucket": version.document.s3_bucket,
                    "error": str(e),
                },
            )
            return {
                "version_id": version.id,
                "document_id": version.document_id,
                "document_name": version.document.name,
                "s3_key": version.s3_key,
                "s3_bucket": version.document.s3_bucket,
                "mismatch_type": "s3_error",
                "error": str(e),
            }

        if not s3_exists:
            # Missing file in S3
            AuditEvent.objects.create(
                firm=version.document.firm,
                category=AuditEvent.CATEGORY_SYSTEM,
                action="s3_reconciliation_mismatch",
                severity=AuditEvent.SEVERITY_WARNING,
                resource_type="Version",
                resource_id=str(version.id),
                metadata={
                    "version_id": version.id,
                    "document_id": version.document_id,
                    "s3_key": version.s3_key,
                    "s3_bucket": version.document.s3_bucket,
                    "mismatch_type": "missing_file",
                },
            )

            return {
                "version_id": version.id,
                "document_id": version.document_id,
                "document_name": version.document.name,
                "s3_key": version.s3_key,
                "s3_bucket": version.document.s3_bucket,
                "mismatch_type": "missing_file",
            }

        # Verify file size matches (if available)
        try:
            s3_metadata = self.s3_service.get_object_metadata(
                bucket=version.document.s3_bucket,
                key=version.s3_key,
            )
            s3_size = s3_metadata.get("ContentLength")

            if version.file_size_bytes and s3_size:
                if version.file_size_bytes != s3_size:
                    # Size mismatch
                    AuditEvent.objects.create(
                        firm=version.document.firm,
                        category=AuditEvent.CATEGORY_SYSTEM,
                        action="s3_reconciliation_mismatch",
                        severity=AuditEvent.SEVERITY_WARNING,
                        resource_type="Version",
                        resource_id=str(version.id),
                        metadata={
                            "version_id": version.id,
                            "document_id": version.document_id,
                            "s3_key": version.s3_key,
                            "local_size": version.file_size_bytes,
                            "s3_size": s3_size,
                            "mismatch_type": "size_mismatch",
                        },
                    )

                    return {
                        "version_id": version.id,
                        "document_id": version.document_id,
                        "document_name": version.document.name,
                        "s3_key": version.s3_key,
                        "mismatch_type": "size_mismatch",
                        "local_size": version.file_size_bytes,
                        "s3_size": s3_size,
                    }
        except Exception as e:
            # Metadata fetch error - log but don't fail reconciliation
            logger.warning(f"Could not verify size for version {version.id}: {str(e)}")

        # No mismatches found
        return None
