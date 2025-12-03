"""WSGI config for eye_contact_service."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eye_contact_service.settings')

application = get_wsgi_application()
