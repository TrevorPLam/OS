"""
Documents Models: Folder, Document, Version.

Implements S3-backed secure document storage with versioning.
Supports hierarchical folders and client portal access.

TIER 0: All documents belong to exactly one Firm for tenant isolation.
"""

from .folders import Folder, FolderComment
from .documents import Document, DocumentComment, DocumentViewLog
from .locks import DocumentLock
from .versions import Version
from .access_logs import DocumentAccessLog
from .shares import ExternalShare, SharePermission, ShareAccess
from .file_requests import FileRequest, FileRequestReminder

__all__ = [
    'Folder',
    'FolderComment',
    'Document',
    'DocumentComment',
    'DocumentViewLog',
    'DocumentLock',
    'Version',
    'DocumentAccessLog',
    'ExternalShare',
    'SharePermission',
    'ShareAccess',
    'FileRequest',
    'FileRequestReminder',
]
