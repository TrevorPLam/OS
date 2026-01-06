"""
Environment Variable Validation on Startup.

Ensures all required configuration is present before the application starts.
Fails fast with clear error messages if critical variables are missing.
"""

import os
import sys


class EnvironmentValidationError(Exception):
    """Raised when required environment variables are missing or invalid."""

    pass


class EnvironmentValidator:
    """Validates environment variables on application startup."""

    # Required variables (always needed)
    REQUIRED_VARS = [
        "DJANGO_SECRET_KEY",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
    ]

    # Required in production only (when DEBUG=False)
    PRODUCTION_REQUIRED_VARS = [
        "DJANGO_ALLOWED_HOSTS",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_STORAGE_BUCKET_NAME",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
    ]

    # Insecure default values that should never be used in production
    INSECURE_DEFAULTS = {
        "DJANGO_SECRET_KEY": [
            "django-insecure-CHANGE-THIS-IN-PRODUCTION-xk7m9n8b5v4c3x2z1",
            "your-secret-key-here-change-in-production",
            "change-me",
            "secret",
        ],
        "POSTGRES_PASSWORD": [
            "postgres",
            "password",
            "admin",
            "your-postgres-password-here",
        ],
    }

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.is_production = os.environ.get("DJANGO_DEBUG", "True").lower() not in ["true", "1", "yes"]

    def validate_all(self) -> None:
        """Run all validation checks."""
        self.check_required_vars()
        if self.is_production:
            self.check_production_vars()
            self.check_insecure_defaults()
            self.check_allowed_hosts()
            self.check_secret_key_strength()
            self.check_webhook_secrets()

        self.report_results()

    def check_required_vars(self) -> None:
        """Check that all required variables are present."""
        for var in self.REQUIRED_VARS:
            value = os.environ.get(var)
            if not value:
                self.errors.append(f"❌ Required variable missing: {var}")

    def check_production_vars(self) -> None:
        """Check production-specific required variables."""
        for var in self.PRODUCTION_REQUIRED_VARS:
            value = os.environ.get(var)
            if not value:
                self.errors.append(f"❌ Production variable missing: {var} " f"(required when DJANGO_DEBUG=False)")

    def check_insecure_defaults(self) -> None:
        """Check for insecure default values."""
        for var, insecure_values in self.INSECURE_DEFAULTS.items():
            value = os.environ.get(var, "")
            if value in insecure_values:
                self.errors.append(
                    f"❌ SECURITY RISK: {var} is set to an insecure default value. "
                    f"You must change this in production!"
                )

    def check_allowed_hosts(self) -> None:
        """Validate ALLOWED_HOSTS configuration."""
        allowed_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")

        if not allowed_hosts:
            self.errors.append(
                "❌ DJANGO_ALLOWED_HOSTS is empty in production. "
                "Set it to your domain (e.g., 'example.com,www.example.com')"
            )
            return

        # Check for insecure localhost-only configuration
        if allowed_hosts in ["localhost", "127.0.0.1", "localhost,127.0.0.1"]:
            self.warnings.append(
                "⚠️  DJANGO_ALLOWED_HOSTS only includes localhost. "
                "This will reject all external requests in production."
            )

        # Check for wildcard (insecure)
        if "*" in allowed_hosts:
            self.errors.append(
                "❌ SECURITY RISK: DJANGO_ALLOWED_HOSTS contains '*' (wildcard). "
                "This defeats Host header validation. Specify exact domains."
            )

    def check_secret_key_strength(self) -> None:
        """Validate SECRET_KEY has sufficient entropy."""
        secret_key = os.environ.get("DJANGO_SECRET_KEY", "")

        if len(secret_key) < 50:
            self.warnings.append(
                f"⚠️  DJANGO_SECRET_KEY is too short ({len(secret_key)} chars). "
                "Recommended: at least 50 characters of random data."
            )

        # Check for common patterns
        if secret_key.lower() in ["secret", "password", "key"]:
            self.errors.append(
                "❌ SECURITY RISK: DJANGO_SECRET_KEY is a common word. " "Use a cryptographically random string."
            )

    def check_webhook_secrets(self) -> None:
        """Validate webhook secrets are configured if webhooks are enabled (SEC-6)."""
        # Check DocuSign webhook secret
        docusign_client_id = os.environ.get("DOCUSIGN_CLIENT_ID")
        docusign_webhook_secret = os.environ.get("DOCUSIGN_WEBHOOK_SECRET")
        
        if docusign_client_id and not docusign_webhook_secret:
            self.errors.append(
                "❌ SECURITY RISK (SEC-6): DOCUSIGN_CLIENT_ID is set but DOCUSIGN_WEBHOOK_SECRET is missing. "
                "Webhook signature verification will reject all DocuSign webhooks. "
                "Set DOCUSIGN_WEBHOOK_SECRET or disable DocuSign integration."
            )
        
        # Check Twilio auth token
        twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        
        if twilio_account_sid and not twilio_auth_token:
            self.errors.append(
                "❌ SECURITY RISK (SEC-6): TWILIO_ACCOUNT_SID is set but TWILIO_AUTH_TOKEN is missing. "
                "Webhook signature verification will reject all Twilio webhooks. "
                "Set TWILIO_AUTH_TOKEN or disable Twilio integration."
            )

    def report_results(self) -> None:
        """Print validation results and exit if there are errors."""
        if not self.errors and not self.warnings:
            print("✅ Environment validation passed")
            return

        print("\n" + "=" * 70)
        print("🔍 ENVIRONMENT VALIDATION RESULTS")
        print("=" * 70)

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  {error}")

            print("\n" + "=" * 70)
            print("💥 Application startup BLOCKED due to configuration errors.")
            print("=" * 70)
            print("\nFix the errors above and try again.")
            print("See .env.example for configuration template.\n")
            sys.exit(1)

        if self.warnings and not self.errors:
            print("\n" + "=" * 70)
            print("⚠️  Application starting with warnings. Review them before deploying.")
            print("=" * 70 + "\n")


def validate_environment() -> None:
    """
    Main entry point for environment validation.
    Call this from settings.py or wsgi.py on startup.
    """
    # Skip validation in CI environments
    if os.environ.get("CI") == "true":
        print("ℹ️  Skipping environment validation (CI environment detected)")
        return

    validator = EnvironmentValidator()
    validator.validate_all()


# Auto-run validation when this module is imported
# (Will run when imported in settings.py)
if __name__ != "__main__":
    # Only validate if not in test mode
    if "test" not in sys.argv and "pytest" not in sys.modules:
        validate_environment()
