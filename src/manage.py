#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def main():
    """Run administrative tasks."""
    # Load environment variables from .env file (TIER 0: Configuration)
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    # Commands that can run without a fully configured environment.
    COMMANDS_TO_SKIP_VALIDATION = {
        "makemigrations",
        "startapp",
        "startproject",
        "shell",
        "dbshell",
        "help",
    }

    command = sys.argv[1] if len(sys.argv) > 1 else ""

    if command not in COMMANDS_TO_SKIP_VALIDATION:
        from config.env_validator import validate_environment

        validate_environment()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
