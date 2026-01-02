"""
Active Directory Synchronization Tasks

Background tasks for scheduled AD synchronization.
Part of AD-4: Add scheduled synchronization.
"""

import logging
from typing import Optional

from django.utils import timezone

from modules.ad_sync.models import ADSyncConfig
from modules.ad_sync.sync_service import ADSyncService
from modules.firm.models import Firm

logger = logging.getLogger(__name__)


def sync_ad_users_for_firm(firm_id: int, sync_type: str = 'delta') -> dict:
    """
    Synchronize users from Active Directory for a specific firm.
    
    AD-4: Scheduled synchronization task.
    
    Args:
        firm_id: ID of the firm to sync
        sync_type: Type of sync ('full', 'delta', or 'scheduled')
    
    Returns:
        Dict with sync results
    """
    try:
        firm = Firm.objects.get(id=firm_id)
        
        # Check if AD sync is configured and enabled
        try:
            config = firm.ad_sync_config
        except ADSyncConfig.DoesNotExist:
            logger.warning(f"No AD sync configuration found for firm {firm.name}")
            return {
                'success': False,
                'error': 'No AD sync configuration found'
            }
        
        if not config.is_enabled:
            logger.info(f"AD sync is disabled for firm {firm.name}, skipping")
            return {
                'success': False,
                'error': 'AD sync is disabled'
            }
        
        # Run sync
        logger.info(f"Starting {sync_type} AD sync for firm {firm.name}")
        
        sync_service = ADSyncService(firm=firm)
        sync_log = sync_service.sync(sync_type=sync_type, triggered_by=None)
        
        logger.info(f"AD sync completed for firm {firm.name}: {sync_log.status}")
        
        return {
            'success': sync_log.status == 'success',
            'firm_id': firm_id,
            'firm_name': firm.name,
            'sync_type': sync_type,
            'users_created': sync_log.users_created,
            'users_updated': sync_log.users_updated,
            'users_disabled': sync_log.users_disabled,
            'users_skipped': sync_log.users_skipped,
            'groups_synced': sync_log.groups_synced,
            'duration_seconds': sync_log.duration_seconds,
            'error': sync_log.error_message if sync_log.status == 'error' else None
        }
        
    except Firm.DoesNotExist:
        logger.error(f"Firm with ID {firm_id} not found")
        return {
            'success': False,
            'error': f'Firm with ID {firm_id} not found'
        }
    except Exception as e:
        logger.error(f"AD sync failed for firm {firm_id}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def sync_ad_users_for_all_firms(sync_type: str = 'delta') -> dict:
    """
    Synchronize users from Active Directory for all firms with AD sync enabled.
    
    AD-4: Scheduled synchronization for all firms.
    
    Args:
        sync_type: Type of sync ('full', 'delta', or 'scheduled')
    
    Returns:
        Dict with aggregate sync results
    """
    logger.info(f"Starting {sync_type} AD sync for all firms")
    
    # Get all firms with AD sync enabled
    configs = ADSyncConfig.objects.filter(is_enabled=True).select_related('firm')
    
    if not configs.exists():
        logger.info("No firms with AD sync enabled found")
        return {
            'success': True,
            'total_firms': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'results': []
        }
    
    results = []
    successful_syncs = 0
    failed_syncs = 0
    
    for config in configs:
        firm = config.firm
        
        # Check sync schedule if this is a scheduled run
        if sync_type == 'scheduled':
            # Skip if not time to sync based on schedule
            if not should_sync_now(config):
                logger.debug(f"Skipping firm {firm.name} - not scheduled to sync now")
                continue
        
        try:
            result = sync_ad_users_for_firm(firm.id, sync_type=sync_type)
            results.append(result)
            
            if result['success']:
                successful_syncs += 1
            else:
                failed_syncs += 1
                
        except Exception as e:
            logger.error(f"Error syncing firm {firm.name}: {e}", exc_info=True)
            results.append({
                'success': False,
                'firm_id': firm.id,
                'firm_name': firm.name,
                'error': str(e)
            })
            failed_syncs += 1
    
    logger.info(
        f"AD sync completed for all firms: "
        f"{successful_syncs} successful, {failed_syncs} failed out of {len(results)} total"
    )
    
    return {
        'success': failed_syncs == 0,
        'total_firms': len(results),
        'successful_syncs': successful_syncs,
        'failed_syncs': failed_syncs,
        'results': results
    }


def should_sync_now(config: ADSyncConfig) -> bool:
    """
    Determine if a firm should be synced now based on its schedule.
    
    AD-4: Schedule checking logic.
    
    Args:
        config: AD sync configuration
    
    Returns:
        True if sync should run now
    """
    if config.sync_schedule == 'manual':
        return False
    
    if not config.last_sync_at:
        # Never synced before, should sync now
        return True
    
    now = timezone.now()
    time_since_last_sync = now - config.last_sync_at
    
    if config.sync_schedule == 'hourly':
        # Sync if more than 55 minutes since last sync (5 min buffer)
        return time_since_last_sync.total_seconds() >= (55 * 60)
    
    elif config.sync_schedule == 'daily':
        # Sync if more than 23 hours since last sync
        return time_since_last_sync.total_seconds() >= (23 * 60 * 60)
    
    elif config.sync_schedule == 'weekly':
        # Sync if more than 6.9 days since last sync
        return time_since_last_sync.total_seconds() >= (6.9 * 24 * 60 * 60)
    
    return False


# Management command helpers
def run_scheduled_sync() -> dict:
    """
    Run scheduled AD sync for all firms.
    
    Called by management command or cron job.
    
    Returns:
        Dict with sync results
    """
    return sync_ad_users_for_all_firms(sync_type='scheduled')


def run_full_sync_for_firm(firm_id: int) -> dict:
    """
    Run full AD sync for a specific firm.
    
    Used for manual full sync via management command.
    
    Args:
        firm_id: ID of the firm to sync
    
    Returns:
        Dict with sync results
    """
    return sync_ad_users_for_firm(firm_id, sync_type='full')


def run_delta_sync_for_firm(firm_id: int) -> dict:
    """
    Run delta AD sync for a specific firm.
    
    Used for manual delta sync via management command.
    
    Args:
        firm_id: ID of the firm to sync
    
    Returns:
        Dict with sync results
    """
    return sync_ad_users_for_firm(firm_id, sync_type='delta')
