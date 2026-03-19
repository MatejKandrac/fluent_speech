import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'audio_analysis_ms.settings')

application = get_wsgi_application()
