"""
ASGI config for audio_analysis_ms project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'audio_analysis_ms.settings')

application = get_asgi_application()
