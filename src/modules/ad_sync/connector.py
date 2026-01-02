"""
Active Directory LDAP Connector

Handles LDAP/LDAPS connections to Active Directory and user/group queries.
Part of AD-1: Implement AD Organizational Unit sync.
"""

import logging
import ssl
from datetime import datetime, timezone as dt_timezone
from typing import Any, Optional

from django.conf import settings
from ldap3 import ALL, SUBTREE, Connection, Server
from ldap3.core.exceptions import LDAPException

logger = logging.getLogger(__name__)


class ActiveDirectoryConnector:
    """
    LDAP connector for Active Directory integration.
    
    Provides methods to connect, search users, search groups, and perform delta syncs.
    Uses LDAPS (port 636) for secure communication.
    """
    
    def __init__(
        self,
        server_url: str,
        service_account_dn: str,
        password: str,
        base_dn: str,
        verify_ssl: bool = True
    ):
        """
        Initialize AD connector.
        
        Args:
            server_url: LDAPS URL (e.g., ldaps://ad.company.com:636)
            service_account_dn: Service account DN (e.g., CN=ServiceAccount,OU=Service Accounts,DC=company,DC=com)
            password: Service account password
            base_dn: Base DN for searches (e.g., DC=company,DC=com)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.server_url = server_url
        self.service_account_dn = service_account_dn
        self.password = password
        self.base_dn = base_dn
        self.verify_ssl = verify_ssl
        self.conn: Optional[Connection] = None
        self.server: Optional[Server] = None
        
        logger.info(f"Initializing AD connector for {server_url}")
    
    def connect(self) -> bool:
        """
        Establish connection to Active Directory.
        
        Returns:
            True if connection successful, False otherwise
        
        Raises:
            LDAPException: If connection fails
        """
        try:
            # Create TLS context
            tls = ssl.create_default_context()
            if not self.verify_ssl:
                tls.check_hostname = False
                tls.verify_mode = ssl.CERT_NONE
                logger.warning("SSL verification disabled - use only for testing!")
            else:
                tls.verify_mode = ssl.CERT_REQUIRED
            
            # Create server object
            self.server = Server(
                self.server_url,
                use_ssl=True,
                tls=tls,
                get_info=ALL
            )
            
            # Create connection
            self.conn = Connection(
                self.server,
                user=self.service_account_dn,
                password=self.password,
                auto_bind=True,
                raise_exceptions=True
            )
            
            logger.info(f"Successfully connected to AD: {self.server_url}")
            return True
            
        except LDAPException as e:
            logger.error(f"Failed to connect to AD: {e}")
            raise
    
    def search_users(
        self,
        ou_filter: Optional[str] = None,
        attributes: Optional[list[str]] = None,
        active_only: bool = True
    ) -> list[Any]:
        """
        Search for users in Active Directory.
        
        AD-1: Core user search functionality.
        
        Args:
            ou_filter: Optional OU to search within (e.g., OU=Employees,DC=company,DC=com)
            attributes: List of AD attributes to retrieve
            active_only: Only return active (non-disabled) users
        
        Returns:
            List of LDAP user entries
        """
        if not self.conn:
            raise RuntimeError("Not connected to AD. Call connect() first.")
        
        if attributes is None:
            # Default attributes to retrieve
            attributes = [
                'sAMAccountName',      # Username
                'mail',                # Email
                'userPrincipalName',   # UPN
                'objectGUID',          # Unique ID
                'givenName',           # First name
                'sn',                  # Last name (surname)
                'displayName',         # Display name
                'memberOf',            # Group memberships
                'whenChanged',         # Last modified timestamp
                'whenCreated',         # Created timestamp
                'userAccountControl',  # Account status (enabled/disabled)
                'distinguishedName',   # DN
            ]
        
        search_base = ou_filter if ou_filter else self.base_dn
        
        # Search filter: Users only (not computers or other objects)
        if active_only:
            # Filter for active users only (not disabled, not deleted)
            # userAccountControl:1.2.840.113556.1.4.803:=2 checks if ACCOUNTDISABLE flag is set
            search_filter = '(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))'
        else:
            # All users (including disabled)
            search_filter = '(&(objectClass=user)(objectCategory=person))'
        
        try:
            self.conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=attributes,
                paged_size=1000  # Pagination for large results
            )
            
            entries = self.conn.entries
            logger.info(f"Found {len(entries)} users in AD")
            return entries
            
        except LDAPException as e:
            logger.error(f"Failed to search users: {e}")
            raise
    
    def search_groups(
        self,
        ou_filter: Optional[str] = None,
        attributes: Optional[list[str]] = None
    ) -> list[Any]:
        """
        Search for security groups in Active Directory.
        
        AD-5: Group sync functionality.
        
        Args:
            ou_filter: Optional OU to search within
            attributes: List of AD attributes to retrieve
        
        Returns:
            List of LDAP group entries
        """
        if not self.conn:
            raise RuntimeError("Not connected to AD. Call connect() first.")
        
        if attributes is None:
            attributes = [
                'cn',                  # Common name
                'distinguishedName',   # DN
                'objectGUID',          # Unique ID
                'member',              # Group members
                'whenChanged',         # Last modified
                'description',         # Group description
            ]
        
        search_base = ou_filter if ou_filter else self.base_dn
        
        # Search filter: Security groups only
        search_filter = '(objectClass=group)'
        
        try:
            self.conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=attributes,
                paged_size=1000
            )
            
            entries = self.conn.entries
            logger.info(f"Found {len(entries)} groups in AD")
            return entries
            
        except LDAPException as e:
            logger.error(f"Failed to search groups: {e}")
            raise
    
    def get_delta_users(
        self,
        since_timestamp: datetime,
        ou_filter: Optional[str] = None
    ) -> list[Any]:
        """
        Get users modified since a specific timestamp (delta/incremental sync).
        
        AD-4: Delta sync functionality.
        
        Args:
            since_timestamp: Get users modified since this timestamp
            ou_filter: Optional OU to search within
        
        Returns:
            List of modified LDAP user entries
        """
        if not self.conn:
            raise RuntimeError("Not connected to AD. Call connect() first.")
        
        search_base = ou_filter if ou_filter else self.base_dn
        
        # Convert Python datetime to AD timestamp format (GeneralizedTime)
        # Format: YYYYMMDDHHMMSSmmZ (UTC)
        if since_timestamp.tzinfo is None:
            since_timestamp = since_timestamp.replace(tzinfo=dt_timezone.utc)
        ad_timestamp = since_timestamp.strftime('%Y%m%d%H%M%S.0Z')
        
        # Search for users modified since timestamp
        search_filter = f'(&(objectClass=user)(objectCategory=person)(whenChanged>={ad_timestamp}))'
        
        try:
            self.conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes='*',  # Get all attributes for modified users
                paged_size=1000
            )
            
            entries = self.conn.entries
            logger.info(f"Found {len(entries)} users modified since {since_timestamp}")
            return entries
            
        except LDAPException as e:
            logger.error(f"Failed to get delta users: {e}")
            raise
    
    def is_user_enabled(self, user_entry: Any) -> bool:
        """
        Check if AD user account is enabled.
        
        AD-3: Used for auto-disable functionality.
        
        Args:
            user_entry: LDAP user entry
        
        Returns:
            True if user is enabled, False if disabled
        """
        try:
            # userAccountControl is a bitfield
            # Bit 2 (0x0002) = ACCOUNTDISABLE flag
            uac = int(user_entry.userAccountControl.value)
            is_enabled = not (uac & 0x0002)  # Check if ACCOUNTDISABLE bit is NOT set
            return is_enabled
        except (AttributeError, ValueError, TypeError) as e:
            logger.warning(f"Could not determine user enabled status: {e}")
            return False  # Default to disabled if we can't determine
    
    def get_user_groups(self, user_entry: Any) -> list[str]:
        """
        Get list of AD groups a user belongs to.
        
        AD-5: Group membership extraction.
        
        Args:
            user_entry: LDAP user entry
        
        Returns:
            List of group DNs
        """
        try:
            if hasattr(user_entry, 'memberOf') and user_entry.memberOf:
                return [str(group) for group in user_entry.memberOf.values]
            return []
        except (AttributeError, TypeError) as e:
            logger.warning(f"Could not get user groups: {e}")
            return []
    
    def get_group_members(self, group_dn: str) -> list[str]:
        """
        Get list of members in an AD group.
        
        AD-5: Group member retrieval.
        
        Args:
            group_dn: Distinguished Name of the group
        
        Returns:
            List of member DNs
        """
        if not self.conn:
            raise RuntimeError("Not connected to AD. Call connect() first.")
        
        try:
            self.conn.search(
                search_base=group_dn,
                search_filter='(objectClass=group)',
                search_scope='BASE',
                attributes=['member']
            )
            
            if self.conn.entries:
                group_entry = self.conn.entries[0]
                if hasattr(group_entry, 'member') and group_entry.member:
                    return [str(member) for member in group_entry.member.values]
            return []
            
        except LDAPException as e:
            logger.error(f"Failed to get group members for {group_dn}: {e}")
            return []
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test AD connection and return status.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not self.conn:
                self.connect()
            
            # Try a simple search to verify connection works
            self.conn.search(
                search_base=self.base_dn,
                search_filter='(objectClass=*)',
                search_scope='BASE',
                attributes=['*']
            )
            
            return (True, f"Successfully connected to {self.server_url}")
            
        except LDAPException as e:
            error_msg = f"Connection test failed: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
    
    def close(self):
        """Close AD connection."""
        if self.conn:
            try:
                self.conn.unbind()
                logger.info("AD connection closed")
            except Exception as e:
                logger.error(f"Error closing AD connection: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
