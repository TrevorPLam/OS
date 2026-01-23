"""
Contact Enrichment Background Tasks.

Provides scheduled tasks for:
- Re-enrichment of stale contact data
- Quality metric calculation
- Provider performance monitoring

These tasks are designed to be called by management commands or cron jobs.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from django.db.models import Count, Q
from django.utils import timezone

from modules.crm.enrichment_service import EnrichmentOrchestrator
from modules.crm.models import (
    ContactEnrichment,
    EnrichmentProvider,
    EnrichmentQualityMetric,
)
from modules.firm.models import Firm

logger = logging.getLogger(__name__)


def refresh_stale_enrichments(firm_id: int = None, batch_size: int = 100) -> Dict:
    """
    Refresh stale contact enrichments for a specific firm or all firms.

    Args:
        firm_id: Optional firm ID to limit refresh to single firm
        batch_size: Maximum number of enrichments to refresh per run

    Returns:
        Dict with refresh statistics
    """
    logger.info(f"Starting stale enrichment refresh (batch_size={batch_size})")

    # Build queryset for stale enrichments
    queryset = ContactEnrichment.objects.filter(
        Q(is_stale=True) | Q(next_refresh_at__lte=timezone.now())
    ).select_related(
        "enrichment_provider",
        "enrichment_provider__firm",
        "account_contact",
        "client_contact",
    )

    if firm_id:
        # Filter by firm through provider relationship
        queryset = queryset.filter(enrichment_provider__firm_id=firm_id)

    # Limit batch size
    enrichments_to_refresh = queryset[:batch_size]
    total_count = len(enrichments_to_refresh)

    if total_count == 0:
        logger.info("No stale enrichments found")
        return {
            "success": True,
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

    logger.info(f"Found {total_count} stale enrichments to refresh")

    successful = 0
    failed = 0
    errors = []

    for enrichment in enrichments_to_refresh:
        try:
            # Get contact email
            email = enrichment.contact_email
            if not email:
                logger.warning(
                    f"Skipping enrichment {enrichment.id} - no email address"
                )
                failed += 1
                continue

            # Get firm from enrichment
            firm = enrichment.firm
            if not firm:
                logger.warning(
                    f"Skipping enrichment {enrichment.id} - no firm found"
                )
                failed += 1
                continue

            # Re-enrich using orchestrator
            orchestrator = EnrichmentOrchestrator(firm=firm)

            if enrichment.account_contact:
                result, enrich_errors = orchestrator.enrich_contact(
                    email=email,
                    contact=enrichment.account_contact,
                )
            elif enrichment.client_contact:
                result, enrich_errors = orchestrator.enrich_contact(
                    email=email,
                    client_contact=enrichment.client_contact,
                )
            else:
                logger.warning(
                    f"Skipping enrichment {enrichment.id} - no contact found"
                )
                failed += 1
                continue

            if result:
                successful += 1
                logger.info(
                    f"Successfully refreshed enrichment {enrichment.id} for {email}"
                )
            else:
                failed += 1
                error_msg = f"enrichment {enrichment.id}: {enrich_errors}"
                errors.append(error_msg)
                logger.warning(f"Failed to refresh {error_msg}")

        except Exception as e:
            failed += 1
            error_msg = f"enrichment {enrichment.id}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"Error refreshing enrichment {enrichment.id}: {e}", exc_info=True)

    result = {
        "success": failed == 0,
        "total_processed": total_count,
        "successful": successful,
        "failed": failed,
        "errors": errors[:10],  # Limit error list
    }

    logger.info(
        f"Refresh complete: {successful}/{total_count} successful, "
        f"{failed} failed"
    )

    return result


def refresh_enrichments_for_firm(firm_id: int, batch_size: int = 100) -> Dict:
    """
    Refresh stale enrichments for a specific firm.

    Args:
        firm_id: Firm ID
        batch_size: Maximum number of enrichments to refresh

    Returns:
        Dict with refresh statistics
    """
    try:
        firm = Firm.objects.get(id=firm_id)
        logger.info(f"Refreshing enrichments for firm: {firm.name}")

        return refresh_stale_enrichments(firm_id=firm_id, batch_size=batch_size)

    except Firm.DoesNotExist:
        logger.error(f"Firm {firm_id} not found")
        return {
            "success": False,
            "error": f"Firm {firm_id} not found",
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
        }
    except Exception as e:
        logger.error(f"Error refreshing enrichments for firm {firm_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
        }


def refresh_enrichments_for_all_firms(batch_size_per_firm: int = 50) -> Dict:
    """
    Refresh stale enrichments for all firms.

    Args:
        batch_size_per_firm: Maximum enrichments per firm per run

    Returns:
        Dict with overall statistics
    """
    logger.info("Starting enrichment refresh for all firms")

    firms = Firm.objects.filter(is_active=True)
    total_firms = firms.count()

    if total_firms == 0:
        logger.info("No active firms found")
        return {
            "success": True,
            "total_firms": 0,
            "results": [],
        }

    logger.info(f"Processing {total_firms} active firms")

    results = []
    for firm in firms:
        try:
            result = refresh_enrichments_for_firm(
                firm_id=firm.id,
                batch_size=batch_size_per_firm
            )
            results.append({
                "firm_id": firm.id,
                "firm_name": firm.name,
                **result,
            })
        except Exception as e:
            logger.error(f"Error processing firm {firm.id}: {e}", exc_info=True)
            results.append({
                "firm_id": firm.id,
                "firm_name": firm.name,
                "success": False,
                "error": str(e),
            })

    # Calculate overall stats
    total_successful = sum(r.get("successful", 0) for r in results)
    total_failed = sum(r.get("failed", 0) for r in results)
    failed_firms = sum(1 for r in results if not r.get("success", True))

    overall_result = {
        "success": failed_firms == 0,
        "total_firms": total_firms,
        "total_successful": total_successful,
        "total_failed": total_failed,
        "failed_firms": failed_firms,
        "results": results,
    }

    logger.info(
        f"Refresh complete for all firms: {total_successful} successful, "
        f"{total_failed} failed across {total_firms} firms"
    )

    return overall_result


def calculate_quality_metrics(firm_id: int = None) -> Dict:
    """
    Calculate and store quality metrics for enrichment providers.

    Aggregates enrichment statistics from the past 24 hours and stores
    them in EnrichmentQualityMetric for historical tracking.

    Args:
        firm_id: Optional firm ID to limit to single firm

    Returns:
        Dict with calculation statistics
    """
    logger.info("Starting quality metric calculation")

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    # Get all enabled providers
    providers = EnrichmentProvider.objects.filter(is_enabled=True)

    if firm_id:
        providers = providers.filter(firm_id=firm_id)

    total_providers = providers.count()

    if total_providers == 0:
        logger.info("No enabled providers found")
        return {
            "success": True,
            "total_providers": 0,
            "metrics_created": 0,
        }

    logger.info(f"Calculating metrics for {total_providers} providers")

    metrics_created = 0
    errors = []

    for provider in providers:
        try:
            # Get enrichments from the past 24 hours
            enrichments = ContactEnrichment.objects.filter(
                enrichment_provider=provider,
                last_enriched_at__date=today,
            )

            total_enrichments = enrichments.count()

            if total_enrichments == 0:
                logger.debug(f"No enrichments today for {provider}")
                continue

            # Calculate metrics
            successful_enrichments = enrichments.filter(
                enrichment_error=""
            ).count()
            failed_enrichments = total_enrichments - successful_enrichments

            # Calculate average completeness
            completeness_values = [
                e.data_completeness for e in enrichments
                if e.data_completeness > 0
            ]
            average_completeness = (
                sum(completeness_values) / len(completeness_values)
                if completeness_values else 0.0
            )

            # Calculate average confidence
            confidence_values = [
                e.confidence_score for e in enrichments
                if e.confidence_score > 0
            ]
            average_confidence = (
                sum(confidence_values) / len(confidence_values)
                if confidence_values else 0.0
            )

            # Calculate field-level success rates
            field_success_rates = {}
            all_fields_enriched = [e.fields_enriched for e in enrichments]
            all_fields_missing = [e.fields_missing for e in enrichments]

            # Aggregate field statistics
            for fields_list in all_fields_enriched:
                for field in fields_list:
                    if field not in field_success_rates:
                        field_success_rates[field] = {"success": 0, "total": 0}
                    field_success_rates[field]["success"] += 1
                    field_success_rates[field]["total"] += 1

            for fields_list in all_fields_missing:
                for field in fields_list:
                    if field not in field_success_rates:
                        field_success_rates[field] = {"success": 0, "total": 0}
                    field_success_rates[field]["total"] += 1

            # Calculate percentages
            for field, stats in field_success_rates.items():
                if stats["total"] > 0:
                    field_success_rates[field]["rate"] = (
                        stats["success"] / stats["total"] * 100
                    )

            # Count error types
            error_types = {}
            for enrichment in enrichments.filter(enrichment_error__isnull=False).exclude(enrichment_error=""):
                error = enrichment.enrichment_error
                error_types[error] = error_types.get(error, 0) + 1

            # Create or update metric
            metric, created = EnrichmentQualityMetric.objects.update_or_create(
                enrichment_provider=provider,
                metric_date=today,
                defaults={
                    "total_enrichments": total_enrichments,
                    "successful_enrichments": successful_enrichments,
                    "failed_enrichments": failed_enrichments,
                    "average_completeness": round(average_completeness, 2),
                    "average_confidence": round(average_confidence, 2),
                    "field_success_rates": field_success_rates,
                    "average_response_time_ms": 0,  # Would need actual timing data
                    "error_types": error_types,
                },
            )

            if created:
                metrics_created += 1
                logger.info(f"Created quality metric for {provider}")
            else:
                logger.info(f"Updated quality metric for {provider}")

        except Exception as e:
            error_msg = f"provider {provider.id}: {str(e)}"
            errors.append(error_msg)
            logger.error(
                f"Error calculating metrics for provider {provider.id}: {e}",
                exc_info=True
            )

    result = {
        "success": len(errors) == 0,
        "total_providers": total_providers,
        "metrics_created": metrics_created,
        "errors": errors,
    }

    logger.info(
        f"Quality metric calculation complete: {metrics_created} metrics created/updated"
    )

    return result


def mark_stale_enrichments(days_stale: int = 30) -> Dict:
    """
    Mark enrichments as stale if they haven't been refreshed recently.

    Args:
        days_stale: Number of days after which enrichment is considered stale

    Returns:
        Dict with statistics
    """
    logger.info(f"Marking enrichments stale after {days_stale} days")

    cutoff_date = timezone.now() - timedelta(days=days_stale)

    # Mark enrichments as stale
    stale_count = ContactEnrichment.objects.filter(
        last_enriched_at__lt=cutoff_date,
        is_stale=False,
    ).update(is_stale=True)

    logger.info(f"Marked {stale_count} enrichments as stale")

    return {
        "success": True,
        "stale_count": stale_count,
        "cutoff_date": cutoff_date.isoformat(),
    }


def cleanup_old_quality_metrics(days_to_keep: int = 90) -> Dict:
    """
    Delete quality metrics older than specified days.

    Args:
        days_to_keep: Number of days of metrics to retain

    Returns:
        Dict with cleanup statistics
    """
    logger.info(f"Cleaning up quality metrics older than {days_to_keep} days")

    cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)

    deleted_count, _ = EnrichmentQualityMetric.objects.filter(
        metric_date__lt=cutoff_date
    ).delete()

    logger.info(f"Deleted {deleted_count} old quality metrics")

    return {
        "success": True,
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat(),
    }


def get_enrichment_summary(firm_id: int = None) -> Dict:
    """
    Get summary statistics for enrichments.

    Args:
        firm_id: Optional firm ID to limit to single firm

    Returns:
        Dict with summary statistics
    """
    queryset = ContactEnrichment.objects.all()

    if firm_id:
        queryset = queryset.filter(
            Q(account_contact__account__firm_id=firm_id) |
            Q(client_contact__firm_id=firm_id)
        )

    total_enrichments = queryset.count()
    stale_enrichments = queryset.filter(is_stale=True).count()
    enrichments_needing_refresh = queryset.filter(
        next_refresh_at__lte=timezone.now()
    ).count()

    # Get provider breakdown
    provider_stats = queryset.values(
        "enrichment_provider__provider"
    ).annotate(
        count=Count("id")
    )

    return {
        "total_enrichments": total_enrichments,
        "stale_enrichments": stale_enrichments,
        "enrichments_needing_refresh": enrichments_needing_refresh,
        "provider_breakdown": list(provider_stats),
    }
