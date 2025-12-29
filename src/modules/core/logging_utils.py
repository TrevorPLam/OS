"""
Governance-Aware Logging Utilities (DOC-07.1)

Provides logging utilities that integrate with the governance classification registry
to ensure sensitive data is properly redacted in logs.

Per docs/7 section 3.1:
- HR data MUST NOT appear in logs
- R-PII values should be avoided unless strictly required for troubleshooting

Usage:
    from modules.core.logging_utils import SafeLogger

    # Create a governance-aware logger
    logger = SafeLogger('mymodule')

    # Log with automatic redaction
    logger.info_entity('Contact', contact_data, "Updated contact")

    # Or use the filter directly
    import logging
    logging.config.dictConfig({
        'filters': {
            'governance': {
                '()': 'modules.core.logging_utils.GovernanceRedactionFilter',
            }
        }
    })
"""

import logging
from typing import Any, Optional

from modules.core.governance import (
    DataClassification,
    governance_registry,
    redact_for_logging,
)


class GovernanceRedactionFilter(logging.Filter):
    """
    Logging filter that redacts sensitive data from log records.

    This filter looks for specific attributes on log records:
    - governance_entity: The entity type for classification lookup
    - governance_data: The data dictionary to redact

    If these are present, the data is redacted before the record is emitted.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply governance redaction to log records."""
        # Check if this record has governance metadata
        entity = getattr(record, "governance_entity", None)
        data = getattr(record, "governance_data", None)

        if entity and data:
            # Redact the data
            record.governance_data = redact_for_logging(entity, data)

        # Also check the message args for dict-like data
        if record.args and isinstance(record.args, dict):
            entity = record.args.get("_governance_entity")
            if entity:
                # Create a redacted copy of the args
                redacted_args = {}
                for key, value in record.args.items():
                    if key.startswith("_"):
                        continue  # Skip metadata keys
                    if isinstance(value, dict):
                        redacted_args[key] = redact_for_logging(entity, value)
                    else:
                        classification = governance_registry.get_field_classification(
                            entity, key
                        )
                        if classification and classification.requires_redaction_in_logs():
                            if classification == DataClassification.HIGHLY_RESTRICTED:
                                redacted_args[key] = "[REDACTED]"
                            else:
                                redacted_args[key] = governance_registry._mask_pii(value)
                        else:
                            redacted_args[key] = value
                record.args = redacted_args

        return True


class SafeLogger:
    """
    A wrapper around Python's logging module that provides governance-aware logging.

    This logger automatically redacts sensitive data based on the governance
    classification registry.

    Usage:
        logger = SafeLogger('mymodule')

        # Log a message with entity context
        logger.info_entity('Contact', contact_data, "Contact created")

        # Standard logging (no automatic redaction)
        logger.info("Standard message")
    """

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def _log_with_entity(
        self,
        level: int,
        entity: str,
        data: dict,
        message: str,
        *args,
        **kwargs,
    ):
        """Log a message with entity context and automatic redaction."""
        redacted = redact_for_logging(entity, data)
        self._logger.log(
            level,
            f"{message}: %s",
            redacted,
            *args,
            extra={
                "governance_entity": entity,
                "governance_data": redacted,
            },
            **kwargs,
        )

    def info_entity(self, entity: str, data: dict, message: str, *args, **kwargs):
        """Log at INFO level with governance redaction."""
        self._log_with_entity(logging.INFO, entity, data, message, *args, **kwargs)

    def debug_entity(self, entity: str, data: dict, message: str, *args, **kwargs):
        """Log at DEBUG level with governance redaction."""
        self._log_with_entity(logging.DEBUG, entity, data, message, *args, **kwargs)

    def warning_entity(self, entity: str, data: dict, message: str, *args, **kwargs):
        """Log at WARNING level with governance redaction."""
        self._log_with_entity(logging.WARNING, entity, data, message, *args, **kwargs)

    def error_entity(self, entity: str, data: dict, message: str, *args, **kwargs):
        """Log at ERROR level with governance redaction."""
        self._log_with_entity(logging.ERROR, entity, data, message, *args, **kwargs)

    # Passthrough to standard logger methods
    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._logger.exception(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)


def get_safe_logger(name: str) -> SafeLogger:
    """
    Get a governance-aware logger instance.

    Usage:
        from modules.core.logging_utils import get_safe_logger
        logger = get_safe_logger(__name__)
    """
    return SafeLogger(name)


# Configure default logging filter
def configure_governance_logging():
    """
    Configure the root logger with governance redaction filter.

    Call this during application startup to ensure all loggers
    have governance-aware filtering.
    """
    root_logger = logging.getLogger()
    governance_filter = GovernanceRedactionFilter()

    for handler in root_logger.handlers:
        handler.addFilter(governance_filter)
