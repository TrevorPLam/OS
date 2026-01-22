"""
Input Validation Utilities (DOC-24.1).

Validates all external content to prevent injection attacks per SECURITY_MODEL (docs/03-reference/requirements/DOC-24.md).

Requirements:
- Input validation for email bodies, attachments, filenames
- Protection against XSS, SQLi, command injection
- Safe handling of user-uploaded content
"""

import re
import os
from typing import Optional, List
from pathlib import Path
import mimetypes


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class InputValidator:
    """
    Validates external content for security.

    Per docs/03-reference/requirements/DOC-24.md: "Input validation for all external content (email bodies, attachments, filenames)."
    """

    # Dangerous file extensions that should be blocked
    DANGEROUS_EXTENSIONS = {
        # Executable files
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        # Scripts and code
        '.sh', '.bash', '.zsh', '.ps1', '.psm1', '.py', '.rb', '.pl',
        # Archives that can contain executables
        '.zip', '.rar', '.7z', '.tar', '.gz',  # Allow with scan
        # Office macros
        '.xlsm', '.docm', '.pptm',
        # Other dangerous
        '.jar', '.apk', '.app', '.dmg', '.iso',
    }

    # Safe file extensions (allowlist approach)
    SAFE_EXTENSIONS = {
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods',
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico',
        # Other safe formats
        '.csv', '.json', '.xml', '.yaml', '.md',
    }

    # Allowed MIME types for uploads
    SAFE_MIME_TYPES = {
        # Documents
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain',
        'text/rtf',
        # Images
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/svg+xml',
        'image/webp',
        # Other
        'text/csv',
        'application/json',
        'text/xml',
        'application/xml',
    }

    # Maximum file size (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    @classmethod
    def validate_filename(cls, filename: str, allow_dangerous: bool = False) -> str:
        """
        Validate and sanitize filename.

        Args:
            filename: Original filename
            allow_dangerous: If True, allow dangerous extensions (with virus scan required)

        Returns:
            Sanitized filename

        Raises:
            ValidationError: If filename is invalid or dangerous

        Security:
            - Prevents directory traversal (../)
            - Blocks null bytes
            - Removes special characters
            - Checks extension against blocklist
        """
        if not filename:
            raise ValidationError("Filename cannot be empty")

        # Check for null bytes (directory traversal attack)
        if '\x00' in filename:
            raise ValidationError("Filename contains null bytes (security risk)")

        # Check for directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValidationError("Filename contains path separators (security risk)")

        # Get file extension
        _, ext = os.path.splitext(filename.lower())

        # Check against dangerous extensions
        if ext in cls.DANGEROUS_EXTENSIONS and not allow_dangerous:
            raise ValidationError(
                f"File extension '{ext}' is not allowed for security reasons. "
                f"Allowed extensions: {', '.join(sorted(cls.SAFE_EXTENSIONS))}"
            )

        # Sanitize filename: keep only alphanumeric, underscore, hyphen, dot
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Ensure filename isn't too long (255 chars max)
        if len(safe_filename) > 255:
            # Truncate but keep extension
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:240] + ext

        return safe_filename

    @classmethod
    def validate_file_upload(
        cls,
        filename: str,
        content_type: Optional[str] = None,
        file_size: Optional[int] = None,
        require_virus_scan: bool = True
    ) -> dict:
        """
        Validate file upload.

        Args:
            filename: Uploaded filename
            content_type: MIME type (optional)
            file_size: File size in bytes (optional)
            require_virus_scan: If True, dangerous files require virus scan

        Returns:
            dict with:
                - safe_filename: Sanitized filename
                - requires_scan: Boolean indicating if virus scan required
                - warnings: List of warnings

        Raises:
            ValidationError: If file is invalid

        Security:
            - Validates filename
            - Checks file size limits
            - Validates MIME type
            - Flags files requiring virus scan
        """
        warnings = []

        # Validate filename
        _, ext = os.path.splitext(filename.lower())
        allow_dangerous = require_virus_scan  # Allow dangerous if we'll scan
        safe_filename = cls.validate_filename(filename, allow_dangerous=allow_dangerous)

        # Validate file size
        if file_size is not None:
            if file_size <= 0:
                raise ValidationError("File size must be greater than 0")
            if file_size > cls.MAX_FILE_SIZE:
                raise ValidationError(
                    f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum "
                    f"allowed size ({cls.MAX_FILE_SIZE / 1024 / 1024:.0f}MB)"
                )

        # Validate MIME type
        requires_scan = False
        if content_type:
            if content_type not in cls.SAFE_MIME_TYPES:
                # Check if it's a dangerous type that requires scanning
                if ext in cls.DANGEROUS_EXTENSIONS:
                    requires_scan = True
                    warnings.append(f"File type '{content_type}' requires virus scan")
                else:
                    warnings.append(f"Uncommon MIME type: {content_type}")

        # Flag executable extensions for scanning
        if ext in cls.DANGEROUS_EXTENSIONS:
            requires_scan = True

        # Flag archives for scanning
        if ext in {'.zip', '.rar', '.7z', '.tar', '.gz'}:
            requires_scan = True
            warnings.append("Archive files require virus scan")

        return {
            'safe_filename': safe_filename,
            'requires_scan': requires_scan,
            'warnings': warnings,
        }

    @classmethod
    def validate_email_content(cls, content: str, max_length: int = 1_000_000) -> str:
        """
        Validate and sanitize email content.

        Args:
            content: Email body content
            max_length: Maximum content length

        Returns:
            Sanitized content

        Raises:
            ValidationError: If content is invalid

        Security:
            - Prevents excessively large content (DoS)
            - Removes null bytes
            - Flags suspicious patterns (future: scan for malicious links)
        """
        if not content:
            return ""

        # Check length (prevent DoS)
        if len(content) > max_length:
            raise ValidationError(
                f"Content too large ({len(content)} chars, max {max_length})"
            )

        # Remove null bytes
        if '\x00' in content:
            content = content.replace('\x00', '')

        # FUTURE: Add link scanning, malicious pattern detection
        # For now, just sanitize basic issues

        return content

    @classmethod
    def validate_url(cls, url: str, allowed_schemes: Optional[List[str]] = None, block_internal: bool = True) -> str:
        """
        Validate URL and prevent SSRF attacks (ASSESS-I5.6).

        Args:
            url: URL to validate
            allowed_schemes: Allowed URL schemes (default: ['http', 'https'])
            block_internal: If True, block internal IPs and localhost (SSRF protection)

        Returns:
            Validated URL

        Raises:
            ValidationError: If URL is invalid or blocked

        Security:
            - Prevents javascript: URLs (XSS)
            - Prevents data: URLs (XSS)
            - Prevents file: URLs (local file access)
            - Blocks internal IPs and localhost (SSRF protection) via validate_safe_url
            - Only allows http/https by default
        """
        from modules.core.validators import validate_safe_url
        from django.core.exceptions import ValidationError as DjangoValidationError

        if not url:
            raise ValidationError("URL cannot be empty")

        url = url.strip()

        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']

        # Extract scheme
        if '://' not in url:
            raise ValidationError("URL must include scheme (http:// or https://)")

        scheme = url.split('://')[0].lower()

        # Check scheme allowlist
        if scheme not in allowed_schemes:
            raise ValidationError(
                f"URL scheme '{scheme}' not allowed. "
                f"Allowed schemes: {', '.join(allowed_schemes)}"
            )

        # Block common XSS schemes
        dangerous_schemes = ['javascript', 'data', 'vbscript', 'file']
        if scheme in dangerous_schemes:
            raise ValidationError(
                f"URL scheme '{scheme}' is blocked for security reasons"
            )

        # SECURITY: Block internal IPs and localhost to prevent SSRF (ASSESS-I5.6)
        # Use existing validate_safe_url which has comprehensive SSRF protection
        if block_internal:
            try:
                validate_safe_url(url)
            except DjangoValidationError as e:
                raise ValidationError(str(e)) from e

        return url

    @classmethod
    def sanitize_html(cls, html: str, allowed_tags: Optional[List[str]] = None) -> str:
        """
        Sanitize HTML content (stub - requires library like bleach).

        Args:
            html: HTML content to sanitize
            allowed_tags: Allowed HTML tags

        Returns:
            Sanitized HTML

        Security:
            - STUB: Full implementation requires bleach or similar
            - For now, escape all HTML to prevent XSS
        """
        if allowed_tags is None:
            allowed_tags = []

        # STUB: For now, just escape HTML
        # FUTURE: Use bleach library for proper HTML sanitization
        import html as html_module
        return html_module.escape(html)

    @classmethod
    def validate_json_field(cls, data: dict, max_depth: int = 10, max_size: int = 100_000) -> dict:
        """
        Validate JSON data.

        Args:
            data: JSON data to validate
            max_depth: Maximum nesting depth
            max_size: Maximum serialized size

        Returns:
            Validated data

        Raises:
            ValidationError: If JSON is invalid

        Security:
            - Prevents deeply nested JSON (DoS)
            - Prevents excessively large JSON (DoS)
        """
        import json

        # Check depth
        def get_depth(d, level=0):
            if not isinstance(d, dict) and not isinstance(d, list):
                return level
            if isinstance(d, dict):
                return max((get_depth(v, level + 1) for v in d.values()), default=level)
            if isinstance(d, list):
                return max((get_depth(item, level + 1) for item in d), default=level)

        depth = get_depth(data)
        if depth > max_depth:
            raise ValidationError(
                f"JSON nesting too deep ({depth} levels, max {max_depth})"
            )

        # Check size
        serialized = json.dumps(data)
        if len(serialized) > max_size:
            raise ValidationError(
                f"JSON too large ({len(serialized)} bytes, max {max_size})"
            )

        return data


# Convenience functions

def validate_filename(filename: str) -> str:
    """Validate filename."""
    return InputValidator.validate_filename(filename)


def validate_file_upload(filename: str, content_type: Optional[str] = None, file_size: Optional[int] = None) -> dict:
    """Validate file upload."""
    return InputValidator.validate_file_upload(filename, content_type, file_size)


def validate_email_content(content: str) -> str:
    """Validate email content."""
    return InputValidator.validate_email_content(content)


def validate_url(url: str) -> str:
    """Validate URL."""
    return InputValidator.validate_url(url)


def sanitize_html(html: str) -> str:
    """Sanitize HTML content."""
    return InputValidator.sanitize_html(html)
