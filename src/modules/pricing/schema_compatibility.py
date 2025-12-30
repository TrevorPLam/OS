"""
Pricing Schema Version Compatibility Checker (DOC-09.3)

Implements schema version validation and compatibility checking
per docs/9 section 3 (JSON rule schema versioning).

Per docs/9 section 3.1:
- Schema MUST include `schema_version`
- Backwards-incompatible changes MUST increment major version
- Evaluator MUST reject rulesets with unknown schema versions
  unless an explicit compatibility layer exists

This module provides:
- Schema version parsing and validation
- Compatibility checking between schema versions
- Explicit compatibility layers for version migration
"""

from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class SchemaVersion:
    """Semantic version for pricing schema."""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version_string: str) -> "SchemaVersion":
        """
        Parse semantic version string.

        Args:
            version_string: Version string like "1.2.3"

        Returns:
            SchemaVersion instance

        Raises:
            ValueError: If version string is invalid
        """
        try:
            parts = version_string.split(".")
            if len(parts) != 3:
                raise ValueError(
                    f"Schema version must be in format 'major.minor.patch', got: {version_string}"
                )

            return cls(
                major=int(parts[0]),
                minor=int(parts[1]),
                patch=int(parts[2]),
            )
        except (ValueError, IndexError) as e:
            raise ValueError(
                f"Invalid schema version format: {version_string}. Expected 'X.Y.Z' format."
            ) from e

    def to_string(self) -> str:
        """Convert to string representation."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, other: "SchemaVersion") -> bool:
        """
        Check if this version is compatible with another version.

        Per docs/9:
        - Major version changes are backwards-incompatible
        - Minor/patch changes are backwards-compatible

        Args:
            other: Other schema version to check compatibility with

        Returns:
            True if compatible (same major version), False otherwise
        """
        return self.major == other.major

    def __str__(self) -> str:
        return self.to_string()


class SchemaCompatibilityError(Exception):
    """Raised when schema version is incompatible."""

    pass


class SchemaCompatibilityChecker:
    """
    Schema version compatibility checker.

    Per docs/9 section 3.1:
    - Validates schema versions in rulesets
    - Rejects unknown/incompatible versions
    - Applies compatibility layers when available
    """

    # Supported schema versions (DOC-09.3)
    SUPPORTED_VERSIONS = [
        SchemaVersion(1, 0, 0),  # Initial schema version
        SchemaVersion(1, 1, 0),  # Added discount stacking rules
    ]

    # Maximum supported major version
    MAX_MAJOR_VERSION = 1

    def __init__(self):
        """Initialize compatibility checker."""
        self.supported_versions = self.SUPPORTED_VERSIONS
        self.compatibility_layers = self._initialize_compatibility_layers()

    def _initialize_compatibility_layers(self) -> dict:
        """
        Initialize compatibility layers for version migration.

        Compatibility layers allow older schema versions to be evaluated
        by newer evaluators.

        Returns:
            Dict mapping (from_version, to_version) to migration function
        """
        return {
            # Example: (SchemaVersion(1, 0, 0), SchemaVersion(1, 1, 0)): self._migrate_1_0_to_1_1,
        }

    def validate_ruleset_schema(self, ruleset) -> None:
        """
        Validate that ruleset schema version is supported.

        Per docs/9 section 3.1: Evaluator MUST reject rulesets
        with unknown schema versions unless an explicit compatibility
        layer exists.

        Args:
            ruleset: RuleSet instance to validate

        Raises:
            SchemaCompatibilityError: If schema version is unsupported
        """
        # Get schema version from ruleset
        schema_version_str = ruleset.schema_version

        # Parse schema version
        try:
            schema_version = SchemaVersion.parse(schema_version_str)
        except ValueError as e:
            raise SchemaCompatibilityError(
                f"Invalid schema version in ruleset '{ruleset.code}': {e}"
            )

        # Check if version is supported
        if not self.is_version_supported(schema_version):
            # Check if compatibility layer exists
            if self._has_compatibility_layer_for(schema_version):
                # Compatibility layer exists - allow with warning
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Ruleset '{ruleset.code}' uses schema version {schema_version} "
                    f"which requires compatibility layer. Consider upgrading to "
                    f"latest schema version."
                )
            else:
                # No compatibility layer - reject
                supported_versions_str = ", ".join(
                    [v.to_string() for v in self.supported_versions]
                )
                raise SchemaCompatibilityError(
                    f"Ruleset '{ruleset.code}' uses unsupported schema version {schema_version}. "
                    f"Supported versions: {supported_versions_str}. "
                    f"Major version {schema_version.major} is not supported by this evaluator."
                )

        # Validate rules_json contains required schema_version field
        if "schema_version" not in ruleset.rules_json:
            raise SchemaCompatibilityError(
                f"Ruleset '{ruleset.code}' rules_json missing required 'schema_version' field"
            )

        # Validate rules_json schema_version matches model field
        rules_json_version_str = ruleset.rules_json.get("schema_version")
        if rules_json_version_str != schema_version_str:
            raise SchemaCompatibilityError(
                f"Ruleset '{ruleset.code}' schema version mismatch: "
                f"model has '{schema_version_str}' but rules_json has '{rules_json_version_str}'"
            )

    def is_version_supported(self, version: SchemaVersion) -> bool:
        """
        Check if a schema version is directly supported.

        Args:
            version: Schema version to check

        Returns:
            True if version is in supported list, False otherwise
        """
        return any(
            v.major == version.major
            and v.minor == version.minor
            and v.patch == version.patch
            for v in self.supported_versions
        )

    def _has_compatibility_layer_for(self, version: SchemaVersion) -> bool:
        """
        Check if a compatibility layer exists for this version.

        Args:
            version: Schema version to check

        Returns:
            True if compatibility layer exists, False otherwise
        """
        # Check if we can migrate from this version to any supported version
        for supported_version in self.supported_versions:
            if (version, supported_version) in self.compatibility_layers:
                return True
        return False

    def get_compatible_versions(self, version: SchemaVersion) -> List[SchemaVersion]:
        """
        Get list of schema versions compatible with given version.

        Args:
            version: Schema version to check

        Returns:
            List of compatible schema versions
        """
        compatible = []
        for supported_version in self.supported_versions:
            if version.is_compatible_with(supported_version):
                compatible.append(supported_version)
        return compatible

    def check_backwards_compatibility(
        self,
        old_version: SchemaVersion,
        new_version: SchemaVersion,
    ) -> bool:
        """
        Check if new version is backwards compatible with old version.

        Per docs/9:
        - Same major version = compatible
        - Different major version = incompatible

        Args:
            old_version: Older schema version
            new_version: Newer schema version

        Returns:
            True if new version is backwards compatible with old
        """
        return old_version.is_compatible_with(new_version)


# Global compatibility checker instance
schema_compatibility_checker = SchemaCompatibilityChecker()


def validate_schema_version(ruleset) -> None:
    """
    Convenience function to validate ruleset schema version.

    Usage:
        from modules.pricing.schema_compatibility import validate_schema_version

        try:
            validate_schema_version(ruleset)
        except SchemaCompatibilityError as e:
            # Handle incompatible schema
            pass

    Args:
        ruleset: RuleSet instance to validate

    Raises:
        SchemaCompatibilityError: If schema version is unsupported
    """
    schema_compatibility_checker.validate_ruleset_schema(ruleset)


def verify_ruleset_checksum(ruleset) -> bool:
    """
    Verify ruleset checksum for tamper detection.

    DOC-09.3: Checksum enforcement.

    Usage:
        from modules.pricing.schema_compatibility import verify_ruleset_checksum

        if not verify_ruleset_checksum(ruleset):
            raise IntegrityError("Ruleset checksum verification failed")

    Args:
        ruleset: RuleSet instance to verify

    Returns:
        True if checksum is valid, False otherwise
    """
    return ruleset.verify_checksum()
