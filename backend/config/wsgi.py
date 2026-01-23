"""
WSGI config for ConsultantPro.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from config.env_validator import validate_environment

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

validate_environment()
application = get_wsgi_application()
