import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_ORCHESTRATOR', 'django-insecure-orchestrator-dev-key')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_ORCHESTRATOR', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'orchestrator_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'orchestrator_service.urls'

WSGI_APPLICATION = 'orchestrator_service.wsgi.application'

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

POSTGRES_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'fluent'),
    'user': os.getenv('DB_USERNAME', ''),
    'password': os.getenv('DB_PASSWORD', ''),
}

VIDEO_STORAGE_PATH = os.getenv('VIDEO_STORAGE_PATH', '/tmp/video_data')

PROCESSING_SERVICES = {
    'video_processing': os.getenv('VIDEO_PROCESSING_SERVICE_URL', 'http://localhost:8001'),
    'audio_processing': os.getenv('AUDIO_PROCESSING_SERVICE_URL', 'http://localhost:8004'),
    'transcript': os.getenv('TRANSCRIPT_PROCESSING_SERVICE_URL', 'http://localhost:8009'),
}
