"""
ASGI config for arm_movement_service project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arm_movement_service.settings')

application = get_asgi_application()
